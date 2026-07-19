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

TYPING_TTL = 6
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
        'is_typing': is_typing,
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


def message_payload(msg) -> dict:
    sender = msg.sender
    name = f'{sender.first_name} {sender.last_name}'.strip() or sender.email
    return {
        'id': str(msg.id),
        'ticket_id': str(msg.ticket_id),
        'body': msg.body,
        'is_staff_reply': msg.is_staff_reply,
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
        'delivered_at': msg.delivered_at.isoformat() if msg.delivered_at else None,
        'read_at': msg.read_at.isoformat() if msg.read_at else None,
        'receipt_status': msg.receipt_status,
        'sender': sender.pk,
        'sender_name': name,
    }


def notify_new_message(ticket, msg) -> None:
    from support.models import SupportTicket

    # Clear typing for the sender side when they send
    if msg.is_staff_reply:
        SupportTicket.objects.filter(pk=ticket.pk).update(staff_typing_at=None)
    else:
        SupportTicket.objects.filter(pk=ticket.pk).update(user_typing_at=None)

    payload = {
        'type': 'message',
        'ticket_id': str(ticket.id),
        'message': message_payload(msg),
    }
    broadcast_ticket(ticket.id, payload)
    broadcast_user(ticket.user_id, payload)
    broadcast_staff(payload)


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
