"""Accurate local datetime formatting with timezone labels."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone as dj_tz
from django.utils.formats import date_format


def resolve_tz(name: str | None):
    name = (name or '').strip()
    if name:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            pass
    try:
        return ZoneInfo(getattr(settings, 'TIME_ZONE', 'UTC') or 'UTC')
    except ZoneInfoNotFoundError:
        return dj_tz.utc


def to_local(dt, tz_name: str | None = None):
    """Convert aware/naive datetime to target timezone (aware)."""
    if dt is None:
        return None
    if dj_tz.is_naive(dt):
        dt = dj_tz.make_aware(dt, dj_tz.get_default_timezone())
    tz = resolve_tz(tz_name) if tz_name else dj_tz.get_current_timezone()
    return dt.astimezone(tz)


def format_datetime(
    dt,
    tz_name: str | None = None,
    *,
    with_seconds: bool = False,
    with_tz: bool = True,
    with_weekday: bool = False,
) -> str:
    """
    Human-accurate stamp, e.g.:
      Sat, 18 Jul 2026 · 16:45 EAT
      18 Jul 2026 · 16:45:12 EAT
    """
    if dt is None:
        return '—'
    local = to_local(dt, tz_name)
    if local is None:
        return '—'

    if with_weekday:
        day = local.strftime('%a, %d %b %Y')
    else:
        day = local.strftime('%d %b %Y')

    if with_seconds:
        clock = local.strftime('%H:%M:%S')
    else:
        clock = local.strftime('%H:%M')

    if not with_tz:
        return f'{day} · {clock}'

    # Prefer short zone name (EAT, UTC, PST…)
    z = local.tzname() or ''
    # Also append IANA if short name is numeric offset only
    iana = ''
    try:
        iana = str(local.tzinfo)
    except Exception:
        iana = ''
    if z and not z.startswith(('+', '-')):
        return f'{day} · {clock} {z}'
    if iana:
        return f'{day} · {clock} {iana}'
    return f'{day} · {clock}'


def format_datetime_location(dt, location: str = '', tz_name: str | None = None) -> str:
    """Date/time + optional access location."""
    base = format_datetime(dt, tz_name, with_seconds=False, with_tz=True, with_weekday=True)
    location = (location or '').strip()
    if location:
        return f'{base} · {location}'
    return base
