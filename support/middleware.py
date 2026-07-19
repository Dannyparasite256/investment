"""WebSocket auth: session (default) or ?token= for SPA TokenAuthentication."""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token_key: str):
    from rest_framework.authtoken.models import Token
    try:
        return Token.objects.select_related('user').get(key=token_key).user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if scope.get('type') == 'websocket':
            user = scope.get('user')
            if user is None or user.is_anonymous:
                qs = parse_qs(scope.get('query_string', b'').decode())
                token = (qs.get('token') or [None])[0]
                if token:
                    scope['user'] = await _user_from_token(token)
        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
