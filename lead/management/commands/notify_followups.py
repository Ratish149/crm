from django.core.management.base import BaseCommand

from lead.tasks import check_and_notify_upcoming_followups


class Command(BaseCommand):
    help = "Checks for upcoming follow-ups and sends email notifications."

    def handle(self, *args, **options):
        self.stdout.write("Checking for upcoming follow-ups...")
        notifications_sent = check_and_notify_upcoming_followups()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully sent {notifications_sent} notifications.")
        )
