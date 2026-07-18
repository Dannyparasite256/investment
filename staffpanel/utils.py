"""Staff panel utilities."""
from accounts.security_models import AdminActivityLog
from core.utils import get_client_ip


def log_admin_activity(request, action, message='', target_type='', target_id='', extra=None):
    return AdminActivityLog.objects.create(
        admin=request.user if request.user.is_authenticated else None,
        action=action,
        message=message,
        target_type=target_type,
        target_id=str(target_id) if target_id else '',
        ip_address=get_client_ip(request),
        extra=extra or {},
    )
