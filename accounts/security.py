"""Login history and suspicious login detection."""
from accounts.security_models import LoginHistory
from core.utils import get_client_ip


def record_login(request, user=None, email='', result=LoginHistory.Result.SUCCESS):
    ip = get_client_ip(request)
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    is_suspicious = False
    reason = ''

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
        user.last_login_ip = ip
        user.save(update_fields=['last_login_ip'])

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
        result=result,
        is_suspicious=is_suspicious,
        suspicion_reason=reason,
        session_key=request.session.session_key or '',
    )

    if is_suspicious and user:
        from notifications.models import Notification, notify
        notify(
            user,
            'Suspicious login detected',
            f'A login from {ip} was flagged: {reason}',
            level=Notification.Level.WARNING,
            category=Notification.Category.SECURITY,
        )
    return entry
