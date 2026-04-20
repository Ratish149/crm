from .models import ActivityTimeline


def log_activity(lead, activity_type, user=None, description=None):
    """
    Utility function to log activities in the ActivityTimeline.
    """
    return ActivityTimeline.objects.create(
        lead=lead, activity_type=activity_type, user=user, description=description or {}
    )
