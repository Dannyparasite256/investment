"""Celery application configuration."""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('cryptoinvest')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process-daily-earnings': {
        'task': 'investments.tasks.process_scheduled_earnings',
        'schedule': crontab(minute=0, hour='*/1'),  # hourly check
    },
    'expire-stale-deposits': {
        'task': 'transactions.tasks.flag_stale_deposits',
        'schedule': crontab(minute=30, hour='*/6'),
    },
    'cleanup-old-notifications': {
        'task': 'notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(minute=0, hour=3),
    },
    'daily-portfolio-snapshots': {
        'task': 'core.tasks.daily_portfolio_snapshots',
        'schedule': crontab(minute=5, hour=0),
    },
    'daily-admin-digest': {
        'task': 'core.tasks.daily_admin_digest',
        'schedule': crontab(minute=15, hour=8),
    },
    'update-market-prices': {
        'task': 'core.tasks.update_market_prices',
        'schedule': crontab(minute='*/15'),
    },
    'check-price-alerts': {
        'task': 'core.tasks.check_price_alerts_task',
        'schedule': crontab(minute='*/10'),
    },
    'weekly-user-digests': {
        'task': 'core.tasks.send_weekly_digests',
        'schedule': crontab(minute=0, hour=8, day_of_week=1),
    },
    'welcome-email-series': {
        'task': 'core.tasks.send_welcome_series',
        'schedule': crontab(minute=20, hour='*/6'),
    },
    'nudge-stale-deposits': {
        'task': 'core.tasks.nudge_stale_deposits',
        'schedule': crontab(minute=40, hour='*/12'),
    },
    'winback-inactive-users': {
        'task': 'core.tasks.winback_inactive_users',
        'schedule': crontab(minute=30, hour=10),
    },
    'withdrawal-sla-breaches': {
        'task': 'core.tasks.check_withdrawal_sla_breaches',
        'schedule': crontab(minute='*/30'),
    },
    'monthly-statement-emails': {
        'task': 'core.tasks.monthly_statement_emails',
        'schedule': crontab(minute=0, hour=9, day_of_month=1),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
