import secrets
from urllib.parse import quote

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zernio import Zernio

from messaging.models import BusinessAccount, ConnectAttempt, ZernioProfile


class ZernioServiceError(Exception):
    """Raised when Zernio is not configured or returns an unusable response."""


def _as_dict(value):
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True)
    if hasattr(value, "dict"):
        return value.dict()
    return {}


def _first(mapping, *keys, default=""):
    for key in keys:
        value = mapping.get(key)
        if value is not None and value != "":
            return value
    return default


class ZernioService:
    def __init__(self):
        api_key = getattr(settings, "ZERNIO_API_KEY", None)
        if not api_key:
            raise ZernioServiceError("ZERNIO_API_KEY is not configured.")
        self.api_key = api_key
        self.client = Zernio(api_key=api_key)

    def disconnect_account(self, account_id):
        try:
            response = requests.delete(
                f"https://zernio.com/api/v1/accounts/{quote(str(account_id), safe='')}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ZernioServiceError("Zernio could not disconnect this account.") from exc

    def register_webhook(self):
        webhook_url = getattr(settings, "ZERNIO_WEBHOOK_URL", None)
        webhook_secret = getattr(settings, "ZERNIO_WEBHOOK_SECRET", None)
        if not webhook_url or not webhook_secret:
            raise ZernioServiceError(
                "Set ZERNIO_WEBHOOK_URL and ZERNIO_WEBHOOK_SECRET before registering the webhook."
            )

        name = "Nepdora CRM inbox messages"
        events = ["message.received"]
        try:
            response = _as_dict(self.client.webhooks.get_webhook_settings())
            webhooks = response.get("webhooks", [])
            if not isinstance(webhooks, list):
                webhooks = []
            existing = next(
                (item for item in webhooks if item.get("url") == webhook_url), None
            )
            if existing:
                webhook_id = _first(existing, "_id", "id", "webhookId")
                if not webhook_id:
                    raise ZernioServiceError(
                        "The existing Zernio webhook is missing its ID."
                    )
                return self.client.webhooks.update_webhook_settings(
                    webhook_id=str(webhook_id),
                    name=name,
                    url=webhook_url,
                    secret=webhook_secret,
                    events=events,
                    is_active=True,
                )
            return self.client.webhooks.create_webhook_settings(
                name=name,
                url=webhook_url,
                secret=webhook_secret,
                events=events,
            )
        except ZernioServiceError:
            raise
        except Exception as exc:
            raise ZernioServiceError("Could not register the Zernio webhook.") from exc

    def get_or_create_profile(self, user):
        existing = ZernioProfile.objects.filter(user=user).first()
        if existing:
            return existing

        # external_id makes profile creation repeatable if a request is retried.
        try:
            response = _as_dict(
                self.client.profiles.create_profile(
                    name=f"CRM user {user.pk}", external_id=str(user.pk)
                )
            )
        except Exception as exc:
            # Recover from a concurrent request that created the profile first.
            existing = ZernioProfile.objects.filter(user=user).first()
            if existing:
                return existing
            raise ZernioServiceError("Could not create a Zernio profile.") from exc

        profile_id = _first(response, "_id", "id", "profile_id", "profileId")
        if not profile_id and isinstance(response.get("profile"), dict):
            profile_id = _first(response["profile"], "_id", "id", "profile_id", "profileId")
        if not profile_id:
            raise ZernioServiceError("Zernio did not return a profile ID.")

        profile, _ = ZernioProfile.objects.get_or_create(
            user=user, defaults={"profile_id": str(profile_id)}
        )
        return profile

    def create_connect_url(self, user, platform, callback_url, return_url):
        profile = self.get_or_create_profile(user)
        state = secrets.token_urlsafe(32)
        callback_parts = urlsplit(callback_url)
        callback_query = parse_qsl(callback_parts.query, keep_blank_values=True)
        callback_query.append(("state", state))
        redirect_url = urlunsplit(
            (
                callback_parts.scheme,
                callback_parts.netloc,
                callback_parts.path,
                urlencode(callback_query),
                callback_parts.fragment,
            )
        )

        try:
            response = _as_dict(
                self.client.connect.get_connect_url(
                    platform=platform.lower(),
                    profile_id=profile.profile_id,
                    redirect_url=redirect_url,
                )
            )
        except Exception as exc:
            raise ZernioServiceError("Could not create a Zernio connect URL.") from exc

        connect_url = _first(
            response, "authUrl", "auth_url", "url", "connect_url", "connectUrl"
        )
        if not connect_url and isinstance(response.get("connect"), dict):
            connect_url = _first(
                response["connect"], "authUrl", "auth_url", "url", "connectUrl"
            )
        if not connect_url:
            raise ZernioServiceError("Zernio returned an incomplete connect response.")

        ConnectAttempt.objects.create(
            user=user,
            platform=platform.lower(),
            profile_id=profile.profile_id,
            state=str(state),
            return_url=return_url,
        )
        return {"url": connect_url}

    @transaction.atomic
    def complete_connect(self, platform, state, account_id, profile_id, username=""):
        try:
            attempt = ConnectAttempt.objects.select_for_update().get(
                state=state, platform=platform.lower()
            )
        except ConnectAttempt.DoesNotExist as exc:
            raise ZernioServiceError("The connect state is invalid or expired.") from exc
        if attempt.created_at < timezone.now() - timedelta(minutes=15):
            attempt.delete()
            raise ZernioServiceError("The connect state is invalid or expired.")

        if profile_id and profile_id != attempt.profile_id:
            raise ZernioServiceError("The returned Zernio profile does not match this connect request.")
        if not account_id:
            raise ZernioServiceError("Zernio did not return a connected account ID.")

        account_data = {
            "accountId": account_id,
            "platform": platform.lower(),
            "username": username,
        }
        try:
            accounts_response = _as_dict(
                self.client.accounts.list_accounts(profile_id=attempt.profile_id)
            )
            accounts = accounts_response.get("accounts", [])
            if isinstance(accounts, list):
                account_data = next(
                    (
                        _as_dict(item)
                        for item in accounts
                        if str(_first(_as_dict(item), "accountId", "account_id", "_id", "id"))
                        == str(account_id)
                    ),
                    account_data,
                )
        except Exception:
            # The callback itself supplies a verified account ID. The account
            # list is only used to enrich the local record with display metadata.
            pass

        account, _ = BusinessAccount.objects.update_or_create(
            user=attempt.user,
            zernio_account_id=str(account_id),
            defaults={
                "profile_id": attempt.profile_id,
                "platform": platform.lower(),
                "platform_account_id": str(
                    _first(account_data, "platformAccountId", "platform_account_id", "userId", "user_id")
                ),
                "account_name": str(
                    _first(account_data, "name", "account_name", "displayName", "display_name")
                ),
                "username": str(_first(account_data, "username", "handle")),
                "avatar_url": str(
                    _first(account_data, "avatar", "avatarUrl", "avatar_url", "profilePicture")
                ),
                # Keep only display/status metadata; never persist OAuth credentials.
                "account_data": {
                    key: value
                    for key, value in account_data.items()
                    if key
                    in {
                        "platform",
                        "name",
                        "account_name",
                        "displayName",
                        "display_name",
                        "username",
                        "handle",
                        "platformAccountId",
                        "platform_account_id",
                        "userId",
                        "user_id",
                        "avatar",
                        "avatarUrl",
                        "avatar_url",
                        "profilePicture",
                        "status",
                        "category",
                    }
                },
            },
        )
        return_url = attempt.return_url
        attempt.delete()
        return account, return_url
