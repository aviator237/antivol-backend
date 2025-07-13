 
from django.urls import path

from .views import *

app_name = "box"
urlpatterns = [
    path('', box_register),
    # path('api/box/', BoxApiView.as_view()),
    path("get_shared_albums", get_shared_albums, name="get_shared_albums"),
    path("get_album_photos/<album_id>/", get_album_photos, name="get_album_photos"),
    path("accept_invitation/<shared_album_id>/<accept>/", accept_invitation, name="accept_invitation"),
    path("get_shared_album_photos/<shared_album_id>/", get_shared_album_photos, name="get_shared_album_photos"),
    path("check_phone_number/<phone_number>/", check_phone_number, name="check_phone_number"),
    path("check_associated_account/<mac_address>/", check_associated_account, name="check_associated_account"),
    path("get_box_by_mac_address/<mac_address>/", get_box_by_mac_address, name="get_box_by_mac_address"),

]
