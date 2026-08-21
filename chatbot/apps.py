from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    name = 'chatbot'

    def ready(self):
        from . import signals  # noqa: F401
