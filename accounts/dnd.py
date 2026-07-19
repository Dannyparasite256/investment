"""Do Not Disturb schedule helpers."""
from __future__ import annotations

from datetime import datetime, time

from django.utils import timezone


def _local_now(user):
    tz_name = (getattr(user, 'preferred_timezone', None) or '').strip()
    if tz_name:
        try:
            from zoneinfo import ZoneInfo
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return timezone.localtime()


def user_in_dnd(user) -> bool:
    """True if user has DND enabled and current local time is inside the window."""
    if not user or not getattr(user, 'dnd_enabled', False):
        return False
    start = getattr(user, 'dnd_start', None)
    end = getattr(user, 'dnd_end', None)
    if not start or not end:
        return False
    now_t = _local_now(user).time()
    # Same-day window e.g. 09:00–17:00
    if start <= end:
        return start <= now_t < end
    # Overnight window e.g. 22:00–07:00
    return now_t >= start or now_t < end
