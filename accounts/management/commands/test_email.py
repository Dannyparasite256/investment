"""
Send a test email (or print why mail is not configured).

Usage:
  python manage.py test_email you@example.com
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP / inbox delivery'

    def add_arguments(self, parser):
        parser.add_argument('to_email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        to = options['to_email'].strip()
        backend = settings.EMAIL_BACKEND
        self.stdout.write(f'EMAIL_BACKEND = {backend}')
        self.stdout.write(f'EMAIL_HOST    = {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USER    = {settings.EMAIL_HOST_USER or "(empty)"}')
        self.stdout.write(f'FROM          = {settings.DEFAULT_FROM_EMAIL}')

        if 'console' in (backend or '').lower():
            self.stderr.write(self.style.ERROR(
                '\nEmail is in CONSOLE mode — messages only print in this terminal / server log.\n'
                'They will NEVER appear in a real inbox.\n\n'
                'Fix: edit .env and set SMTP, e.g. Gmail App Password:\n'
                '  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n'
                '  EMAIL_HOST=smtp.gmail.com\n'
                '  EMAIL_PORT=587\n'
                '  EMAIL_USE_TLS=True\n'
                '  EMAIL_HOST_USER=your@gmail.com\n'
                '  EMAIL_HOST_PASSWORD=your-16-char-app-password\n'
                '  DEFAULT_FROM_EMAIL=CryptoInvest <your@gmail.com>\n'
                'Then reload the web app (PythonAnywhere) or restart runserver.\n'
            ))
            return

        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            self.stderr.write(self.style.ERROR(
                'EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is empty in .env'
            ))
            return

        try:
            n = send_mail(
                subject=f'Test email — {settings.SITE_NAME}',
                message=(
                    f'This is a test from {settings.SITE_NAME}.\n'
                    f'If you received this, SMTP is working.\n'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Sent OK (send_mail returned {n}). Check inbox + spam for {to}.'
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Send failed: {exc}'))
            self.stderr.write(
                'Common fixes: Gmail App Password (not normal password), '
                '2FA enabled on Google, PythonAnywhere allows smtp.gmail.com:587, '
                'or use Brevo free SMTP.'
            )
