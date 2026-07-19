from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from support.models import SupportTicket, TicketMessage
from support.realtime import (
    clear_presence,
    get_presence,
    get_typing,
    notify_new_message,
    notify_receipts,
    set_presence,
    set_typing,
)


def _mark_staff_messages_read(ticket, user):
    now = timezone.now()
    qs = TicketMessage.objects.filter(ticket=ticket, is_staff_reply=True, read_at__isnull=True)
    ids = list(qs.values_list('id', flat=True))
    if not ids:
        return 0
    n = qs.update(delivered_at=now, read_at=now, updated_at=now)
    notify_receipts(ticket.id, ids, 'read', now.isoformat())
    return n


@login_required
def ticket_list(request):
    qs = SupportTicket.objects.filter(user=request.user).prefetch_related('messages')
    page = Paginator(qs, 30).get_page(request.GET.get('page'))
    return render(request, 'support/list.html', {'page': page})


@login_required
@require_http_methods(['GET', 'POST'])
def ticket_create(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        category = request.POST.get('category', 'general')
        if subject and body:
            ticket = SupportTicket.objects.create(
                user=request.user, subject=subject, category=category,
            )
            msg = TicketMessage.objects.create(ticket=ticket, sender=request.user, body=body)
            notify_new_message(ticket, msg)
            messages.success(request, 'Conversation started.')
            return redirect('support:detail', pk=ticket.pk)
        messages.error(request, 'Subject and message are required.')
    return render(request, 'support/create.html')


def _msg_json(m):
    return {
        'id': str(m.id),
        'body': m.body,
        'is_staff_reply': m.is_staff_reply,
        'created_at': m.created_at.isoformat() if m.created_at else None,
        'delivered_at': m.delivered_at.isoformat() if m.delivered_at else None,
        'read_at': m.read_at.isoformat() if m.read_at else None,
        'receipt_status': m.receipt_status,
        'sender_name': m.sender.get_full_name() or m.sender.email,
    }


@login_required
@require_http_methods(['GET', 'POST'])
def ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        wants_json = (
            request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            or 'application/json' in (request.headers.get('Accept') or '')
        )
        if not body:
            if wants_json:
                return JsonResponse({'detail': 'Message required'}, status=400)
            messages.error(request, 'Message required.')
            return redirect('support:detail', pk=pk)
        if ticket.status in (SupportTicket.Status.CLOSED, SupportTicket.Status.RESOLVED):
            if wants_json:
                return JsonResponse({'detail': 'Conversation closed'}, status=400)
            return redirect('support:detail', pk=pk)
        msg = TicketMessage.objects.create(ticket=ticket, sender=request.user, body=body)
        if ticket.status == SupportTicket.Status.WAITING:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save(update_fields=['status', 'updated_at'])
        else:
            ticket.save(update_fields=['updated_at'])
        notify_new_message(ticket, msg)
        if wants_json:
            return JsonResponse({'ok': True, 'message': _msg_json(msg)})
        messages.success(request, 'Message sent.')
        return redirect('support:detail', pk=pk)
    set_presence(ticket.id, request.user, is_staff=False)
    _mark_staff_messages_read(ticket, request.user)
    other_tickets = (
        SupportTicket.objects.filter(user=request.user)
        .order_by('-updated_at')[:40]
    )
    return render(request, 'support/detail.html', {
        'ticket': ticket,
        'messages_list': ticket.messages.select_related('sender'),
        'other_tickets': other_tickets,
        'presence': get_presence(ticket.id),
        'typing': get_typing(ticket.id, exclude_user_id=request.user.pk),
    })


@login_required
@require_POST
def ticket_typing(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    is_typing = request.POST.get('is_typing', '1') in ('1', 'true', 'True', 'yes')
    set_typing(ticket.id, request.user, is_typing=is_typing, is_staff=False)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def ticket_leave(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    clear_presence(ticket.id, request.user, is_staff=False)
    return JsonResponse({'ok': True, 'presence': get_presence(ticket.id)})


@login_required
@require_http_methods(['GET'])
def ticket_poll(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    set_presence(ticket.id, request.user, is_staff=False)
    _mark_staff_messages_read(ticket, request.user)
    since = request.GET.get('since')
    qs = ticket.messages.select_related('sender').all()
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if timezone.is_naive(since_dt):
                since_dt = timezone.make_aware(since_dt, timezone.get_current_timezone())
            qs = qs.filter(created_at__gt=since_dt)
        except (ValueError, TypeError):
            pass
    data = []
    for m in qs:
        data.append({
            'id': str(m.id),
            'body': m.body,
            'is_staff_reply': m.is_staff_reply,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'delivered_at': m.delivered_at.isoformat() if m.delivered_at else None,
            'read_at': m.read_at.isoformat() if m.read_at else None,
            'receipt_status': m.receipt_status,
            'sender_name': m.sender.get_full_name() or m.sender.email,
        })
    own = []
    for m in ticket.messages.filter(is_staff_reply=False):
        own.append({
            'id': str(m.id),
            'receipt_status': m.receipt_status,
            'delivered_at': m.delivered_at.isoformat() if m.delivered_at else None,
            'read_at': m.read_at.isoformat() if m.read_at else None,
        })
    return JsonResponse({
        'messages': data,
        'receipts': own,
        'typing': get_typing(ticket.id, exclude_user_id=request.user.pk),
        'presence': get_presence(ticket.id),
        'server_time': timezone.now().isoformat(),
    })
