from datetime import datetime

from django.db import transaction

from messaging.models import (
    BusinessAccount,
    Message,
    MessageConversation,
    MessageStatus,
    MessageType,
    MessagingPlatform,
    ZernioWebhookEvent,
)
from messaging.realtime import broadcast_message


class WebhookPayloadError(Exception):
    """Raised when a Zernio inbox webhook is missing required fields."""


class WebhookAccountNotFound(WebhookPayloadError):
    """Raised when an inbox event cannot yet be matched to a CRM account."""


def _first(data, *keys, default=""):
    if not isinstance(data, dict):
        return default
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return default


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


@transaction.atomic
def receive_zernio_event(payload, event_id):
    event_type = str(payload.get("event", ""))
    _, created = ZernioWebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type},
    )
    if not created:
        return False

    if event_type != "message.received":
        return True

    message_data = payload.get("message") or {}
    conversation_data = payload.get("conversation") or {}
    account_data = payload.get("account") or {}
    sender_data = message_data.get("sender") or {}

    account_id = _first(account_data, "accountId", "account_id", "id")
    conversation_id = _first(
        message_data, "conversationId", "conversation_id"
    ) or _first(
        conversation_data,
        "id",
        "conversationId",
        "conversation_id",
        "platformConversationId",
        "platform_conversation_id",
    )
    platform = str(
        _first(message_data, "platform")
        or _first(conversation_data, "platform")
        or _first(account_data, "platform")
    ).lower()
    participant_id = str(
        _first(conversation_data, "participantId", "participant_id")
        or _first(sender_data, "id", "userId", "user_id", "phoneNumber")
    )
    if platform not in MessagingPlatform.values:
        # The endpoint may be subscribed team-wide; acknowledge other platforms
        # without attempting to map them into the Instagram/Facebook models.
        return True
    if not account_id or not conversation_id or not participant_id:
        raise WebhookPayloadError(
            "The message event is missing its account, conversation, or participant ID."
        )

    account_filters = {"zernio_account_id": str(account_id), "platform": platform}
    profile_id = _first(account_data, "profileId", "profile_id")
    if profile_id:
        account_filters["profile_id"] = str(profile_id)
    business_account = BusinessAccount.objects.filter(**account_filters).first()
    if business_account is None:
        raise WebhookAccountNotFound(
            "No connected CRM account matches this Zernio account ID."
        )

    participant_name = str(
        _first(conversation_data, "participantName", "participant_name")
        or _first(sender_data, "name", "username", "displayName")
        or participant_id
    )
    participant_avatar = str(
        _first(conversation_data, "participantAvatar", "participant_avatar")
        or _first(sender_data, "avatar", "avatarUrl", "profilePicture")
    )

    conversation, _ = MessageConversation.objects.get_or_create(
        business_account=business_account,
        zernio_conversation_id=str(conversation_id),
        defaults={
            "platform": platform,
            "participant_id": participant_id,
            "participant_name": participant_name,
            "participant_avatar": participant_avatar,
        },
    )
    changed_fields = []
    for field, value in (
        ("participant_id", participant_id),
        ("participant_name", participant_name),
        ("participant_avatar", participant_avatar),
        ("platform", platform),
    ):
        if value and getattr(conversation, field) != value:
            setattr(conversation, field, value)
            changed_fields.append(field)
    if changed_fields:
        conversation.save(update_fields=[*changed_fields, "updated_at"])
    else:
        # Bump the conversation so inboxes sort by the latest incoming message.
        conversation.save(update_fields=["updated_at"])

    platform_message_id = _first(
        message_data, "platformMessageId", "platform_message_id", "id"
    )
    if not platform_message_id:
        raise WebhookPayloadError("The message event is missing its message ID.")
    attachments = message_data.get("attachments") or []
    if not isinstance(attachments, list):
        attachments = []
    content = str(_first(message_data, "text", "content", "body"))

    message, created = Message.objects.get_or_create(
        conversation=conversation,
        zernio_message_id=str(platform_message_id),
        defaults={
            "direction": MessageType.INCOMING,
            "status": MessageStatus.READ if message_data.get("isRead") else "",
            "content": content,
            "attachments": attachments,
            "sent_at": _parse_datetime(
                _first(message_data, "sentAt", "sent_at", default=payload.get("timestamp"))
            ),
        },
    )
    if created:
        transaction.on_commit(lambda: broadcast_message(message.pk))
    return True
