import hashlib
import hmac
import json
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponseRedirect
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import reverse

from .models import BusinessAccount, Message, MessageConversation, MessageStatus, MessageType, MessagingPlatform
from .serializers import BusinessAccountSerializer, MessageConversationSerializer, MessageSerializer
from .realtime import broadcast_message
from .services.zernio_service import ZernioService, ZernioServiceError
from .services.inbox_service import sync_conversation_history
from .services.webhook_service import (
    WebhookAccountNotFound,
    WebhookPayloadError,
    receive_zernio_event,
)


class ZernioConnectedAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = BusinessAccount.objects.filter(user=request.user)
        return Response(BusinessAccountSerializer(accounts, many=True).data)


class ZernioDisconnectAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, account_id):
        account = get_object_or_404(BusinessAccount, id=account_id, user=request.user)
        try:
            ZernioService().disconnect_account(account.zernio_account_id)
        except ZernioServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ZernioConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, account_id):
        conversations = MessageConversation.objects.filter(
            business_account__user=request.user,
            business_account_id=account_id,
        ).select_related("business_account").annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__direction=MessageType.INCOMING)
                & ~Q(messages__status=MessageStatus.READ),
            )
        )
        return Response(MessageConversationSerializer(conversations, many=True).data)


class ConversationSocketTicketView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"ticket": signing.dumps({"user_id": request.user.pk}, salt="messaging.websocket")})


class UnreadCountsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = Message.objects.filter(
            conversation__business_account__user=request.user,
            direction=MessageType.INCOMING,
        ).exclude(status=MessageStatus.READ).values("conversation_id").annotate(count=Count("id"))
        return Response({str(row["conversation_id"]): row["count"] for row in rows})


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation(self, request, conversation_id):
        return get_object_or_404(
            MessageConversation.objects.select_related("business_account"),
            pk=conversation_id,
            business_account__user=request.user,
        )

    def get(self, request, conversation_id):
        conversation = self.get_conversation(request, conversation_id)
        if request.query_params.get("sync") == "1":
            try:
                sync_conversation_history(conversation)
            except Exception:
                # Locally persisted webhook history remains available if Zernio
                # is temporarily unavailable or this account lacks inbox history.
                pass
        messages = conversation.messages.all().order_by("sent_at", "created_at")
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, conversation_id):
        conversation = self.get_conversation(request, conversation_id)
        content = request.data.get("message", "")
        if not isinstance(content, str) or not content.strip():
            return Response({"detail": "Message text is required."}, status=status.HTTP_400_BAD_REQUEST)
        if len(content) > 10000:
            return Response({"detail": "Message text is too long."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            service = ZernioService()
            client = service.client
            send = getattr(client.messages, "send_inbox_message")
            result = send(
                conversation_id=conversation.zernio_conversation_id,
                account_id=conversation.business_account.zernio_account_id,
                message=content.strip(),
            )
            if hasattr(result, "model_dump"):
                result = result.model_dump(by_alias=True)
            elif not isinstance(result, dict):
                result = {}
        except Exception:
            return Response({"detail": "Could not send this message through Zernio."}, status=status.HTTP_502_BAD_GATEWAY)
        zernio_id = result.get("id") or result.get("messageId") or result.get("message_id") or ""
        with transaction.atomic():
            message = Message.objects.create(
                conversation=conversation,
                direction=MessageType.OUTGOING,
                status=MessageStatus.SENT,
                zernio_message_id=str(zernio_id),
                content=content.strip(),
                attachments=result.get("attachments") or [],
                sent_at=timezone.now(),
            )
            transaction.on_commit(lambda: broadcast_message(message.pk))
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ConversationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = get_object_or_404(
            MessageConversation,
            pk=conversation_id,
            business_account__user=request.user,
        )
        conversation.messages.filter(direction=MessageType.INCOMING).exclude(
            status=MessageStatus.READ
        ).update(status=MessageStatus.READ)
        return Response({"read": True})


class ZernioConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, platform):
        if platform.lower() not in MessagingPlatform.values:
            return Response(
                {"detail": "Only Instagram and Facebook accounts are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return_url = request.query_params.get("return_url", "")
        return_parts = urlsplit(return_url)
        return_origin = f"{return_parts.scheme}://{return_parts.netloc}"
        if (
            return_parts.scheme not in {"http", "https"}
            or not return_parts.netloc
            or return_origin not in getattr(settings, "CORS_ALLOWED_ORIGINS", [])
        ):
            return Response(
                {"detail": "A valid frontend return_url is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        callback_url = request.build_absolute_uri(
            reverse("messaging:connect-callback", kwargs={"platform": platform.lower()})
        )
        try:
            result = ZernioService().create_connect_url(
                request.user,
                platform,
                callback_url=callback_url,
                return_url=return_url,
            )
        except ZernioServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result, status=status.HTTP_200_OK)


class ZernioConnectCallbackView(APIView):
    # Zernio redirects here from OAuth; persisted state binds the callback to its owner.
    permission_classes = [AllowAny]

    def get(self, request, platform):
        state = request.query_params.get("state")
        account_id = request.query_params.get("accountId")
        profile_id = request.query_params.get("profileId")
        connected_platform = request.query_params.get("connected", platform).lower()
        if not state or not account_id:
            return Response(
                {"detail": "The Zernio callback requires state and accountId."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if connected_platform != platform.lower():
            return Response(
                {"detail": "The connected platform does not match the callback route."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            account, return_url = ZernioService().complete_connect(
                platform=platform,
                state=state,
                account_id=account_id,
                profile_id=profile_id,
                username=request.query_params.get("username", ""),
            )
        except ZernioServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if return_url:
            parts = urlsplit(return_url)
            query = dict(parse_qsl(parts.query, keep_blank_values=True))
            query["social_connected"] = platform.lower()
            return HttpResponseRedirect(
                urlunsplit(
                    (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
                )
            )
        return Response(
            BusinessAccountSerializer(account).data,
            status=status.HTTP_200_OK,
        )


class ZernioWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        secret = getattr(settings, "ZERNIO_WEBHOOK_SECRET", "")
        if not secret:
            return Response(
                {"detail": "Zernio webhook secret is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        raw_body = request.body
        signature = request.headers.get("X-Zernio-Signature", "")
        expected_signature = hmac.new(
            secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        if not signature or not hmac.compare_digest(expected_signature, signature):
            return Response(
                {"detail": "Invalid Zernio webhook signature."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                {"detail": "Webhook body must be valid JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(payload, dict):
            return Response(
                {"detail": "Webhook body must be a JSON object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_type = payload.get("event")
        if not isinstance(event_type, str) or not event_type:
            return Response(
                {"detail": "Webhook event type is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        header_event_type = request.headers.get("X-Zernio-Event")
        if header_event_type and event_type != header_event_type:
            return Response(
                {"detail": "Webhook event header does not match its payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_id = payload.get("id") or request.headers.get("X-Zernio-Event-Id")
        header_event_id = request.headers.get("X-Zernio-Event-Id")
        if not event_id or (header_event_id and str(event_id) != header_event_id):
            return Response(
                {"detail": "A matching webhook event ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            receive_zernio_event(payload, str(event_id))
        except WebhookAccountNotFound as exc:
            # A retry allows account registration/connect data to catch up.
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except WebhookPayloadError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"received": True}, status=status.HTTP_200_OK)
