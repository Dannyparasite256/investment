"""
Run lifecycle / ops email jobs manually (useful on PythonAnywhere without Celery beat).

  python manage.py run_email_jobs
  python manage.py run_email_jobs --only digest
  python manage.py run_email_jobs --only welcome,sla,nudge,winback,weekly,statements
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run branded email background jobs once'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            type=str,
            default='all',
            help='Comma list: digest,welcome,nudge,winback,sla,weekly,statements,all',
        )

    def handle(self, *args, **options):
        from core import tasks

        only = {x.strip().lower() for x in (options['only'] or 'all').split(',') if x.strip()}
        if 'all' in only:
            only = {'digest', 'welcome', 'nudge', 'winback', 'sla', 'weekly', 'statements'}

        mapping = {
            'digest': ('Staff ops digest', tasks.daily_admin_digest),
            'welcome': ('Welcome series', tasks.send_welcome_series),
            'nudge': ('Stale deposit nudges', tasks.nudge_stale_deposits),
            'winback': ('Win-back emails', tasks.winback_inactive_users),
            'sla': ('Withdrawal SLA breaches', tasks.check_withdrawal_sla_breaches),
            'weekly': ('Weekly digests', tasks.send_weekly_digests),
            'statements': ('Monthly statements', tasks.monthly_statement_emails),
        }
        for key, (label, fn) in mapping.items():
            if key not in only:
                continue
            self.stdout.write(f'Running {label}…')
            try:
                result = fn()
                self.stdout.write(self.style.SUCCESS(f'  OK → {result}'))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  FAIL {label}: {exc}'))
