from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
import os
from media_app.settings import MEDIA_ROOT
from pricing.models import Product
from album.models import Album, Photo, SharedAlbum
# from album.utils import get_user_photos_directory_size
from pricing.models import Plan, Product, PlanType
from account.models import Profil, UserRole
from company.decorators import regular_user_required

@regular_user_required
def index(request: WSGIRequest):
    """Vue pour le tableau de bord de l'utilisateur régulier"""
    # L'utilisateur est déjà vérifié comme étant un utilisateur régulier
    # Les administrateurs d'entreprise sont redirigés vers le tableau de bord de l'entreprise

    context = {
        "title": "Compte",
        "is_company_owner": False,  # Toujours faux avec le décorateur regular_user_required
        "has_company": False,
        # 'total_size': total_size,
        # 'remaining_storage': remaining_storage,
        # 'used_percentage': used_percentage,
        # 'user_plan': user_plan,
    }
    return render(request, "account/index.html", context)

@login_required
def share(request: WSGIRequest):
    return render(request, "account/share.html", context={"title": "Partage de photo"})

@login_required
def add_photos(request: WSGIRequest, album_id):
    back_url = request.GET.get('back_url')
    album = Album.objects.get(id=album_id)
    if album.owner != request.user and not SharedAlbum.objects.filter(album=album, shared_with=request.user).exists():
        messages.error(request, "Vous n'avez pas la permission d'ajouter des photos à cet album.")
        return redirect('album:albums')

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
            messages.error(request, "Vous n'avez pas assez d'espace de stockage pour ajouter ces photos.")
            return redirect('album:albums')

        for photo in photos:
            Photo.objects.create(album=album, owner=request.user, file=photo)
        messages.success(request, "Vos photos ont été uploadées avec succès !")
        return redirect('album:albums')

    return render(request, 'account/add_photo.html', {'album': album, 'back_url': back_url, 'title': 'Ajouter des photos'})

def get_user_photos_directory_size(user):
    base_dir = os.path.join(MEDIA_ROOT, f'photos/{user.id}')
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)

    # Convertir la taille en mégaoctets
    total_size_gb = total_size / (1024 * 1024 * 1024)
    return total_size_gb




