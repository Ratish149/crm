import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ZernioProfile(BaseModel):
    """A Zernio profile associated with one CRM user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="zernio_profile",
    )
    profile_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Zernio profile {self.profile_id} ({self.user})"


class ConnectAttempt(BaseModel):
    """Short lived record used to associate a Zernio OAuth callback to its owner."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="zernio_connect_attempts",
    )
    platform = models.CharField(max_length=50)
    profile_id = models.CharField(max_length=255)
    state = models.CharField(max_length=512, unique=True)
    return_url = models.URLField(max_length=1000, blank=True)


class BusinessAccount(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    zernio_account_id = models.CharField(max_length=255)
    profile_id = models.CharField(max_length=255)
    platform = models.CharField(max_length=50)
    platform_account_id = models.CharField(max_length=255, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(max_length=1000, blank=True)
    account_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["platform", "account_name", "username"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "zernio_account_id"],
                name="uniq_user_zernio_social_account",
            )
        ]

    def __str__(self):
        return self.account_name or self.username or self.zernio_account_id


class MessagingPlatform(models.TextChoices):
    INSTAGRAM = "instagram", "Instagram"
    FACEBOOK = "facebook", "Facebook"


class MessageConversation(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    platform = models.CharField(max_length=50, choices=MessagingPlatform.choices)
    zernio_conversation_id = models.CharField(max_length=255, blank=True)
    participant_id = models.CharField(max_length=255)
    participant_name = models.CharField(max_length=255)
    participant_avatar = models.URLField(max_length=1000, blank=True)
    business_account = models.ForeignKey(
        BusinessAccount,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["business_account", "zernio_conversation_id"],
                condition=~models.Q(zernio_conversation_id=""),
                name="uniq_account_zernio_conversation",
            )
        ]


class MessageType(models.TextChoices):
    INCOMING = "INCOMING", "Incoming"
    OUTGOING = "OUTGOING", "Outgoing"


class MessageStatus(models.TextChoices):
    SENT = "SENT", "Sent"
    DELIVERED = "DELIVERED", "Delivered"
    READ = "READ", "Read"


class Message(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    direction = models.CharField(max_length=10, choices=MessageType.choices)
    status = models.CharField(
        max_length=12, choices=MessageStatus.choices, blank=True
    )
    zernio_message_id = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    conversation = models.ForeignKey(
        MessageConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    class Meta:
        ordering = ["created_at"]


class ZernioWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, primary_key=True)
    event_type = models.CharField(max_length=100)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.event_type}: {self.event_id}"
