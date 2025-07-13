 
from django.urls import path

from .views import *

app_name = "album"
urlpatterns = [
    path('share_album/<album_id>/', share_album, name="share_album"),
    path('add_photos/<album_id>/', add_photos, name="add_photos"),
    path('albums/', albums, name="albums"),
    path('shared_albums/', shared_albums, name="shared_albums"),
    path('delete_album/<album_id>/', delete_album, name="delete_album"),

]
