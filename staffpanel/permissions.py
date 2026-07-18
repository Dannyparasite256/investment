"""Staff panel access helpers."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def user_is_staff_panel(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return getattr(user, 'role', '') in ('support', 'manager', 'admin')


def staff_panel_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not user_is_staff_panel(request.user):
            raise PermissionDenied('Staff panel access required')
        return view_func(request, *args, **kwargs)
    return _wrapped


def role_required(*roles):
    def decorator(view_func):
        @staff_panel_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles and not request.user.is_staff:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
