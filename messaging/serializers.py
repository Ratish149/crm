from rest_framework import serializers

from .models import BusinessAccount, Message, MessageConversation


class BusinessAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessAccount
        fields = [
            "id",
            "zernio_account_id",
            "platform",
            "platform_account_id",
            "account_name",
            "username",
            "avatar_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "direction",
            "status",
            "zernio_message_id",
            "content",
            "attachments",
            "sent_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MessageConversationSerializer(serializers.ModelSerializer):
    business_account = BusinessAccountSerializer(read_only=True)
    unread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MessageConversation
        fields = [
            "id",
            "platform",
            "zernio_conversation_id",
            "participant_id",
            "participant_name",
            "participant_avatar",
            "business_account",
            "unread_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
