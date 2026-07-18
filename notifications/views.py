from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import Notification


@login_required
def notification_list(request):
    qs = Notification.objects.filter(user=request.user)
    unread_only = request.GET.get('unread') == '1'
    if unread_only:
        qs = qs.filter(is_read=False)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'notifications/list.html', {'page': page, 'unread_only': unread_only})


@login_required
@require_POST
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.mark_read()
    if request.headers.get('HX-Request'):
        return HttpResponse(status=204)
    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('HX-Request'):
        return render(request, 'notifications/partials/badge.html', {'unread_count': 0})
    return redirect('notifications:list')
