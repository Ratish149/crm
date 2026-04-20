from django.db import models
from django.utils.translation import gettext_lazy as _

from lead.models import Lead


class DiscoveryCategory(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Discovery Category")
        verbose_name_plural = _("Discovery Categories")

    def __str__(self):
        return self.name


class DiscoveryQuestion(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Discovery Question")
        verbose_name_plural = _("Discovery Questions")

    def __str__(self):
        return self.title


class DiscoveryOption(models.Model):
    question = models.ForeignKey(
        DiscoveryQuestion, on_delete=models.CASCADE, related_name="options"
    )
    category = models.ForeignKey(
        DiscoveryCategory,
        on_delete=models.CASCADE,
        related_name="options",
        blank=True,
        null=True,
    )
    text = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.question.title} - {self.text}"


class LeadDiscoveryAnswer(models.Model):
    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name="discovery_answers"
    )
    question = models.ForeignKey(
        DiscoveryQuestion, on_delete=models.CASCADE, related_name="lead_answers"
    )
    options = models.ManyToManyField(DiscoveryOption, related_name="lead_selections")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("lead", "question")
        verbose_name = _("Lead Discovery Answer")
        verbose_name_plural = _("Lead Discovery Answers")

    def __str__(self):
        return f"{self.lead.full_name} - {self.question.title}"
