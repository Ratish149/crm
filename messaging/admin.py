from django.contrib import admin

from .models import (
    BusinessAccount,
    ConnectAttempt,
    Message,
    MessageConversation,
    ZernioProfile,
    ZernioWebhookEvent,
)


@admin.register(ZernioProfile)
class ZernioProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "profile_id", "created_at")
    search_fields = ("user__username", "user__email", "profile_id")


@admin.register(ConnectAttempt)
class ConnectAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "profile_id", "created_at")
    search_fields = ("user__username", "platform")
    readonly_fields = ("state",)


@admin.register(BusinessAccount)
class BusinessAccountAdmin(admin.ModelAdmin):
    list_display = ("account_name", "username", "platform", "user", "zernio_account_id")
    list_filter = ("platform",)
    search_fields = ("account_name", "username", "zernio_account_id", "user__username")


@admin.register(MessageConversation)
class MessageConversationAdmin(admin.ModelAdmin):
    list_display = ("participant_name", "platform", "business_account", "updated_at")
    list_filter = ("platform",)
    search_fields = ("participant_name", "participant_id", "zernio_conversation_id")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("direction", "status", "conversation", "created_at")
    list_filter = ("direction", "status")


@admin.register(ZernioWebhookEvent)
class ZernioWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "event_type", "received_at")
    list_filter = ("event_type",)
    readonly_fields = ("event_id", "event_type", "received_at")
