from django.urls import path

from .views import (
    ZernioConnectCallbackView,
    ZernioConnectedAccountsView,
    ZernioConnectView,
    ZernioDisconnectAccountView,
    ZernioConversationsView,
    ConversationMessagesView,
    ConversationSocketTicketView,
    ConversationReadView,
    UnreadCountsView,
    ZernioWebhookView,
)

app_name = "messaging"

urlpatterns = [
    path("messages/socket-ticket/", ConversationSocketTicketView.as_view(), name="socket-ticket"),
    path("messages/unread-counts/", UnreadCountsView.as_view(), name="unread-counts"),
    path("messages/conversations/<uuid:conversation_id>/messages/", ConversationMessagesView.as_view(), name="conversation-messages"),
    path("messages/conversations/<uuid:conversation_id>/read/", ConversationReadView.as_view(), name="conversation-read"),
    path("messages/webhooks/zernio/", ZernioWebhookView.as_view(), name="zernio-webhook"),
    path("messages/accounts/", ZernioConnectedAccountsView.as_view(), name="accounts"),
    path("messages/accounts/<uuid:account_id>/disconnect/", ZernioDisconnectAccountView.as_view(), name="disconnect-account"),
    path(
        "messages/accounts/<uuid:account_id>/conversations/",
        ZernioConversationsView.as_view(),
        name="conversations",
    ),
    path("messages/connect/<str:platform>/", ZernioConnectView.as_view(), name="connect"),
    path(
        "messages/connect/callback/<str:platform>/",
        ZernioConnectCallbackView.as_view(),
        name="connect-callback",
    ),
]
