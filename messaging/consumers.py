from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core import signing

from .models import MessageConversation
from .realtime import inbox_group_name, message_group_name


class ConversationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        ticket = self.scope["url_route"]["kwargs"].get("ticket", "")
        conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        try:
            data = signing.loads(ticket, salt="messaging.websocket", max_age=60)
            allowed = await self._can_access(conversation_id, data.get("user_id"))
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            allowed = False
        if not allowed:
            await self.close(code=4401)
            return
        self.group_name = message_group_name(conversation_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def message_created(self, event):
        await self.send_json({"type": "message.created", "message": event["message"]})

    @database_sync_to_async
    def _can_access(self, conversation_id, user_id):
        return MessageConversation.objects.filter(
            pk=conversation_id, business_account__user_id=user_id
        ).exists()


class InboxConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        ticket = self.scope["url_route"]["kwargs"].get("ticket", "")
        try:
            data = signing.loads(ticket, salt="messaging.websocket", max_age=60)
            user_id = data.get("user_id")
            if not user_id:
                raise signing.BadSignature("Missing user")
        except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
            await self.close(code=4401)
            return
        self.group_name = inbox_group_name(user_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def inbox_message(self, event):
        await self.send_json({
            "type": "message.created",
            "message": event["message"],
            "conversation": event["conversation"],
        })
