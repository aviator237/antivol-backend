from enum import Enum
from django.db import models
from django.contrib.auth.models import User
import uuid
from django_clamd.validators import validate_file_infection
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.validators import FileExtensionValidator

def user_directory_path(instance, filename):
    extension = filename.split('.')[-1]
    random_filename = f'{uuid.uuid4()}.{extension}'
    if instance.owner == instance.album.owner:
        # Propriétaire de l'album
        return f'photos/{instance.owner.id}/{instance.album.id}/{random_filename}'
    else:
        # Utilisateur partageant l'album
        return f'photos/{instance.album.owner.id}/{instance.album.id}/{random_filename}'

class InvitationStatus(Enum):
    PENDING = "pending", "En attente"
    ACCEPTED = "accepted", "Accepté"
    DENIED = "denied", "Refusé"
    EXPIRY = "expiry", "Expiré"

    @classmethod
    def choices(cls):
        return [(key.value[0], key.value[1]) for key in cls]

class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=False, verbose_name='nom')
    owner = models.ForeignKey(User, blank=True, null=True, verbose_name='propriétaire', on_delete=models.CASCADE)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.name
    
    def get_shared_albums(self):
        return SharedAlbum.objects.filter(album=self)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
 
    class Meta:
        ordering = ['-created_at']
        verbose_name = "album"
        verbose_name_plural = "albums"

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(Album, blank=True, null=True, verbose_name='album', on_delete=models.CASCADE)
    owner = models.ForeignKey(User, blank=True, null=True, verbose_name='propriétaire', on_delete=models.CASCADE)
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")
    file = models.ImageField(upload_to=user_directory_path, verbose_name='image', validators=[validate_file_infection, FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])])

    def __str__(self):
        return self.file.name
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "photo"
        verbose_name_plural = "photos"

class SharedAlbum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(Album, blank=True, null=True, verbose_name='album', on_delete=models.CASCADE)
    shared_with = models.ForeignKey(User, blank=True, null=True, verbose_name='partagé avec', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, verbose_name='statut', choices=InvitationStatus.choices(), default=InvitationStatus.PENDING.value[0])
    created_at = models.DateTimeField(blank=True, null=True, auto_created=True, auto_now_add=True, verbose_name="date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="dernière mise à jour")

    def __str__(self):
        return self.album.name
    
    def is_accepted(self):
        return self.status == InvitationStatus.ACCEPTED.value[0]
    
    
    def is_denied(self):
        return self.status == InvitationStatus.DENIED.value[0]
    
    def is_pending(self):
        return self.status == InvitationStatus.PENDING.value[0]
    
    def is_expiry(self):
        return self.status == InvitationStatus.EXPIRY.value[0]
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "album partagé"
        verbose_name_plural = "albums partagés"
