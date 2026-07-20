"""
Render branded email HTML to a local file for design review.

  python manage.py preview_email
  # opens templates/emails/_preview_otp.html and _preview_action.html in project root previews/
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from core.mail import render_action_email, render_otp_email, site_name, site_url


class Command(BaseCommand):
    help = 'Write sample branded HTML emails for visual preview'

    def handle(self, *args, **options):
        out = Path(settings.BASE_DIR) / 'previews'
        out.mkdir(exist_ok=True)

        otp_html, _ = render_otp_email(
            name='Alex Investor',
            code='482917',
            purpose_label='password reset',
            minutes=10,
            heading='Reset your password',
            intro='Enter this code to choose a new password, or tap the button for a secure one-click reset.',
            badge='Password reset',
            action_url=f'{site_url() or "https://example.com"}/accounts/password-reset/demo-token/',
            action_label='Reset password securely',
            subject_line='Password reset code',
        )
        action_html, _ = render_action_email(
            name='Alex Investor',
            heading='Confirm your email address',
            paragraphs=[
                f'Thanks for joining {site_name()}. Confirm your email so we can secure your account.',
                'This only takes a second — click the button below.',
            ],
            action_url=f'{site_url() or "https://example.com"}/accounts/verify-email/demo/',
            action_label='Verify email address',
            badge='Welcome',
            secondary_note='If you did not create an account, ignore this message.',
            subject_line='Verify your email',
        )

        p1 = out / 'otp_email.html'
        p2 = out / 'action_email.html'
        p1.write_text(otp_html, encoding='utf-8')
        p2.write_text(action_html, encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Wrote {p1}'))
        self.stdout.write(self.style.SUCCESS(f'Wrote {p2}'))
        self.stdout.write('Open these files in a browser to review design.')
