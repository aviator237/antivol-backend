"""
ASGI config for media_app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""


import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_app.settings')
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from my_socket.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
