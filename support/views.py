from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from support.models import SupportTicket, TicketMessage


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
            TicketMessage.objects.create(ticket=ticket, sender=request.user, body=body)
            messages.success(request, 'Conversation started.')
            return redirect('support:detail', pk=ticket.pk)
        messages.error(request, 'Subject and message are required.')
    return render(request, 'support/create.html')


@login_required
@require_http_methods(['GET', 'POST'])
def ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket, pk=pk, user=request.user)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            TicketMessage.objects.create(ticket=ticket, sender=request.user, body=body)
            if ticket.status == SupportTicket.Status.WAITING:
                ticket.status = SupportTicket.Status.OPEN
                ticket.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Message sent.')
            return redirect('support:detail', pk=pk)
    other_tickets = (
        SupportTicket.objects.filter(user=request.user)
        .order_by('-updated_at')[:40]
    )
    return render(request, 'support/detail.html', {
        'ticket': ticket,
        'messages_list': ticket.messages.select_related('sender'),
        'other_tickets': other_tickets,
    })
