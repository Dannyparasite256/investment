"""WebSocket consumer for real-time notifications."""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if user is None or user.is_anonymous:
            await self.close()
            return
        self.group_name = f'user_{user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        # Send unread count on connect
        count = await self._unread_count(user)
        await self.send_json({'type': 'connected', 'unread': count})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        action = content.get('action')
        if action == 'ping':
            await self.send_json({'type': 'pong'})
        elif action == 'mark_read' and content.get('id'):
            await self._mark_read(self.scope['user'], content['id'])
            await self.send_json({'type': 'marked_read', 'id': content['id']})

    async def notify_message(self, event):
        await self.send_json({'type': 'notification', 'data': event['payload']})

    @database_sync_to_async
    def _unread_count(self, user):
        return user.notifications.filter(is_read=False).count()

    @database_sync_to_async
    def _mark_read(self, user, notif_id):
        user.notifications.filter(pk=notif_id).update(is_read=True)
