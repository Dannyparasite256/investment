"""Audit, theme, maintenance mode, session timeout, language."""
from datetime import timedelta

from django.contrib.auth import logout
from django.shortcuts import render
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class AuditLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.client_ip = self._get_client_ip(request)
        request.client_user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        return None

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ThemeMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.theme = request.COOKIES.get('theme', 'dark')
        return None


class MaintenanceModeMiddleware(MiddlewareMixin):
    """Block non-staff users when maintenance mode is on."""

    def process_request(self, request):
        path = request.path
        if path.startswith('/static/') or path.startswith('/media/') or path.startswith('/admin/'):
            return None
        if path.startswith('/staff/'):
            return None
        try:
            from core.models import SiteConfiguration
            cfg = SiteConfiguration.get_solo()
        except Exception:
            return None
        if not cfg.maintenance_mode:
            return None
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and (user.is_staff or user.is_superuser):
            return None
        if path.startswith('/accounts/login'):
            return None
        return render(request, 'core/maintenance.html', {
            'message': cfg.maintenance_message,
            'site_name': cfg.site_name,
        }, status=503)


class SessionTimeoutMiddleware(MiddlewareMixin):
    """Idle session timeout based on SiteConfiguration."""

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        try:
            from core.models import SiteConfiguration
            minutes = SiteConfiguration.get_solo().session_timeout_minutes or 60
        except Exception:
            minutes = 60
        now = timezone.now().timestamp()
        last = request.session.get('_last_activity')
        if last and (now - last) > minutes * 60:
            logout(request)
            request.session.flush()
            return None
        request.session['_last_activity'] = now
        return None


class LanguageMiddleware(MiddlewareMixin):
    def process_request(self, request):
        lang = request.COOKIES.get('django_language') or request.GET.get('lang')
        if not lang and request.user.is_authenticated:
            lang = getattr(request.user, 'preferred_language', None)
        request.user_language = lang or 'en'
        return None


class TimezoneMiddleware(MiddlewareMixin):
    """
    Activate the user's real timezone so dates/times render accurately.
    Priority: cookie user_tz (browser) → user.preferred_timezone → settings.TIME_ZONE
    """

    def process_request(self, request):
        from django.utils import timezone as dj_tz
        from core.datetime_display import resolve_tz

        tz_name = (request.COOKIES.get('user_tz') or '').strip()
        user = getattr(request, 'user', None)
        if not tz_name and user is not None and getattr(user, 'is_authenticated', False):
            tz_name = (getattr(user, 'preferred_timezone', None) or '').strip()
        if not tz_name:
            from django.conf import settings
            tz_name = getattr(settings, 'TIME_ZONE', 'UTC') or 'UTC'

        request.user_timezone = tz_name
        try:
            dj_tz.activate(resolve_tz(tz_name))
        except Exception:
            dj_tz.deactivate()
        return None

    def process_response(self, request, response):
        from django.utils import timezone as dj_tz
        dj_tz.deactivate()
        return response


class GeoBlockMiddleware(MiddlewareMixin):
    """Optional geo allow/block on register and deposit paths."""

    PROTECTED_PREFIXES = ('/accounts/register', '/transactions/deposits/new')

    def process_request(self, request):
        path = request.path
        if not any(path.startswith(p) for p in self.PROTECTED_PREFIXES):
            return None
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and (user.is_staff or user.is_superuser):
            return None
        try:
            from core.platform_models import GeoRule
            rule = GeoRule.objects.filter(is_active=True).first()
        except Exception:
            return None
        if not rule:
            return None
        # Prefer user country_code, else CF / custom header, else empty (allow)
        code = ''
        if user and user.is_authenticated:
            code = getattr(user, 'country_code', '') or ''
        code = code or request.META.get('HTTP_CF_IPCOUNTRY', '') or request.GET.get('country', '')
        if not code:
            return None
        if not rule.is_country_allowed(code):
            return render(request, 'core/geo_blocked.html', {
                'message': rule.block_message,
            }, status=403)
        return None
