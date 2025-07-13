from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from notification.utils import NotificationService
from .models import Album,  Photo, SharedAlbum
from django.conf import settings

@receiver(pre_delete, sender=Album)
def delete_album(sender, instance, **kwargs):
    try:
        NotificationService().notify_album_update(instance, "delete")
    except Exception as e:
        print(e)

@receiver(pre_delete, sender=SharedAlbum)
def delete_shared_album(sender, instance, **kwargs):
    try:
        NotificationService().notify_shared_album_update(instance, "delete")
    except Exception as e:
        print(e)

@receiver(pre_delete, sender=Photo)
def delete_photo(sender, instance, **kwargs):
    try:
        NotificationService().notify_album_update(album=instance.album, action="delete", photo=instance)
    except Exception as e:
        print(e)

@receiver(post_save, sender=Album)
def create_or_update_album(sender, instance, created, **kwargs):
    try:
        if created:
            NotificationService().notify_album_update(instance, "create")
        else:
            NotificationService().notify_album_update(instance, "update")
    except Exception as e:
        print(e)


@receiver(post_save, sender=Photo)
def create_or_update_photo(sender, instance, created, **kwargs):
    try:
        NotificationService().notify_album_update(album=instance.album, action="update", photo=instance)
    except Exception as e:
        print(e)

@receiver(post_save, sender=SharedAlbum)
def create_or_update_shared_album(sender, instance, created, **kwargs):
    try:
        if created:
            NotificationService().notify_shared_album_update(instance, "create")
        else:
            NotificationService().notify_shared_album_update(instance, "update")
    except Exception as e:
        print(e)