from django.core.management.base import BaseCommand
from lead.tasks import check_and_notify_upcoming_followups

class Command(BaseCommand):
    help = 'Check and send notifications for upcoming followups'

    def handle(self, *args, **options):
        self.stdout.write("Checking for upcoming followups...")
        notifications_sent = check_and_notify_upcoming_followups()
        self.stdout.write(self.style.SUCCESS(f"Done. Notifications sent: {notifications_sent}"))
