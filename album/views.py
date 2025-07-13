from itertools import chain
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from .models import Album, Photo, SharedAlbum
from django.contrib.auth.models import User
from django import forms
from .forms import AlbumForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
import os
from account.views import get_user_photos_directory_size
from pricing.models import Plan, Product, PlanType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.db.models import Q

@login_required
def share_album(request: WSGIRequest, album_id):
    album = Album.objects.get(id=album_id)
    if request.user != album.owner:
        messages.error(request, "Vous n'avez pas la permission de partager cet album.")
        return redirect('account:home')
    if request.method == 'POST':
        contacts: str = request.POST.get('contacts')
        my_contacts = request.POST.get('my_contacts')
        for phone_number in contacts.split(','):
            try:
                user = User.objects.get(username=phone_number)
                SharedAlbum.objects.create(album=album, shared_with=user).save()
            except User.DoesNotExist:
                continue
        messages.success(request, "Nous avons envoyé des invitations de partage à vos contacts !")
        return redirect('album:albums')
    user = request.user  # L'utilisateur qui envoie la requête

    # 1. Récupérer les albums que l'utilisateur a créés
    owned_albums = Album.objects.filter(owner=user)

    # 2. Récupérer les photos de ces albums
    owned_photos = Photo.objects.filter(album__in=owned_albums)

    # 3. Récupérer les utilisateurs qui ont partagé ces albums (peu importe le statut)
    shared_with_users = User.objects.filter(
        Q(sharedalbum__album__in=owned_albums) #Utilisateurs qui ont reçu un partage
    ).distinct()
    # shared_by_users = User.objects.filter(
    #     Q(sharedalbum__shared_with=user)
    # ).distinct()
    shared_with_users = shared_with_users.exclude(id=user.id)
    # combined_users = list(chain(shared_with_users, shared_by_users))
    # print(combined_users)

    return render(request, 'account/share.html', {'album': album, "contacts": shared_with_users})

@login_required
def albums(request: WSGIRequest):
    if request.method == 'POST':
        form = AlbumForm(request.POST)
        if form.is_valid():
            album = form.save(commit=False)
            album.owner = request.user
            album.save()
        messages.success(request, "Album photo crée avec succès !")
        return redirect('album:albums')
    else:
        form = AlbumForm()
    user_albums_list = Album.objects.filter(owner=request.user)
    paginator = Paginator(user_albums_list, 12)  # Show 10 albums per page

    page_number = request.GET.get('page')
    user_albums = paginator.get_page(page_number if page_number is not None else 1)
    for album in user_albums:
        album.photo_count = Photo.objects.filter(album=album).count()
    return render(request, 'account/albums.html', {'form': form, 'albums': user_albums, "page_obj": user_albums})

@login_required
def shared_albums(request: WSGIRequest):
    shared_albums_list = SharedAlbum.objects.filter(shared_with=request.user).select_related('album')
    paginator = Paginator(shared_albums_list, 12)  # Show 12 shared albums per page
    page_number = request.GET.get('page')
    shared_albums = paginator.get_page(page_number if page_number is not None else 1)
    for shared_album in shared_albums:
        shared_album.album.photo_count = Photo.objects.filter(album=shared_album.album).count()
    return render(request, 'account/shared_albums.html', {'albums': shared_albums, "page_obj": shared_albums, 'title': 'Photos partagées'})

@login_required
def edit_album(request: WSGIRequest, album_id):
    album = Album.objects.get(id=album_id, owner=request.user)
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            messages.success(request, "Album modifié avec succès !")
            return redirect('album:albums')
    else:
        form = AlbumForm(instance=album)
    return render(request, 'account/edit_album.html', {'form': form, 'album': album})

@login_required
def delete_album(request: WSGIRequest, album_id):
    album = Album.objects.get(id=album_id)
    if request.user == album.owner or request.user.is_superuser:
        if request.method == 'GET':
            photos = Photo.objects.filter(album=album)
            album.delete()
            for photo in photos:
                photo.file.delete()  # Delete the file from the storage
                photo.delete()  # Delete the Photo object from the database
            messages.success(request, "Album supprimé avec succès !")
            return redirect('album:albums')
    else:
        messages.error(request, "Vous n'avez pas la permission de supprimer cet album.")
    return redirect('album:albums')
    # return render(request, 'account/confirm_delete.html', {'album': album})

@login_required
def add_photos(request: WSGIRequest, album_id):
    back_url = request.GET.get('back_url')
    album = Album.objects.get(id=album_id)
    if album.owner != request.user and not SharedAlbum.objects.filter(album=album, shared_with=request.user).exists():
        return JsonResponse({"status": "error", "message": "Vous n'avez pas la permission d'ajouter des photos à cet album."}, status=403)
    
    if request.method == 'POST':
        photos = request.FILES.getlist('photos')
        total_size = sum(photo.size for photo in photos) / (1024 * 1024 * 1024)
        owner = album.owner if album.owner == request.user else request.user
        try:
            user_plan = Plan.objects.get(profil=request.user.profil)
            user_product = user_plan.product
        except Plan.DoesNotExist:
            user_product = Product.objects.get(type=PlanType.FREE.value[0])
        available_space = user_product.storage - get_user_photos_directory_size(owner)
        if total_size > available_space:
            return JsonResponse({"status": "error", "message": "Vous n'avez pas assez d'espace de stockage pour ajouter ces photos."}, status=400)
        
        for photo in photos:
            Photo.objects.create(album=album, owner=request.user, file=photo)
        return JsonResponse({"status": "success", "message": "Vos photos ont été uploadées avec succès !", "redirect_url": reverse('album:albums')}, status=200)
    
    return render(request, 'account/add_photo.html', {'album': album, 'back_url': back_url, 'title': 'Ajouter des photos'})



