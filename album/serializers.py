from authentification.serializers import UserSerializer
from .models import Album, Photo, SharedAlbum
from rest_framework.serializers import ModelSerializer


class AlbumSerializer(ModelSerializer):
    owner = UserSerializer()
    
    class Meta:
        model = Album
        fields = ['id', 'name', 'owner', 'created_at', 'last_updated']

class PhotoSerializer(ModelSerializer):
    owner = UserSerializer()
    album = AlbumSerializer()

    class Meta:
        model = Photo
        fields = ['id', 'album', 'owner', 'created_at', 'last_updated', 'file']

class SharedAlbumSerializer(ModelSerializer):
    album = AlbumSerializer()
    shared_with = UserSerializer()

    class Meta:
        model = SharedAlbum
        fields = ['id', 'album', "status", 'shared_with', 'created_at', 'last_updated']


