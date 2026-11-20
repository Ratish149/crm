from django.core.management.base import BaseCommand, CommandError

from messaging.services.zernio_service import ZernioService, ZernioServiceError


class Command(BaseCommand):
    help = "Register or update the Zernio incoming-message webhook endpoint."

    def handle(self, *args, **options):
        try:
            ZernioService().register_webhook()
        except ZernioServiceError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Zernio message webhook is registered."))
