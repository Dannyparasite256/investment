"""Template context processors."""
from django.conf import settings


def site_settings(request):
    from django.utils import timezone as dj_tz
    from core.datetime_display import format_datetime

    ctx = {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'CryptoInvest'),
        'SITE_URL': getattr(settings, 'SITE_URL', ''),
        'theme': getattr(request, 'theme', 'dark'),
        'ui_theme': getattr(request, 'ui_theme', 'classic'),
        'DEFAULT_CURRENCY': getattr(settings, 'DEFAULT_CURRENCY', 'USD'),
        'LANGUAGES': getattr(settings, 'LANGUAGES', [('en', 'English')]),
        'user_language': getattr(request, 'user_language', 'en'),
        'user_timezone': getattr(request, 'user_timezone', getattr(settings, 'TIME_ZONE', 'UTC')),
        'now_display': format_datetime(dj_tz.now(), with_seconds=False, with_tz=True, with_weekday=True),
        'live_chat_embed': '',
        'risk_disclaimer': '',
        'show_tour': False,
        'user_vip_tier': None,
    }
    try:
        from core.models import SiteConfiguration
        cfg = SiteConfiguration.get_solo()
        ctx['live_chat_embed'] = cfg.live_chat_embed
        ctx['risk_disclaimer'] = cfg.risk_disclaimer
    except Exception:
        pass
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        ctx['show_tour'] = not getattr(user, 'tour_completed', True)
        try:
            from core.vip import get_user_tier
            tier = get_user_tier(user)
            ctx['user_vip_tier'] = tier
        except Exception:
            pass
        try:
            from wallets.display import user_display_context
            ctx.update(user_display_context(user, request=request))
        except Exception:
            ctx['display_currency'] = getattr(user, 'preferred_currency', 'USD') or 'USD'
            ctx['display_options'] = [{'code': 'USD', 'label': 'USD'}]
    return ctx
