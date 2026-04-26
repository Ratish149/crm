from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    def __str__(self):
        return self.name


class Lead(models.Model):
    STATUS_CHOICES = (
        ("new", "new"),
        ("discovery", "discovery"),
        ("quoted", "quoted"),
        ("negotiation", "negotiation"),
        ("closed", "closed"),
    )
    # Basic Contact Information
    full_name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True, null=True, unique=True)

    phone_number = models.CharField(max_length=20, unique=True)

    source = models.CharField(
        max_length=100, blank=True, help_text=_("e.g., Facebook, Referral, Walk-in")
    )
    estimate_value = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    assigned_to = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_leads",
        blank=True,
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_leads",
        blank=True,
    )
    tags = models.ManyToManyField(Tag, related_name="leads", blank=True)
    rating = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text=_("Rating from 0 to 10"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Lead")
        verbose_name_plural = _("Leads")

    def __str__(self):
        return self.full_name


class LeadDocument(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="lead_documents/")
    uploaded_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_documents",
        blank=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = _("Lead Document")
        verbose_name_plural = _("Lead Documents")

    def __str__(self):
        return f"Document for {self.lead.full_name}"


class Note(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField()
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="notes_created_by",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")

    def __str__(self):
        return f"Note on {self.lead.full_name}"


class ActivityTimeline(models.Model):
    ACTIVITY_TYPES = (
        ("lead_created", _("Lead Created")),
        ("note_added", _("Note Added")),
        ("discovery_updated", _("Discovery Updated")),
        ("document_uploaded", _("Document Uploaded")),
        ("email_sent", _("Email Sent")),
    )
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    user = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Activity Timeline")
        verbose_name_plural = _("Activity Timelines")

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead.full_name}"


class Followup(models.Model):
    STATUS_CHOICES = (
        ("pending", _("Pending")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="followups")
    followup_date = models.DateField(
        help_text=_("Date scheduled for the follow-up"), blank=True, null=True
    )
    followup_time = models.TimeField(
        help_text=_("Time scheduled for the follow-up"), blank=True, null=True
    )

    notes = models.TextField(
        blank=True, help_text=_("Notes or agenda for the follow-up")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="followups_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["followup_date", "followup_time"]
        verbose_name = _("Follow-up")
        verbose_name_plural = _("Follow-ups")

    def __str__(self):
        return f"Follow-up for {self.lead.full_name} on {self.followup_date} at {self.followup_time}"
