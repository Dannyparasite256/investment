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
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
