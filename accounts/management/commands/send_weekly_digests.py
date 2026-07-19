"""Send weekly portfolio digest emails to opted-in users."""
from django.core.management.base import BaseCommand

from accounts.models import User
from accounts.social_features import send_weekly_digest


class Command(BaseCommand):
    help = 'Email weekly portfolio digests to users with weekly_digest_emails=True'

    def handle(self, *args, **options):
        qs = User.objects.filter(is_active=True, weekly_digest_emails=True)
        sent = 0
        for user in qs.iterator():
            if send_weekly_digest(user):
                sent += 1
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} weekly digests'))
