import json

from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, Conversation
from .serializers import ChatRequestSerializer, ConversationSerializer
from .services.crm_tools import CRM_TOOLS
from .services.ollama_service import chat
from .services.tool_executor import execute_tool

MAX_TOOL_ITERATIONS = 4

SYSTEM_PROMPT = (
    "You are an internal assistant for a sales CRM. Use the available tools to answer "
    "questions with real data from the system. Never invent lead names, numbers, or statuses. "
    "If a tool returns no results, say so plainly."
)


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")

        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id, user=request.user).first()
            if not conversation:
                return Response({"error": "conversation not found"}, status=404)
        else:
            conversation = Conversation.objects.create(user=request.user)

        ChatMessage.objects.create(conversation=conversation, role="user", content=user_message)

        history = list(conversation.messages.order_by("created_at").values("role", "content"))
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        for _ in range(MAX_TOOL_ITERATIONS):
            result = chat(messages, tools=CRM_TOOLS)
            reply = result["message"]

            tool_calls = reply.get("tool_calls", [])
            if not tool_calls:
                ChatMessage.objects.create(
                    conversation=conversation, role="assistant", content=reply["content"]
                )
                return Response({"conversation_id": conversation.id, "reply": reply["content"]})

            messages.append(reply)
            for call in tool_calls:
                tool_name = call["function"]["name"]
                tool_args = call["function"]["arguments"]
                try:
                    tool_result = execute_tool(request.user, tool_name, tool_args)
                except Exception as e:
                    tool_result = {"error": str(e)}

                messages.append({"role": "tool", "content": json.dumps(tool_result, default=str)})

        return Response(
            {"conversation_id": conversation.id, "reply": "I couldn't finish answering that — try rephrasing?"}
        )


class ConversationDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)