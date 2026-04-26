from datetime import timedelta

from django.utils import timezone

from crm.utils import send_resend_email

from .models import Followup


def check_and_notify_upcoming_followups():
    today = timezone.localdate()
    # Look for pending followups scheduled for today or tomorrow
    upcoming_followups = Followup.objects.filter(
        status="pending", followup_date__range=[today, today + timedelta(days=1)]
    ).select_related("lead")

    notifications_sent = 0
    recipient_email = "baliyotechnologies@gmail.com"

    for followup in upcoming_followups:
        lead = followup.lead
        subject = f"Upcoming Follow-up Reminder: {lead.full_name}"
        html_content = f"""
            <h3>Upcoming Follow-up Reminder</h3>
            <p>This is a reminder for your follow-up with <strong>{lead.full_name}</strong>.</p>
            <p><strong>Date:</strong> {followup.followup_date}</p>
            <p><strong>Time:</strong> {followup.followup_time or "Not specified"}</p>
            <p><strong>Notes:</strong> {followup.notes or "No notes provided"}</p>
            <p>View lead details: <a href="https://crm.baliyotech.com/dashboard/leads/{lead.id}">Click here</a></p>
        """
        send_resend_email(recipient_email, subject, html_content)
        notifications_sent += 1

    return notifications_sent
