from django.urls import path

from support.consumers import SupportChatConsumer

websocket_urlpatterns = [
    path('ws/support/', SupportChatConsumer.as_asgi()),
]
