from django.shortcuts import render
from django.core.handlers.wsgi import WSGIRequest
from album.models import InvitationStatus, SharedAlbum
from album.serializers import SharedAlbumSerializer, AlbumSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Box
from .serializers import BoxSerializer
from django.http import Http404, HttpResponseBadRequest

from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sites.shortcuts import get_current_site
from rest_framework_simplejwt.tokens import AccessToken
from album.models import Album, Photo
from album.serializers import PhotoSerializer
from rest_framework.permissions import IsAuthenticated


class BoxApiView(APIView):
    
    def get(self, request: WSGIRequest):
        print("Hello World", request.GET)
        pass
    
    def post(self, request):

        pass
    
    def put(self, request):
        pass
    
    def delete(self, request):
        pass


class BoxViewSet(ModelViewSet):
    
    serializer_class = BoxSerializer
 
    def get_queryset(self):
        return Box.objects.all()
    


@api_view(['POST'])
@authentication_classes(())
@permission_classes(())
def box_register(request: WSGIRequest):
    try:
        box = Box.objects.get(mac_address=request.data.get('mac_address'))
        serializer = BoxSerializer(box)
        response = {'box': serializer.data}
        if box.owner is not None:
            refresh = RefreshToken.for_user(box.owner)
            response['refresh'] = str(refresh)
            response['access'] = str(refresh.access_token)
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            return Response(response, status=status.HTTP_201_CREATED)
    except Box.DoesNotExist:
        serializer = BoxSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # refresh = RefreshToken.for_user(request.user)
            # , 'refresh': str(refresh), 'access': str(refresh.access_token)
            return Response({'box': serializer.data,}, status=status.HTTP_201_CREATED)
    except Exception as e:
        print(e)
        # return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes(())
@permission_classes(())
def check_phone_number(request, phone_number):
    user_exists = User.objects.filter(username=phone_number).exists()
    return Response({'exists': user_exists}, status=status.HTTP_200_OK)

@api_view(['GET'])
def accept_invitation(request, shared_album_id, accept):
    try:
        expected_sa = SharedAlbum.objects.get(id=shared_album_id)
        if accept == "1":
            expected_sa.status = InvitationStatus.ACCEPTED.value[0]
            expected_sa.save()
            return Response({'status': "ok"}, status=status.HTTP_200_OK)
        elif accept == "0":
            expected_sa.status = InvitationStatus.DENIED.value[0]
            expected_sa.save()
            return Response({'status': "ok"}, status=status.HTTP_200_OK)
        else:
            raise HttpResponseBadRequest()
    except SharedAlbum.DoesNotExist:
        raise Http404("SharedAlbum not found")
    


@api_view(['GET'])
def check_associated_account(request, mac_address):
    try:
        box = Box.objects.get(mac_address=mac_address)
        has_owner = box.owner is not None
        return Response({'has_owner': has_owner}, status=status.HTTP_200_OK)
    except Box.DoesNotExist:
        raise Http404("Box not found")
    

@api_view(['GET'])
@authentication_classes(())
@permission_classes(())
def get_box_by_mac_address(request, mac_address):
    try:
        box = Box.objects.get(mac_address=mac_address)
        serializer = BoxSerializer(box)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Box.DoesNotExist:
        raise Http404("Box not found")
    

@api_view(['GET'])
def get_shared_albums(request):
    accepted_status = InvitationStatus.ACCEPTED.value[0]
    pending_status = InvitationStatus.PENDING.value[0]
    shared_albums = SharedAlbum.objects.filter(shared_with=request.user, status__in=[accepted_status, pending_status])
    owned_albums = Album.objects.filter(owner=request.user)
    owned_albums_serializer = AlbumSerializer(owned_albums, many=True)
    shared_album_serializer = SharedAlbumSerializer(shared_albums, many=True)
    return Response({"shared_albums": shared_album_serializer.data, "albums": owned_albums_serializer.data}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shared_album_photos(request, shared_album_id):
    try:
        shared_album = SharedAlbum.objects.get(id=shared_album_id)
        album = shared_album.album
        if album.owner == request.user or request.user.is_superuser or shared_album.shared_with == request.user:
            photos = Photo.objects.filter(album=album)
            serializer = PhotoSerializer(photos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'You do not have permission to access this album.'}, status=status.HTTP_403_FORBIDDEN)
    except SharedAlbum.DoesNotExist:
        raise Http404("Shared album not found")

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_album_photos(request, album_id):
    try:
        album = Album.objects.get(id=album_id)
        if album.owner == request.user or request.user.is_superuser:
            photos = Photo.objects.filter(album=album)
            serializer = PhotoSerializer(photos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'You do not have permission to access this album.'}, status=status.HTTP_403_FORBIDDEN)
    except Album.DoesNotExist:
        raise Http404("Shared album not found")
