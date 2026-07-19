"""WebSocket consumer for realtime support chat."""
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from support.realtime import (
    clear_presence,
    get_presence,
    get_typing,
    set_presence,
    set_typing,
    staff_support_group,
    ticket_group,
    user_support_group,
)


class SupportChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return
        self.user = user
        self.is_staff = bool(
            getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
            or getattr(user, 'role', '') in ('support', 'manager', 'admin')
        )
        self.ticket_id = None
        self.user_group = user_support_group(user.pk)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        if self.is_staff:
            await self.channel_layer.group_add(staff_support_group(), self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'user_id': user.pk, 'is_staff': self.is_staff})

    async def disconnect(self, close_code):
        if getattr(self, 'ticket_id', None):
            await self._clear_presence()
            await self.channel_layer.group_discard(
                ticket_group(self.ticket_id), self.channel_name,
            )
            self.ticket_id = None
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if getattr(self, 'is_staff', False):
            await self.channel_layer.group_discard(staff_support_group(), self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get('action')
        if action == 'ping':
            await self.send_json({'type': 'pong'})
            return
        if action == 'join':
            await self._join_ticket(content.get('ticket_id'))
            return
        if action == 'leave':
            await self._leave_ticket()
            return
        if action == 'typing':
            if self.ticket_id:
                await self._set_typing(bool(content.get('is_typing', True)))
            return
        if action == 'heartbeat':
            if self.ticket_id:
                await self._heartbeat()
            return
        if action == 'mark_read':
            if self.ticket_id:
                await self._mark_read()
            return

    async def chat_event(self, event):
        await self.send_json(event['payload'])

    async def _join_ticket(self, ticket_id):
        if not ticket_id:
            return
        allowed = await self._can_access(ticket_id)
        if not allowed:
            await self.send_json({'type': 'error', 'detail': 'Forbidden'})
            return
        if self.ticket_id:
            await self.channel_layer.group_discard(
                ticket_group(self.ticket_id), self.channel_name,
            )
        self.ticket_id = str(ticket_id)
        await self.channel_layer.group_add(ticket_group(self.ticket_id), self.channel_name)
        await self._heartbeat()
        await self._mark_read()
        presence = await self._presence()
        typers = await self._typers()
        await self.send_json({
            'type': 'joined',
            'ticket_id': self.ticket_id,
            'presence': presence,
            'typing': typers,
        })

    async def _leave_ticket(self):
        if self.ticket_id:
            await self._clear_presence()
            await self.channel_layer.group_discard(
                ticket_group(self.ticket_id), self.channel_name,
            )
            self.ticket_id = None

    @database_sync_to_async
    def _can_access(self, ticket_id):
        from support.models import SupportTicket
        qs = SupportTicket.objects.filter(pk=ticket_id)
        if self.is_staff:
            return qs.exists()
        return qs.filter(user=self.user).exists()

    @database_sync_to_async
    def _set_typing(self, is_typing: bool):
        set_typing(self.ticket_id, self.user, is_typing=is_typing, is_staff=self.is_staff)

    @database_sync_to_async
    def _heartbeat(self):
        set_presence(self.ticket_id, self.user, is_staff=self.is_staff)

    @database_sync_to_async
    def _clear_presence(self):
        if self.ticket_id:
            clear_presence(self.ticket_id, self.user, is_staff=self.is_staff)

    @database_sync_to_async
    def _presence(self):
        return get_presence(self.ticket_id)

    @database_sync_to_async
    def _typers(self):
        return get_typing(self.ticket_id, exclude_user_id=self.user.pk)

    @database_sync_to_async
    def _mark_read(self):
        from support.models import TicketMessage
        from support.realtime import notify_receipts

        now = timezone.now()
        # Mark messages FROM the other party as delivered + read
        qs = TicketMessage.objects.filter(ticket_id=self.ticket_id)
        if self.is_staff:
            qs = qs.filter(is_staff_reply=False)
        else:
            qs = qs.filter(is_staff_reply=True)
        unread = list(qs.filter(read_at__isnull=True).values_list('id', flat=True))
        undelivered = list(qs.filter(delivered_at__isnull=True).values_list('id', flat=True))
        updated = qs.filter(read_at__isnull=True).update(
            delivered_at=now, read_at=now, updated_at=now,
        )
        # Also mark any delivered but unread
        if undelivered:
            TicketMessage.objects.filter(id__in=undelivered).update(delivered_at=now)
        if updated or unread:
            notify_receipts(self.ticket_id, unread or undelivered, 'read', now.isoformat())
        return updated
