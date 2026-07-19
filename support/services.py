"""Support chat business logic: receipts, SLA, auto-assign, email."""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone


def default_sla_hours() -> int:
    try:
        from core.models import SiteConfiguration
        cfg = SiteConfiguration.get_solo()
        return int(getattr(cfg, 'support_sla_hours', None) or 24)
    except Exception:
        return 24


def set_sla_on_open(ticket) -> None:
    if ticket.sla_due_at:
        return
    hours = default_sla_hours()
    ticket.sla_due_at = timezone.now() + timedelta(hours=hours)
    ticket.save(update_fields=['sla_due_at', 'updated_at'])


def auto_assign_agent(ticket, preferred_user=None) -> None:
    """Round-robin / preferred assign when unassigned."""
    if ticket.assigned_to_id:
        return
    from django.contrib.auth import get_user_model

    User = get_user_model()
    if preferred_user and getattr(preferred_user, 'pk', None):
        if preferred_user.is_staff or preferred_user.is_superuser or getattr(preferred_user, 'role', '') in (
            'support', 'manager', 'admin',
        ):
            ticket.assigned_to = preferred_user
            ticket.save(update_fields=['assigned_to', 'updated_at'])
            return

    agents = list(
        User.objects.filter(is_active=True)
        .filter(Q(is_staff=True) | Q(is_superuser=True) | Q(role__in=['support', 'manager', 'admin']))
        .order_by('id')[:50]
    )
    if not agents:
        return
    # Simple round-robin by open ticket load
    from support.models import SupportTicket

    best = None
    best_n = 10**9
    for a in agents:
        n = SupportTicket.objects.filter(
            assigned_to=a,
            status__in=['open', 'in_progress', 'waiting'],
        ).count()
        if n < best_n:
            best_n = n
            best = a
    if best:
        ticket.assigned_to = best
        ticket.save(update_fields=['assigned_to', 'updated_at'])


def mark_messages_delivered(ticket, *, for_staff_messages: bool) -> list:
    """
    Double grey ticks: peer got the messages (online/list/poll) without opening read.
    for_staff_messages=True → customer is online, mark staff replies delivered
    for_staff_messages=False → staff is online, mark customer messages delivered
    """
    from support.models import TicketMessage
    from support.realtime import notify_receipts

    now = timezone.now()
    qs = TicketMessage.objects.filter(
        ticket=ticket,
        delivered_at__isnull=True,
        is_deleted=False,
    )
    if for_staff_messages:
        qs = qs.filter(is_staff_reply=True)
    else:
        qs = qs.filter(is_staff_reply=False)
    ids = list(qs.values_list('id', flat=True))
    if not ids:
        return []
    qs.update(delivered_at=now, updated_at=now)
    notify_receipts(ticket.id, ids, 'delivered', now.isoformat())
    return ids


def mark_messages_read(ticket, *, peer_is_staff_replies: bool) -> list:
    """Blue ticks: viewer opened the chat."""
    from support.models import TicketMessage
    from support.realtime import notify_receipts

    now = timezone.now()
    qs = TicketMessage.objects.filter(ticket=ticket, read_at__isnull=True, is_deleted=False)
    if peer_is_staff_replies:
        qs = qs.filter(is_staff_reply=True)
    else:
        qs = qs.filter(is_staff_reply=False)
    ids = list(qs.values_list('id', flat=True))
    if not ids:
        return []
    qs.update(delivered_at=now, read_at=now, updated_at=now)
    notify_receipts(ticket.id, ids, 'read', now.isoformat())
    return ids


def on_message_created(ticket, msg) -> None:
    """Post-create hooks: SLA, assign, first response, try instant delivered."""
    from support.models import SupportTicket
    from support.realtime import _is_fresh, PRESENCE_TTL

    # SLA clock starts when customer opens / first customer msg
    if not msg.is_staff_reply:
        if not ticket.sla_due_at:
            set_sla_on_open(ticket)
        auto_assign_agent(ticket)
    else:
        # First staff response
        if not ticket.first_response_at:
            SupportTicket.objects.filter(pk=ticket.pk, first_response_at__isnull=True).update(
                first_response_at=timezone.now(),
            )
        if not ticket.assigned_to_id:
            auto_assign_agent(ticket, preferred_user=msg.sender)

    # Instant delivered if peer currently online/in chat
    ticket.refresh_from_db()
    now = timezone.now()
    if msg.is_staff_reply:
        peer_online = ticket.user_in_chat or _is_fresh(ticket.user_last_seen_at, PRESENCE_TTL)
        if peer_online and not msg.delivered_at:
            msg.delivered_at = now
            msg.save(update_fields=['delivered_at', 'updated_at'])
    else:
        peer_online = ticket.staff_in_chat or _is_fresh(ticket.staff_last_seen_at, PRESENCE_TTL)
        if peer_online and not msg.delivered_at:
            msg.delivered_at = now
            msg.save(update_fields=['delivered_at', 'updated_at'])


def maybe_email_support_message(ticket, msg) -> None:
    """Email customer when staff replies (if email_alerts and not muted)."""
    if not msg.is_staff_reply:
        return
    if ticket.muted_by_user:
        return
    user = ticket.user
    if not getattr(user, 'email_alerts', True):
        return
    email = getattr(user, 'email', None)
    if not email:
        return
    preview = (msg.body or '').strip()
    if not preview or preview == '(attachment)':
        preview = 'You have a new attachment from support.'
    preview = ' '.join(preview.split())[:200]
    subject = f'Support reply: {ticket.subject[:80]}'
    body = (
        f'Hello,\n\nSupport replied on your ticket "{ticket.subject}":\n\n'
        f'{preview}\n\n'
        f'Open chat: {getattr(settings, "SITE_URL", "")}/app/support/{ticket.id}\n'
    )
    try:
        send_mail(
            subject,
            body,
            getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@localhost',
            [email],
            fail_silently=True,
        )
    except Exception:
        pass


def last_message_dict(msg) -> dict | None:
    if not msg:
        return None
    body = msg.display_body if hasattr(msg, 'display_body') else (msg.body or '')
    if getattr(msg, 'is_deleted', False):
        body = '🚫 This message was deleted'
    elif getattr(msg, 'is_voice', False):
        body = '🎤 Voice message'
    elif body == '(attachment)':
        body = '📎 Attachment'
    has_att = bool(getattr(msg, 'attachment', None))
    return {
        'id': str(msg.id),
        'body': body[:200],
        'is_staff_reply': msg.is_staff_reply,
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
        'receipt_status': msg.receipt_status,
        'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
        'read_at': msg.read_at.isoformat() if msg.read_at else None,
        'has_attachment': has_att,
        'is_deleted': bool(getattr(msg, 'is_deleted', False)),
        'is_voice': bool(getattr(msg, 'is_voice', False)),
        'is_forwarded': bool(getattr(msg, 'is_forwarded', False)),
    }


def is_voice_file(file_obj) -> bool:
    if not file_obj:
        return False
    name = (getattr(file_obj, 'name', '') or '').lower()
    ctype = (getattr(file_obj, 'content_type', '') or '').lower()
    if ctype.startswith('audio/'):
        return True
    return any(name.endswith(ext) for ext in ('.webm', '.ogg', '.mp3', '.m4a', '.wav', '.aac', '.opus'))


def parse_mention_handles(body: str) -> list[str]:
    """Extract @handles from message body (email local-part or first name)."""
    import re
    if not body:
        return []
    return list({m.group(1).lower() for m in re.finditer(r'@([A-Za-z0-9._+-]{2,40})', body)})


def resolve_staff_mentions(body: str, exclude_user_id=None) -> list:
    """Match @handles against staff-panel users (email local-part or first name)."""
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    handles = parse_mention_handles(body)
    if not handles:
        return []
    User = get_user_model()
    qs = User.objects.filter(is_active=True).filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(role__in=['support', 'manager', 'admin']),
    )
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    found = []
    for u in qs[:100]:
        local = (u.email or '').split('@')[0].lower()
        first = (u.first_name or '').strip().lower()
        full = (u.get_full_name() or '').replace(' ', '').lower()
        for h in handles:
            if h == local or h == first or h == full or h in local:
                found.append(u)
                break
    # unique by pk
    by_id = {u.pk: u for u in found}
    return list(by_id.values())


def notify_mentioned_staff(ticket, msg, mentioned_users) -> None:
    from notifications.models import Notification, notify

    if not mentioned_users:
        return
    preview = (msg.body or '')[:140]
    for u in mentioned_users:
        if u.pk == msg.sender_id:
            continue
        notify(
            u,
            f'You were mentioned · {ticket.subject[:50]}',
            preview or 'Mentioned in support chat',
            level=Notification.Level.INFO,
            category=Notification.Category.SUPPORT,
            link=f'/app/admin/tickets/{ticket.id}',
            ticket_id=str(ticket.id),
            message_id=str(msg.id),
            mention=True,
        )


def forward_message(*, source_msg, target_ticket, sender, is_staff_reply: bool):
    """Create a forwarded copy of source_msg on target_ticket."""
    from support.models import TicketMessage
    from support.realtime import notify_new_message

    body = source_msg.body or ''
    if source_msg.is_deleted:
        body = '(deleted message)'
    elif source_msg.is_voice:
        body = '🎤 Forwarded voice message'
    elif body == '(attachment)' or source_msg.attachment:
        body = f'📎 Forwarded attachment\n{body}' if body and body != '(attachment)' else '📎 Forwarded attachment'
    prefix = '↪️ Forwarded message:\n'
    msg = TicketMessage.objects.create(
        ticket=target_ticket,
        sender=sender,
        body=prefix + (body[:1800] if body else '(empty)'),
        is_staff_reply=is_staff_reply,
        is_forwarded=True,
        forwarded_from=source_msg,
        reply_to=None,
    )
    # Copy file if present (reference same file path carefully — re-save content)
    if source_msg.attachment and not source_msg.is_deleted:
        try:
            src = source_msg.attachment
            src.open('rb')
            from django.core.files.base import ContentFile
            content = src.read()
            src.close()
            name = src.name.split('/')[-1]
            msg.attachment.save(name, ContentFile(content), save=True)
            if source_msg.is_voice:
                msg.is_voice = True
                msg.save(update_fields=['is_voice', 'updated_at'])
        except Exception:
            pass
    if is_staff_reply:
        target_ticket.status = target_ticket.Status.WAITING
        target_ticket.save(update_fields=['status', 'updated_at'])
    else:
        target_ticket.save(update_fields=['updated_at'])
    notify_new_message(target_ticket, msg)
    return msg


def maybe_notify_vip_upgrade(user) -> None:
    """If user reached a higher VIP tier than last notified, send VIP toast notification."""
    from core.vip import get_user_tier
    from notifications.models import Notification, notify

    tier = get_user_tier(user)
    if not tier:
        return
    slug = (getattr(tier, 'slug', None) or getattr(tier, 'name', '') or '').strip().lower()
    if not slug:
        return
    prev = (getattr(user, 'last_vip_tier_slug', None) or '').strip().lower()
    if prev == slug:
        return
    # Only notify on upgrade (higher min_total_invested)
    upgraded = True
    if prev:
        from core.platform_models import VIPTier
        old = VIPTier.objects.filter(slug=prev).first() or VIPTier.objects.filter(name__icontains=prev).first()
        if old and tier.min_total_invested <= old.min_total_invested:
            upgraded = False
    if not upgraded and prev:
        # still update slug if same/down without toast
        type(user).objects.filter(pk=user.pk).update(last_vip_tier_slug=slug)
        return
    name = getattr(tier, 'name', None) or slug.title()
    notify(
        user,
        f'VIP upgraded · {name}',
        f'Congratulations! You reached {name}. Enjoy your new benefits.',
        level=Notification.Level.SUCCESS,
        category=Notification.Category.VIP,
        link='/app/vip',
    )
    type(user).objects.filter(pk=user.pk).update(last_vip_tier_slug=slug)
