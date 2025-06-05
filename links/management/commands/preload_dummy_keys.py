from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from links.models import UserAPIKey

SERVICES = [
    {"key": "psi", "name": "Google PageSpeed Insights"},
    {"key": "uptimerobot", "name": "UptimeRobot"},
]
DUMMY_KEY = "DUMMY_KEY_CHANGE_ME"


class Command(BaseCommand):
    help = "Preload dummy API keys for all users and all services."

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        for user in users:
            for service in SERVICES:
                obj, created = UserAPIKey.objects.get_or_create(
                    user=user,
                    service=service["key"],
                    defaults={"key": DUMMY_KEY, "status": "Not set"},
                )
                if created:
                    created_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Preloaded dummy keys for {created_count} user-service pairs."
            )
        )
