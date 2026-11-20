from datetime import datetime

from .zernio_service import ZernioService
from messaging.models import Message, MessageType, MessageConversation


def sync_conversation_history(conversation: MessageConversation, max_pages=5):
    service = ZernioService()
    cursor = None
    for _ in range(max_pages):
        result = service.client.messages.get_inbox_conversation_messages(
            conversation_id=conversation.zernio_conversation_id,
            account_id=conversation.business_account.zernio_account_id,
            limit=100,
            sort_order="asc",
            cursor=cursor,
        )
        if hasattr(result, "model_dump"):
            result = result.model_dump(by_alias=True)
        if not isinstance(result, dict):
            break
        payload = result.get("data", result)
        page_messages = payload.get("messages", []) if isinstance(payload, dict) else []
        for item in page_messages if isinstance(page_messages, list) else []:
            if hasattr(item, "model_dump"):
                item = item.model_dump(by_alias=True)
            if not isinstance(item, dict):
                continue
            message_id = item.get("id") or item.get("messageId")
            if not message_id:
                continue
            direction = MessageType.OUTGOING if str(item.get("direction", "")).lower() == "outgoing" else MessageType.INCOMING
            sent_at = item.get("sentAt") or item.get("createdAt")
            if sent_at:
                try:
                    sent_at = datetime.fromisoformat(str(sent_at).replace("Z", "+00:00"))
                except (TypeError, ValueError):
                    sent_at = None
            Message.objects.update_or_create(
                conversation=conversation,
                zernio_message_id=str(message_id),
                defaults={
                    "direction": direction,
                    "status": str(item.get("deliveryStatus", "")).upper(),
                    "content": str(item.get("message") or ""),
                    "attachments": item.get("attachments") or [],
                    "sent_at": sent_at,
                },
            )
        pagination = payload.get("pagination", {}) if isinstance(payload, dict) else {}
        cursor = pagination.get("nextCursor") if isinstance(pagination, dict) else None
        if not cursor or not pagination.get("hasMore"):
            break
