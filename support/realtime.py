"""Realtime helpers for support chat: typing, presence, channel broadcasts."""
from __future__ import annotations

from typing import Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils import timezone

TYPING_TTL = 5
PRESENCE_TTL = 45


def ticket_group(ticket_id) -> str:
    return f'support_ticket_{ticket_id}'


def user_support_group(user_id) -> str:
    return f'support_user_{user_id}'


def staff_support_group() -> str:
    return 'support_staff'


def _typing_key(ticket_id, user_id) -> str:
    return f'chat:typing:{ticket_id}:{user_id}'


def _presence_key(ticket_id, role: str) -> str:
    return f'chat:presence:{ticket_id}:{role}'


def set_typing(ticket_id, user, *, is_typing: bool, is_staff: bool = False) -> None:
    key = _typing_key(ticket_id, user.pk)
    if is_typing:
        cache.set(
            key,
            {
                'user_id': user.pk,
                'name': user.get_full_name() or user.email,
                'is_staff': is_staff,
                'at': timezone.now().isoformat(),
            },
            TYPING_TTL,
        )
    else:
        cache.delete(key)
    broadcast_ticket(ticket_id, {
        'type': 'typing',
        'ticket_id': str(ticket_id),
        'user_id': user.pk,
        'name': user.get_full_name() or user.email,
        'is_staff': is_staff,
        'is_typing': is_typing,
    })


def get_typing(ticket_id, exclude_user_id=None) -> list[dict]:
    """Return active typers for a ticket (best-effort; scans known participants via presence)."""
    typers = []
    # Presence keys tell us who is active; also probe last known user/staff roles
    for role in ('user', 'staff'):
        presence = cache.get(_presence_key(ticket_id, role)) or {}
        uid = presence.get('user_id')
        if not uid or uid == exclude_user_id:
            continue
        data = cache.get(_typing_key(ticket_id, uid))
        if data:
            typers.append(data)
    return typers


def set_presence(ticket_id, user, *, is_staff: bool = False) -> None:
    role = 'staff' if is_staff else 'user'
    cache.set(
        _presence_key(ticket_id, role),
        {
            'user_id': user.pk,
            'name': user.get_full_name() or user.email,
            'is_staff': is_staff,
            'at': timezone.now().isoformat(),
            'online': True,
        },
        PRESENCE_TTL,
    )
    broadcast_ticket(ticket_id, {
        'type': 'presence',
        'ticket_id': str(ticket_id),
        'role': role,
        'user_id': user.pk,
        'name': user.get_full_name() or user.email,
        'online': True,
        'at': timezone.now().isoformat(),
    })


def get_presence(ticket_id) -> dict[str, Any]:
    user_p = cache.get(_presence_key(ticket_id, 'user')) or {}
    staff_p = cache.get(_presence_key(ticket_id, 'staff')) or {}
    return {
        'user_online': bool(user_p.get('online')),
        'staff_online': bool(staff_p.get('online')),
        'user_name': user_p.get('name') or '',
        'staff_name': staff_p.get('name') or 'Support',
        'user_last_seen': user_p.get('at'),
        'staff_last_seen': staff_p.get('at'),
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
        'status': status,  # delivered | read
        'at': at_iso,
    }
    broadcast_ticket(ticket_id, payload)
