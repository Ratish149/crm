from django.urls import re_path

from .consumers import ConversationConsumer, InboxConsumer

websocket_urlpatterns = [
    re_path(r"^ws/messages/inbox/(?P<ticket>[^/]+)/$", InboxConsumer.as_asgi()),
    re_path(
        r"^ws/messages/conversations/(?P<conversation_id>[0-9a-fA-F-]+)/(?P<ticket>[^/]+)/$",
        ConversationConsumer.as_asgi(),
    ),
]
