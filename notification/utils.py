
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from box.models import Box
from album.models import Album, Photo, SharedAlbum
from album.serializers import AlbumSerializer, PhotoSerializer, SharedAlbumSerializer
from notification.enums import SocketDataType, SocketEvent

class NotificationService:
    # def __inii__(self):
    #     self.client = Client()

    def notify_box(self, box: Box, message: str = "", event: SocketEvent=SocketEvent.NOTIFICATION, type: SocketDataType = None, data = None):
        if box.socket_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                box.socket_id,
                {
                    'event': event.value if event else None,
                    'type': 'send_notification',
                    'my_type': type.value if type else None,
                    'data': data,
                    'message': message
                }
            )
        # else:
        #     raise ValueError('Box is not connected to any socket.')



    def notify_album_update(self, album: Album, action, photo: Photo | None = None, just_owner: bool = False):
        message = f'Album photo mis à jour...'
        serializer = AlbumSerializer(album)
        data = {'album': serializer.data, "action": action}
        if photo is not None:
            data["photo"] = PhotoSerializer(photo).data
        list_box = list(Box.objects.filter(owner=album.owner))
        for box in list_box:
            if box.is_connected:
                self.notify_box(box, message, event=SocketEvent.NOTIFICATION, type=SocketDataType.SHARE_PHOTO, data=data)
        list_box.clear()
        if not just_owner:
            list_shared_album = album.get_shared_albums()
            for sa in list_shared_album:
                serializer = SharedAlbumSerializer(sa)
                data = {'shared_album': serializer.data, "action": action}
                if photo is not None:
                    data["photo"] = PhotoSerializer(photo).data
                try:
                    # list_box.append(Box.objects.get(owner=sa.shared_with))
                    box = Box.objects.get(owner=sa.shared_with)
                    if box.is_connected:
                        self.notify_box(box, message, event=SocketEvent.NOTIFICATION, type=SocketDataType.SHARE_PHOTO, data=data)
                except:
                    pass
        # for box in list_box:
        #     if box.is_connected:
        #         self.notify_box(box, message, event=SocketEvent.NOTIFICATION, type=SocketDataType.SHARE_PHOTO, data=data)


    def notify_shared_album_update(self, sharedAlbum: SharedAlbum, action):
        message = f'Album photo mis à jour...'
        serializer = SharedAlbumSerializer(sharedAlbum)
        data = {'shared_album': serializer.data, "action": action}
        list_box = list(Box.objects.filter(owner=sharedAlbum.shared_with))
        for box in list_box:
            if box.is_connected:
                self.notify_box(box, message, event=SocketEvent.NOTIFICATION, type=SocketDataType.SHARE_PHOTO, data=data)

    def notify_shared_album_invitation(self, sharedAlbum: SharedAlbum, action):
        message = f'Album photo mis à jour...'
        serializer = AlbumSerializer(sharedAlbum.album)
        data = {'album': serializer.data, "action": action}
        list_box = list(Box.objects.filter(owner=sharedAlbum.shared_with))
        for box in list_box:
            if box.is_connected:
                self.notify_box(box, message, event=SocketEvent.NOTIFICATION, type=SocketDataType.SHARE_PHOTO, data=data)


    def notify_account_creation(self, box: Box):
        
        message = f'Création du compte en cours...'
        self.notify_box(box, message, event=SocketEvent.AUTHENTICATE)

    def notify_account_creation_success(self, box: Box):
        message = f'Compte créé avec succès...'
        self.notify_box(box, message, event=SocketEvent.AUTHENTICATE)

    def notify_account_creation_failure(self, box: Box):
        message = f'Erreur lors de la création du compte...'
        self.notify_box(box, message, event=SocketEvent.AUTHENTICATE)
    
    def phone_number_verifiynig(self, box: Box):
        message = f'Verification du numéro de téléphone...'
        self.notify_box(box, message, event=SocketEvent.AUTHENTICATE)

    def renew_token(self, box: Box, token: dict):
        message = 'Nouveau token'
        self.notify_box(box, message, event=SocketEvent.TOKEN, data=token)

    def close_window(self, box: Box):
        self.notify_box(box, event=SocketEvent.ACTION, type=SocketDataType.CLOSE_WINDOW)

