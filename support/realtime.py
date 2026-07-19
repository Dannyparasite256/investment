"""Realtime helpers for support chat: typing, presence, channel broadcasts.

Typing/presence are stored on SupportTicket in the database so they work
across multiple web workers without Redis (e.g. PythonAnywhere).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

# Short TTL so sticky typing cannot linger when stop events are missed
TYPING_TTL = 3
PRESENCE_TTL = 45


def ticket_group(ticket_id) -> str:
    return f'support_ticket_{ticket_id}'


def user_support_group(user_id) -> str:
    return f'support_user_{user_id}'


def staff_support_group() -> str:
    return 'support_staff'


def _ticket(ticket_id):
    from support.models import SupportTicket
    return (
        SupportTicket.objects
        .select_related('user', 'assigned_to')
        .filter(pk=ticket_id)
        .first()
    )


def _is_fresh(dt, seconds: int) -> bool:
    if not dt:
        return False
    return dt >= timezone.now() - timedelta(seconds=seconds)


def set_typing(ticket_id, user, *, is_typing: bool, is_staff: bool = False) -> None:
    from support.models import SupportTicket

    # Coerce so "false"/0 never sticky-true
    is_typing = bool(is_typing) if not isinstance(is_typing, str) else str(is_typing).strip().lower() in (
        '1', 'true', 'yes', 'on',
    )

    field = 'staff_typing_at' if is_staff else 'user_typing_at'
    value = timezone.now() if is_typing else None
    updates = {field: value}
    if is_staff and is_typing:
        # Keep presence fresh while typing so "online" also shows
        updates['staff_last_seen_at'] = timezone.now()
        SupportTicket.objects.filter(pk=ticket_id, assigned_to__isnull=True).update(assigned_to=user)
    elif not is_staff and is_typing:
        updates['user_last_seen_at'] = timezone.now()
    SupportTicket.objects.filter(pk=ticket_id).update(**updates)

    name = user.get_full_name() or user.email
    broadcast_ticket(ticket_id, {
        'type': 'typing',
        'ticket_id': str(ticket_id),
        'user_id': user.pk,
        'name': name if not is_staff else 'Support',
        'is_staff': is_staff,
        'is_typing': bool(is_typing),
    })


def get_typing(ticket_id, exclude_user_id=None) -> list[dict]:
    """
    Return active typers for a ticket (DB-backed, multi-worker safe).

    exclude_user_id = the viewer:
      - ticket owner → see staff typing only
      - anyone else (staff) → see customer typing only
    """
    t = _ticket(ticket_id)
    if not t:
        return []

    out: list[dict] = []
    viewer_is_customer = exclude_user_id is not None and exclude_user_id == t.user_id

    if _is_fresh(t.user_typing_at, TYPING_TTL) and not viewer_is_customer:
        # Staff (or unknown viewer) sees customer typing
        if exclude_user_id is None or exclude_user_id != t.user_id:
            u = t.user
            out.append({
                'user_id': u.pk,
                'name': u.get_full_name() or u.email,
                'is_staff': False,
                'at': t.user_typing_at.isoformat() if t.user_typing_at else None,
            })

    if _is_fresh(t.staff_typing_at, TYPING_TTL) and (viewer_is_customer or exclude_user_id is None):
        # Customer sees support typing
        name = 'Support'
        if t.assigned_to_id:
            name = t.assigned_to.get_full_name() or t.assigned_to.email or 'Support'
        out.append({
            'user_id': t.assigned_to_id or 0,
            'name': name,
            'is_staff': True,
            'at': t.staff_typing_at.isoformat() if t.staff_typing_at else None,
        })

    return out


def set_presence(ticket_id, user, *, is_staff: bool = False) -> None:
    """Mark side as online / in this chat (also refreshes last seen)."""
    from support.models import SupportTicket

    now = timezone.now()
    if is_staff:
        SupportTicket.objects.filter(pk=ticket_id).update(
            staff_last_seen_at=now,
            staff_in_chat=True,
        )
        SupportTicket.objects.filter(pk=ticket_id, assigned_to__isnull=True).update(assigned_to=user)
    else:
        SupportTicket.objects.filter(pk=ticket_id).update(
            user_last_seen_at=now,
            user_in_chat=True,
        )

    broadcast_ticket(ticket_id, {
        'type': 'presence',
        'ticket_id': str(ticket_id),
        'role': 'staff' if is_staff else 'user',
        'user_id': user.pk,
        'name': user.get_full_name() or user.email,
        'online': True,
        'at': now.isoformat(),
    })


def clear_presence(ticket_id, user, *, is_staff: bool = False) -> None:
    """
    Leave chat immediately: offline for the other party, last seen = now,
    clear typing for this side.
    """
    from support.models import SupportTicket

    now = timezone.now()
    if is_staff:
        SupportTicket.objects.filter(pk=ticket_id).update(
            staff_last_seen_at=now,
            staff_in_chat=False,
            staff_typing_at=None,
        )
    else:
        SupportTicket.objects.filter(pk=ticket_id).update(
            user_last_seen_at=now,
            user_in_chat=False,
            user_typing_at=None,
        )

    broadcast_ticket(ticket_id, {
        'type': 'presence',
        'ticket_id': str(ticket_id),
        'role': 'staff' if is_staff else 'user',
        'user_id': getattr(user, 'pk', None),
        'name': (user.get_full_name() or user.email) if user else '',
        'online': False,
        'at': now.isoformat(),
    })


def get_presence(ticket_id) -> dict[str, Any]:
    t = _ticket(ticket_id)
    if not t:
        return {
            'user_online': False,
            'staff_online': False,
            'user_name': '',
            'staff_name': 'Support',
            'user_last_seen': None,
            'staff_last_seen': None,
        }
    staff_name = 'Support'
    if t.assigned_to_id:
        staff_name = t.assigned_to.get_full_name() or t.assigned_to.email or 'Support'

    # Online only while actively in chat; last_seen always available for offline label
    user_online = bool(getattr(t, 'user_in_chat', False)) and _is_fresh(t.user_last_seen_at, PRESENCE_TTL)
    staff_online = bool(getattr(t, 'staff_in_chat', False)) and _is_fresh(t.staff_last_seen_at, PRESENCE_TTL)

    return {
        'user_online': user_online,
        'staff_online': staff_online,
        'user_name': t.user.get_full_name() or t.user.email,
        'staff_name': staff_name,
        'user_last_seen': t.user_last_seen_at.isoformat() if t.user_last_seen_at else None,
        'staff_last_seen': t.staff_last_seen_at.isoformat() if t.staff_last_seen_at else None,
    }




def broadcast_ticket(ticket_id, payload: dict) -> None:
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)(
            ticket_group(ticket_id),
            {'type': 'chat.event', 'payload': payload},
        )
    except Exception:
        pass


def broadcast_user(user_id, payload: dict) -> None:
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)(
            user_support_group(user_id),
            {'type': 'chat.event', 'payload': payload},
        )
    except Exception:
        pass


def broadcast_staff(payload: dict) -> None:
    layer = get_channel_layer()
    if not layer:
        return
    try:
        async_to_sync(layer.group_send)(
            staff_support_group(),
            {'type': 'chat.event', 'payload': payload},
        )
    except Exception:
        pass


def _reply_preview(msg) -> dict | None:
    parent = getattr(msg, 'reply_to', None)
    if not parent:
        return None
    sender = parent.sender
    name = f'{sender.first_name} {sender.last_name}'.strip() or sender.email
    body = parent.body or ''
    if body == '(attachment)':
        body = '📎 Attachment'
    return {
        'id': str(parent.id),
        'body': body[:200],
        'is_staff_reply': parent.is_staff_reply,
        'sender_name': name,
    }


def message_payload(msg) -> dict:
    sender = msg.sender
    name = f'{sender.first_name} {sender.last_name}'.strip() or sender.email
    att_url = ''
    if getattr(msg, 'attachment', None):
        try:
            att_url = msg.attachment.url
        except Exception:
            att_url = ''
    body = msg.body
    if getattr(msg, 'is_deleted', False):
        body = '🚫 This message was deleted'
    return {
        'id': str(msg.id),
        'ticket_id': str(msg.ticket_id),
        'body': body,
        'is_staff_reply': msg.is_staff_reply,
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
        'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
        'read_at': msg.read_at.isoformat() if msg.read_at else None,
        'receipt_status': msg.receipt_status,
        'sender': sender.pk,
        'sender_name': name,
        'attachment_url': att_url,
        'reply_to_id': str(msg.reply_to_id) if getattr(msg, 'reply_to_id', None) else None,
        'reply_to': _reply_preview(msg),
        'is_starred': bool(getattr(msg, 'is_starred', False)),
        'is_pinned': bool(getattr(msg, 'is_pinned', False)),
        'edited_at': msg.edited_at.isoformat() if getattr(msg, 'edited_at', None) else None,
        'is_deleted': bool(getattr(msg, 'is_deleted', False)),
        'is_voice': bool(getattr(msg, 'is_voice', False)),
        'is_forwarded': bool(getattr(msg, 'is_forwarded', False)),
        'forwarded_from_id': str(msg.forwarded_from_id) if getattr(msg, 'forwarded_from_id', None) else None,
        'mentioned_user_ids': list(getattr(msg, 'mentioned_user_ids', None) or []),
    }


def _preview_body(msg, max_len: int = 140) -> str:
    body = (getattr(msg, 'body', None) or '').strip()
    if not body or body == '(attachment)':
        if getattr(msg, 'attachment', None):
            return '📎 Attachment'
        return 'New message'
    body = ' '.join(body.split())
    if len(body) > max_len:
        return body[: max_len - 1] + '…'
    return body


def _staff_notification_recipients(ticket, exclude_user_id=None):
    """Assigned agent if set; otherwise all staff-panel users."""
    from django.contrib.auth import get_user_model
    from django.db.models import Q

    User = get_user_model()
    if ticket.assigned_to_id and ticket.assigned_to_id != exclude_user_id:
        u = User.objects.filter(pk=ticket.assigned_to_id, is_active=True).first()
        return [u] if u else []

    qs = User.objects.filter(is_active=True).filter(
        Q(is_staff=True)
        | Q(is_superuser=True)
        | Q(role__in=['support', 'manager', 'admin']),
    )
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    return list(qs[:40])


def notify_chat_parties(ticket, msg) -> None:
    """
    In-app (+ optional browser push) when support or customer sends a message.
    - Staff reply → notify the ticket customer (unless muted)
    - Customer message / new ticket → notify assigned agent or all staff
    """
    from notifications.models import Notification, notify

    preview = _preview_body(msg)
    tid = str(ticket.id)

    if msg.is_staff_reply:
        if getattr(ticket, 'muted_by_user', False):
            return
        if ticket.user_id and ticket.user_id != msg.sender_id:
            notify(
                ticket.user,
                'Support replied',
                preview if preview else f'Re: {ticket.subject}',
                level=Notification.Level.INFO,
                category=Notification.Category.SUPPORT,
                link=f'/app/support/{tid}',
                ticket_id=tid,
                message_id=str(msg.id),
            )
        return

    if getattr(ticket, 'muted_by_staff', False):
        return

    # Customer → staff
    who = ''
    try:
        who = ticket.user.get_full_name() or ticket.user.email
    except Exception:
        who = 'Customer'
    title = f'New support message · {ticket.subject[:60]}'
    body = f'{who}: {preview}'
    link = f'/app/admin/tickets/{tid}'
    for agent in _staff_notification_recipients(ticket, exclude_user_id=msg.sender_id):
        notify(
            agent,
            title,
            body,
            level=Notification.Level.INFO,
            category=Notification.Category.SUPPORT,
            link=link,
            ticket_id=tid,
            message_id=str(msg.id),
        )


def notify_new_message(ticket, msg) -> None:
    from support.models import SupportTicket
    from support.services import maybe_email_support_message, on_message_created

    # SLA / assign / instant delivered
    try:
        on_message_created(ticket, msg)
        msg.refresh_from_db()
        ticket.refresh_from_db()
    except Exception:
        import logging
        logging.getLogger('support').exception('on_message_created failed')

    # Clear typing for the sender side when they send
    if msg.is_staff_reply:
        SupportTicket.objects.filter(pk=ticket.pk).update(staff_typing_at=None)
    else:
        SupportTicket.objects.filter(pk=ticket.pk).update(user_typing_at=None)

    # Explicit typing-stop so peer UI does not stick after a message
    broadcast_ticket(ticket.id, {
        'type': 'typing',
        'ticket_id': str(ticket.id),
        'user_id': msg.sender_id,
        'name': 'Support' if msg.is_staff_reply else (msg.sender.get_full_name() or msg.sender.email),
        'is_staff': bool(msg.is_staff_reply),
        'is_typing': False,
    })

    payload = {
        'type': 'message',
        'ticket_id': str(ticket.id),
        'message': message_payload(msg),
    }
    broadcast_ticket(ticket.id, payload)
    broadcast_user(ticket.user_id, payload)
    broadcast_staff(payload)

    # Bell + browser push for the other party
    try:
        notify_chat_parties(ticket, msg)
    except Exception:
        import logging
        logging.getLogger('support').exception('notify_chat_parties failed')

    try:
        maybe_email_support_message(ticket, msg)
    except Exception:
        import logging
        logging.getLogger('support').exception('email support message failed')


def notify_receipts(ticket_id, message_ids: list, status: str, at_iso: str) -> None:
    payload = {
        'type': 'receipts',
        'ticket_id': str(ticket_id),
        'message_ids': [str(i) for i in message_ids],
        'status': status,
        'at': at_iso,
    }
    broadcast_ticket(ticket_id, payload)


def as_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')
