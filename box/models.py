import uuid
from django.db import models
from django.contrib.auth.models import User
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import secrets
import string

from notification.enums import SocketEvent

class Box(models.Model):
    mac_address = models.CharField(max_length=100, unique=True, verbose_name='adresse mac')
    owner = models.ForeignKey(User, related_name='propriétaire', blank=True, null=True, verbose_name='propriétaire', on_delete=models.CASCADE)
    socket_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='socket ID')
    is_connected = models.BooleanField(default=False, verbose_name='connecté ?')
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de commande")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def save(self, *args, **kwargs):
        if not self.socket_id:
            self.socket_id = self.generate_socket_id()
        super().save(*args, **kwargs)
        self.notify_owner()

    def generate_socket_id(self, length=16):
        characters = string.ascii_letters + string.digits
        socket_id = ''.join(secrets.choice(characters) for _ in range(length))
        return socket_id

    def notify_owner(self):
        if self.socket_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                self.socket_id,
                {
                    'type': 'send_notification',
                    'event': SocketEvent.NOTIFICATION.value,
                    'message': f'Your box "{self.mac_address}" has been updated.'
                }
            )

    def __str__(self):
        return self.mac_address
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "box"
        verbose_name_plural = "boxes"





















