import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from notifications.models import Notification


def _unread_count(user):
    return user.notifications.filter(is_read=False).count()


def _badges_oob(unread_count):
    return render_to_string(
        'notifications/partials/badges_oob.html',
        {'unread_count': unread_count},
    )


def _htmx_response(html, unread_count, *, refresh=False, redirect_url=None):
    response = HttpResponse(html)
    response['HX-Trigger'] = json.dumps({'notif-updated': {'count': unread_count}})
    if refresh:
        response['HX-Refresh'] = 'true'
    if redirect_url:
        response['HX-Redirect'] = redirect_url
    return response


@login_required
def notification_list(request):
    """List notifications and mark them as viewed when the page is opened."""
    qs = Notification.objects.filter(user=request.user)
    # Opening the notifications page classifies all as viewed
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    # After auto-view, "unread only" would be empty — show full inbox
    unread_only = False
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    unread_count = 0
    return render(request, 'notifications/list.html', {
        'page': page,
        'unread_only': unread_only,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.mark_read()
    unread_count = _unread_count(request.user)

    if request.headers.get('HX-Request'):
        partial = request.headers.get('X-Notif-Partial', '')
        source = request.POST.get('source', '')

        # Dropdown: mark read, then follow deep-link or show read state
        if partial == 'drop' or source == 'dropdown':
            if n.link:
                return _htmx_response(_badges_oob(unread_count), unread_count, redirect_url=n.link)
            html = render_to_string(
                'notifications/partials/drop_item.html',
                {'n': n},
                request=request,
            )
            return _htmx_response(html + _badges_oob(unread_count), unread_count)

        # Full list row swap
        html = render_to_string(
            'notifications/partials/row.html',
            {'n': n},
            request=request,
        )
        return _htmx_response(html + _badges_oob(unread_count), unread_count)

    if n.link:
        return redirect(n.link)
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        partial = request.headers.get('X-Notif-Partial', '')
        # List page: refresh so cards lose unread state
        if partial == 'list-all':
            return _htmx_response(_badges_oob(0), 0, refresh=True)
        # Dropdown open / mark-all: clear badges (keep items visible as read)
        if partial in ('dropdown-open', 'dropdown-all'):
            empty_ui = (
                '<div id="notif-dropdown-head" class="notif-dropdown-head" hx-swap-oob="true">'
                '<div class="notif-dropdown-head-left">'
                '<span class="notif-dropdown-title">Notifications</span>'
                '</div></div>'
            )
            return _htmx_response(_badges_oob(0) + empty_ui, 0)
        # Legacy full clear of dropdown body
        empty_ui = (
            '<div id="notif-dropdown-head" class="notif-dropdown-head" hx-swap-oob="true">'
            '<div class="notif-dropdown-head-left">'
            '<span class="notif-dropdown-title">Notifications</span>'
            '</div></div>'
            '<div id="notif-dropdown-body" hx-swap-oob="innerHTML">'
            '<div class="notif-drop-empty">'
            '<div class="notif-drop-empty-icon"><i class="bi bi-bell-slash"></i></div>'
            '<div class="notif-drop-empty-title">You\'re all caught up</div>'
            '<div class="small text-muted">New alerts will show up here</div>'
            '</div></div>'
        )
        return _htmx_response(_badges_oob(0) + empty_ui, 0)
    return redirect('notifications:list')
