from rest_framework import serializers
from .models import Conversation, ChatMessage


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "created_at", "messages"]