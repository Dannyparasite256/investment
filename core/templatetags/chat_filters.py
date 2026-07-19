"""Chat helpers: auto-linkify URLs in messages + WhatsApp day labels."""
import re
from datetime import date, datetime
from html import escape

from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()

_URL_RE = re.compile(
    r'((?:https?://|www\.)[^\s<]+)',
    re.IGNORECASE,
)


def _split_url(token: str) -> tuple[str, str]:
    url, trail = token, ''
    while url and url[-1] in '.,;:!?)\"\']':
        trail = url[-1] + trail
        url = url[:-1]
    return url, trail


def _normalize_href(url: str) -> str:
    if re.match(r'^https?://', url, re.I):
        return url
    if url.lower().startswith('www.'):
        return 'https://' + url
    return url


@register.filter(name='chat_links')
def chat_links(value: str) -> str:
    """
    Escape text, convert newlines to <br>, and wrap http(s)/www URLs
    in <a target="_blank" rel="noopener noreferrer">.
    """
    if value is None:
        return ''
    text = escape(str(value))
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '<br>')

    def repl(match: re.Match) -> str:
        raw = match.group(1)
        url, trail = _split_url(raw)
        if len(url) < 4:
            return match.group(0)
        href = _normalize_href(url)
        if not re.match(r'^https?://', href, re.I):
            return match.group(0)
        safe_href = href.replace('"', '%22')
        return (
            f'<a class="chat-link" href="{safe_href}" target="_blank" '
            f'rel="noopener noreferrer">{url}</a>{trail}'
        )

    return mark_safe(_URL_RE.sub(repl, text))


@register.filter(name='wa_day')
def wa_day(value) -> str:
    """WhatsApp-style day label: Today / Yesterday / weekday / date."""
    if not value:
        return ''
    if isinstance(value, datetime):
        d = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    elif isinstance(value, date):
        d = value
    else:
        return ''
    today = timezone.localdate()
    delta = (today - d).days
    if delta == 0:
        return 'Today'
    if delta == 1:
        return 'Yesterday'
    if 1 < delta < 7:
        return d.strftime('%A')
    if d.year == today.year:
        return d.strftime('%a, %b %d')
    return d.strftime('%b %d, %Y')


@register.filter(name='wa_day_key')
def wa_day_key(value) -> str:
    """Stable day key for grouping messages."""
    if not value:
        return ''
    if isinstance(value, datetime):
        d = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    elif isinstance(value, date):
        d = value
    else:
        return ''
    return d.isoformat()
