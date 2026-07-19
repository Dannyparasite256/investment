"""ASGI application with HTTP + WebSocket (Channels)."""
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from notifications.routing import websocket_urlpatterns as notif_ws  # noqa: E402
from support.middleware import TokenAuthMiddlewareStack  # noqa: E402
from support.routing import websocket_urlpatterns as support_ws  # noqa: E402

websocket_urlpatterns = notif_ws + support_ws

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    ),
})
