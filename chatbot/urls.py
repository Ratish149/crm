# chatbot/urls.py
from django.urls import path
from .views import ChatView, ConversationDetailView, SummaryView

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("chat/<int:pk>/", ConversationDetailView.as_view(), name="chat-detail"),
    path("chat/summarize/<int:pk>/", SummaryView.as_view(), name="lead-summary")
]