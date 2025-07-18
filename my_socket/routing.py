from django.urls import re_path
from .consumers import NotificationConsumer
websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<socket_id>\w+)/$', NotificationConsumer.as_asgi()),
]