# chatbot/urls.py
from django.urls import path
from .views import ChatView, ConversationDetailView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/<int:pk>/", ConversationDetailView.as_view(), name="chat-detail"),
]