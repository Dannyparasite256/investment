"""Login history and suspicious login detection."""
from accounts.security_models import LoginHistory
from core.utils import get_client_ip


def record_login(request, user=None, email='', result=LoginHistory.Result.SUCCESS, auth_method='password'):
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    is_suspicious = False
    reason = ''
    auth_method = (auth_method or 'password')[:20]

    # Geo + timezone for accurate access location
    geo = {'country': '', 'city': '', 'region': '', 'timezone': '', 'isp': ''}
    try:
        from core.geoip import lookup_ip
        geo = lookup_ip(ip)
    except Exception:
        pass

    if user and result == LoginHistory.Result.SUCCESS:
        # New IP vs last successful logins
        known_ips = set(
            LoginHistory.objects.filter(
                user=user, result=LoginHistory.Result.SUCCESS,
            ).exclude(ip_address=None).values_list('ip_address', flat=True)[:20]
        )
        if known_ips and ip and ip not in known_ips:
            is_suspicious = True
            reason = 'Login from new IP address'
        # New country
        if geo.get('country') and geo['country'] not in ('Local', ''):
            known_countries = set(
                LoginHistory.objects.filter(
                    user=user, result=LoginHistory.Result.SUCCESS,
                ).exclude(country='').values_list('country', flat=True)[:30]
            )
            if known_countries and geo['country'] not in known_countries:
                is_suspicious = True
                reason = (reason + '; ' if reason else '') + f"New country: {geo['country']}"

        update_fields = ['last_login_ip']
        user.last_login_ip = ip
        # Prefer browser tz cookie; else geo timezone
        browser_tz = (request.COOKIES.get('user_tz') or '').strip()
        tz_name = browser_tz or (geo.get('timezone') or '')
        if tz_name and not (user.preferred_timezone or '').strip():
            user.preferred_timezone = tz_name[:64]
            update_fields.append('preferred_timezone')
        elif tz_name and browser_tz:
            user.preferred_timezone = browser_tz[:64]
            if 'preferred_timezone' not in update_fields:
                update_fields.append('preferred_timezone')
        if geo.get('country') and geo['country'] not in ('Local', '') and not user.country:
            user.country = geo['country'][:100]
            update_fields.append('country')
        user.save(update_fields=update_fields)

    # Burst failures from same IP
    if result == LoginHistory.Result.FAILED and ip:
        from django.utils import timezone
        from datetime import timedelta
        recent_fails = LoginHistory.objects.filter(
            ip_address=ip,
            result=LoginHistory.Result.FAILED,
            created_at__gte=timezone.now() - timedelta(minutes=15),
        ).count()
        if recent_fails >= 4:
            is_suspicious = True
            reason = 'Multiple failed login attempts'
            result = LoginHistory.Result.SUSPICIOUS

    entry = LoginHistory.objects.create(
        user=user,
        email_attempted=email or (user.email if user else ''),
        ip_address=ip,
        user_agent=ua,
        country=geo.get('country', '') or '',
        city=geo.get('city', '') or '',
        region=geo.get('region', '') or '',
        timezone_name=geo.get('timezone', '') or '',
        isp=geo.get('isp', '') or '',
        result=result,
        is_suspicious=is_suspicious,
        suspicion_reason=reason,
        session_key=request.session.session_key or '',
        auth_method=auth_method,
    )

    if user and result == LoginHistory.Result.SUCCESS:
        try:
            from accounts.social_features import send_login_alert_email, set_login_method
            set_login_method(user, auth_method)
            # Always email on suspicious; otherwise email when preference on
            if entry.is_suspicious or getattr(user, 'login_alert_emails', True):
                send_login_alert_email(user, entry)
        except Exception:
            pass

    if is_suspicious and user:
        from notifications.models import Notification, notify
        loc = entry.location_display
        notify(
            user,
            'Suspicious login detected',
            f'A login from {ip} ({loc}) was flagged: {reason}',
            level=Notification.Level.WARNING,
            category=Notification.Category.SECURITY,
        )
    return entry
