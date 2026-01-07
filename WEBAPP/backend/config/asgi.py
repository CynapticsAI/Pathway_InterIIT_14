"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket consumers
from api.consumers import (
    MarketBreadthConsumer,
    StockTickConsumer,
    PnLConsumer,
    SarimaxConsumer,
    VolumeSpikeConsumer,
    NewsConsumer,
    NotificationConsumer,
)
from users.consumers import ChatConsumer, ChatListConsumer
from users.jwt_auth_middleware import JWTAuthMiddlewareStack

# WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/market-breadth/', MarketBreadthConsumer.as_asgi()),
    path('ws/stock-ticks/', StockTickConsumer.as_asgi()),
    path('ws/pnl/', PnLConsumer.as_asgi()),
    path('ws/sarimax-forecast/', SarimaxConsumer.as_asgi()),
    path('ws/volume-spikes/', VolumeSpikeConsumer.as_asgi()),
    path('ws/news/', NewsConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    # Chat WebSocket endpoints
    path('ws/chat/<int:conversation_id>/', ChatConsumer.as_asgi()),
    path('ws/chat/list/', ChatListConsumer.as_asgi()),
]

# ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})

