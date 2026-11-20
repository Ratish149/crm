import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message

logger = logging.getLogger(__name__)


def message_group_name(conversation_id):
    return f"conversation_{str(conversation_id).replace('-', '')}"


def inbox_group_name(user_id):
    return f"inbox_user_{user_id}"


def broadcast_message(message_id):
    message = Message.objects.select_related("conversation").get(pk=message_id)
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    from .serializers import BusinessAccountSerializer, MessageSerializer

    conversation = message.conversation
    unread_count = conversation.messages.filter(direction="INCOMING").exclude(status="READ").count()
    event_message = MessageSerializer(message).data
    event_conversation = {
        "id": str(conversation.pk),
        "platform": conversation.platform,
        "participant_id": conversation.participant_id,
        "participant_name": conversation.participant_name,
        "participant_avatar": conversation.participant_avatar,
        "updated_at": conversation.updated_at.isoformat(),
        "business_account": BusinessAccountSerializer(conversation.business_account).data,
        "unread_count": unread_count,
    }

    try:
        async_to_sync(channel_layer.group_send)(
            message_group_name(message.conversation_id),
            {"type": "message.created", "message": event_message},
        )
        async_to_sync(channel_layer.group_send)(
            inbox_group_name(conversation.business_account.user_id),
            {"type": "inbox.message", "message": event_message, "conversation": event_conversation},
        )
    except Exception:
        logger.exception("Could not broadcast message %s over the WebSocket channel", message_id)
