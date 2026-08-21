from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from lead.models import ActivityTimeline, Followup, Lead, LeadDocument, Note

SUMMARY_FIELDS = {"summary", "summary_generated_at"}


def _invalidate_summary(lead_id):
    if lead_id is None:
        return
    Lead.objects.filter(pk=lead_id).update(
        summary=None, summary_generated_at=None
    )


@receiver(post_save, sender=Lead)
def invalidate_on_lead_save(sender, instance, update_fields=None, **kwargs):
    if update_fields and SUMMARY_FIELDS.issuperset(update_fields):
        return
    _invalidate_summary(instance.pk)


@receiver(post_save, sender=Note)
@receiver(post_save, sender=Followup)
@receiver(post_save, sender=LeadDocument)
@receiver(post_save, sender=ActivityTimeline)
def invalidate_on_related_save(sender, instance, **kwargs):
    _invalidate_summary(instance.lead_id)


@receiver(post_delete, sender=Note)
@receiver(post_delete, sender=Followup)
@receiver(post_delete, sender=LeadDocument)
@receiver(post_delete, sender=ActivityTimeline)
def invalidate_on_related_delete(sender, instance, **kwargs):
    _invalidate_summary(instance.lead_id)


@receiver(m2m_changed, sender=Lead.tags.through)
def invalidate_on_tags_change(sender, instance, action, **kwargs):
    if action in ("post_add", "post_remove", "post_clear"):
        _invalidate_summary(instance.pk)
