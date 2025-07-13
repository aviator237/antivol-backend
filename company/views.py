from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.core.paginator import Paginator
from .models import Company, Catalog, Category, DistributionZone
from .forms import CatalogForm, CompanyUpdateForm, DistributionZoneForm
from authentification.forms import CompanyCreationForm as CompanyCreateForm
from account.models import Profil, UserRole
from .decorators import company_owner_required, regular_user_required
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


@login_required
def company_create(request):
    """Vue pour créer une nouvelle entreprise"""
    # Vérifier si l'utilisateur est un administrateur d'entreprise
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.role != UserRole.COMPANY_OWNER:
            messages.error(request, "Vous n'avez pas les droits pour créer une entreprise.")
            return redirect('/account')

        # Vérifier si l'utilisateur a déjà une entreprise associée
        if profile.company:
            messages.info(request, "Vous avez déjà une entreprise associée à votre compte.")
            return redirect('company:dashboard')

        if request.method == 'POST':
            form = CompanyCreateForm(request.POST)
            if form.is_valid():
                company = form.save()
                # Associer l'entreprise au profil de l'utilisateur
                profile.company = company
                profile.save()
                messages.success(request, "Votre entreprise a été créée avec succès.")
                return redirect('company:dashboard')
        else:
            form = CompanyCreateForm()

        uid = urlsafe_base64_encode(force_bytes(request.user.id))

        return render(request, 'auth/company_create.html', {
            'uid': uid,
            'form': form,
            'title': 'Créer une entreprise'
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@company_owner_required
def company_dashboard(request):
    """Vue pour le tableau de bord de l'entreprise"""
    # L'utilisateur est déjà vérifié comme étant un administrateur d'entreprise avec une entreprise associée
    profile = Profil.objects.get(owner=request.user)
    company = profile.company

    # Récupérer les informations sur la période d'essai
    trial_status = company.get_trial_status()

    return render(request, 'company/dashboard.html', {
        'company': company,
        'is_owner': True,  # Toujours vrai avec le décorateur company_owner_required
        'trial_status': trial_status
    })


@login_required
def company_detail(request):
    """Vue pour afficher les détails de l'entreprise"""
    try:
        profile = Profil.objects.get(owner=request.user)
        if not profile.company:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('/account')

        company = profile.company

        return render(request, 'company/company_detail.html', {
            'company': company,
            'is_owner': profile.is_company_owner()
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@company_owner_required
def company_update(request):
    """Vue pour modifier les informations de l'entreprise"""
    # L'utilisateur est déjà vérifié comme étant un administrateur d'entreprise avec une entreprise associée
    profile = Profil.objects.get(owner=request.user)
    company = profile.company

    if request.method == 'POST':
        form = CompanyUpdateForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Les informations de l'entreprise ont été mises à jour avec succès.")
            return redirect('company:company_detail')
    else:
        form = CompanyUpdateForm(instance=company)

    return render(request, 'company/company_form.html', {
        'form': form,
        'company': company,
        'is_owner': True  # Toujours vrai avec le décorateur company_owner_required
    })


@login_required
def catalog_list(request):
    """Vue pour afficher la liste des catalogues d'une entreprise"""
    # Vérifier si l'utilisateur est associé à une entreprise
    try:
        profile = Profil.objects.get(owner=request.user)
        if not profile.company:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('/account')

        company = profile.company
        catalogs = Catalog.objects.filter(company=company).order_by('-created_at')

        # Pagination
        paginator = Paginator(catalogs, 10)  # 10 catalogues par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'company/catalog_list.html', {
            'company': company,
            'page_obj': page_obj,
            'is_owner': profile.is_company_owner()
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def catalog_create(request):
    """Vue pour créer un nouveau catalogue"""
    # Vérifier si l'utilisateur est associé à une entreprise
    try:
        profile = Profil.objects.get(owner=request.user)
        if not profile.company:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('/account')

        company = profile.company

        # Récupérer le statut d'essai de l'entreprise
        trial_status = company.get_trial_status()

        # Vérifier si l'entreprise peut gérer ses catalogues
        if not company.can_manage_catalogs():
            if trial_status['is_trial']:
                # Ne devrait jamais arriver, mais par sécurité
                messages.error(request, "Une erreur s'est produite. Veuillez contacter le support.")
            else:
                messages.error(request, "Votre période d'essai est expirée. Veuillez souscrire à un abonnement pour pouvoir gérer vos catalogues.")
                # Rediriger vers la page d'abonnement
                return redirect('company:dashboard')

        # Vérifier si l'entreprise peut créer un nouveau catalogue (limite en période d'essai)
        if not trial_status['can_create_catalog']:
            messages.warning(request, f"En période d'essai, vous êtes limité à {trial_status['max_catalogs']} catalogue. Veuillez souscrire à un abonnement pour en créer davantage.")
            return redirect('company:catalog_list')

        # Vérifier si l'entreprise a des zones de diffusion
        zones_count = DistributionZone.objects.filter(company=company).count()
        if zones_count == 0:
            messages.warning(request, "Vous devez d'abord créer au moins une zone de diffusion avant de pouvoir créer un catalogue.")
            return redirect('company:zone_list')

        if request.method == 'POST':
            form = CatalogForm(request.POST, request.FILES, company=company)
            if form.is_valid():
                catalog = form.save(commit=False)
                catalog.company = company
                catalog.publisher = request.user
                catalog.save()
                # Enregistrer les zones de diffusion
                form.save_m2m()
                messages.success(request, "Le catalogue a été créé avec succès.")
                return redirect('company:catalog_list')
        else:
            form = CatalogForm(company=company)

        # Récupérer les informations sur la période d'essai
        trial_status = company.get_trial_status()

        return render(request, 'company/catalog_form.html', {
            'form': form,
            'company': company,
            'is_new': True,
            'trial_status': trial_status
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def catalog_detail(request, catalog_id):
    """Vue pour afficher les détails d'un catalogue"""
    catalog = get_object_or_404(Catalog, id=catalog_id)

    # Vérifier si l'utilisateur a accès à ce catalogue
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != catalog.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas accès à ce catalogue.")
            return redirect('/account')

        return render(request, 'company/catalog_detail.html', {
            'catalog': catalog,
            'company': catalog.company,
            'is_owner': profile.is_company_owner() and profile.company == catalog.company
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def catalog_update(request, catalog_id):
    """Vue pour mettre à jour un catalogue existant"""
    catalog = get_object_or_404(Catalog, id=catalog_id)

    # Vérifier si l'utilisateur a le droit de modifier ce catalogue
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != catalog.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas le droit de modifier ce catalogue.")
            return redirect('/account')

        company = catalog.company

        # Vérifier si l'entreprise peut gérer ses catalogues
        if not company.can_manage_catalogs() and not request.user.is_staff:
            if company.is_in_trial_period():
                # Ne devrait jamais arriver, mais par sécurité
                messages.error(request, "Une erreur s'est produite. Veuillez contacter le support.")
            else:
                messages.error(request, "Votre période d'essai est expirée. Veuillez souscrire à un abonnement pour pouvoir gérer vos catalogues.")
                # Rediriger vers la page d'abonnement
                return redirect('company:dashboard')

        # Vérifier si l'entreprise a des zones de diffusion
        zones_count = DistributionZone.objects.filter(company=company).count()
        if zones_count == 0:
            messages.warning(request, "Vous devez d'abord créer au moins une zone de diffusion avant de pouvoir modifier un catalogue.")
            return redirect('company:zone_list')

        if request.method == 'POST':
            form = CatalogForm(request.POST, request.FILES, instance=catalog, company=company)
            if form.is_valid():
                form.save()
                messages.success(request, "Le catalogue a été mis à jour avec succès.")
                return redirect('company:catalog_detail', catalog_id=catalog.id)
        else:
            form = CatalogForm(instance=catalog, company=company)

        # Récupérer les informations sur la période d'essai
        trial_status = company.get_trial_status()

        return render(request, 'company/catalog_form.html', {
            'form': form,
            'company': catalog.company,
            'catalog': catalog,
            'is_new': False,
            'trial_status': trial_status
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def catalog_delete(request, catalog_id):
    """Vue pour supprimer un catalogue"""
    catalog = get_object_or_404(Catalog, id=catalog_id)

    # Vérifier si l'utilisateur a le droit de supprimer ce catalogue
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != catalog.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas le droit de supprimer ce catalogue.")
            return redirect('/account')

        if request.method == 'POST':
            company_id = catalog.company.id
            catalog.delete()
            messages.success(request, "Le catalogue a été supprimé avec succès.")
            return redirect('company:catalog_list')

        return render(request, 'company/catalog_confirm_delete.html', {
            'catalog': catalog
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def catalog_download(request, catalog_id):
    """Vue pour télécharger un catalogue"""
    catalog = get_object_or_404(Catalog, id=catalog_id)

    # Vérifier si le fichier existe
    if not catalog.file:
        raise Http404("Le fichier n'existe pas.")

    # Ouvrir le fichier et le renvoyer comme réponse
    try:
        response = HttpResponse(catalog.file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{catalog.filename()}"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement: {str(e)}")
        return redirect('company:catalog_detail', catalog_id=catalog.id)


def public_catalog_list(request):
    """Vue publique pour afficher tous les catalogues disponibles"""
    # Récupérer uniquement les entreprises actives (en période d'essai ou avec un abonnement)
    active_companies = []
    for company in Company.objects.all():
        trial_status = company.get_trial_status()
        if trial_status['is_trial'] or trial_status['has_subscription'] or company.is_active:
            active_companies.append(company.id)

    # Récupérer uniquement les catalogues des entreprises actives
    catalogs = Catalog.objects.filter(company_id__in=active_companies).order_by('-created_at')

    # Filtrage par entreprise
    company_id = request.GET.get('company')
    if company_id:
        catalogs = catalogs.filter(company_id=company_id)

    # Pagination
    paginator = Paginator(catalogs, 12)  # 12 catalogues par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Liste des entreprises actives pour le filtre
    companies = Company.objects.filter(id__in=active_companies).order_by('name')

    return render(request, 'company/public_catalog_list.html', {
        'page_obj': page_obj,
        'companies': companies,
        'selected_company': company_id
    })


def api_documentation(request):
    """Vue pour afficher la documentation de l'API"""
    # Liste des catégories pour les exemples
    categories = Category.objects.all()[:2]

    return render(request, 'company/api_documentation.html', {
        'categories': categories
    })


@login_required
def zone_list(request):
    """Vue pour afficher la liste des zones de diffusion d'une entreprise"""
    # Vérifier si l'utilisateur est associé à une entreprise
    try:
        profile = Profil.objects.get(owner=request.user)
        if not profile.company:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('/account')

        company = profile.company
        zones = DistributionZone.objects.filter(company=company).order_by('name')

        # Pagination
        paginator = Paginator(zones, 10)  # 10 zones par page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'company/zone_list.html', {
            'company': company,
            'page_obj': page_obj,
            'is_owner': profile.is_company_owner()
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def zone_create(request):
    """Vue pour créer une nouvelle zone de diffusion"""
    # Vérifier si l'utilisateur est associé à une entreprise
    try:
        profile = Profil.objects.get(owner=request.user)
        if not profile.company:
            messages.error(request, "Vous n'êtes pas associé à une entreprise.")
            return redirect('/account')

        company = profile.company
        # Vérifier si la requête vient d'une fenêtre popup
        is_popup = request.GET.get('popup', 'false') == 'true'

        if request.method == 'POST':
            form = DistributionZoneForm(request.POST)
            if form.is_valid():
                zone = form.save(commit=False)
                zone.company = company
                zone.save()
                messages.success(request, "La zone de diffusion a été créée avec succès.")

                # Si c'est une fenêtre popup, rediriger vers une page de confirmation
                if is_popup:
                    return render(request, 'company/zone_created_popup.html')
                else:
                    return redirect('company:zone_list')
        else:
            form = DistributionZoneForm()

        return render(request, 'company/zone_form.html', {
            'form': form,
            'company': company,
            'is_new': True,
            'is_popup': is_popup
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def zone_update(request, zone_id):
    """Vue pour mettre à jour une zone de diffusion existante"""
    zone = get_object_or_404(DistributionZone, id=zone_id)

    # Vérifier si l'utilisateur a le droit de modifier cette zone
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != zone.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas le droit de modifier cette zone de diffusion.")
            return redirect('/account')

        if request.method == 'POST':
            form = DistributionZoneForm(request.POST, instance=zone)
            if form.is_valid():
                form.save()
                messages.success(request, "La zone de diffusion a été mise à jour avec succès.")
                return redirect('company:zone_list')
        else:
            form = DistributionZoneForm(instance=zone)

        return render(request, 'company/zone_form.html', {
            'form': form,
            'company': zone.company,
            'zone': zone,
            'is_new': False
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def zone_delete(request, zone_id):
    """Vue pour supprimer une zone de diffusion"""
    zone = get_object_or_404(DistributionZone, id=zone_id)

    # Vérifier si l'utilisateur a le droit de supprimer cette zone
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != zone.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas le droit de supprimer cette zone de diffusion.")
            return redirect('/account')

        # Vérifier si la zone est utilisée par des catalogues
        catalogs_count = zone.catalogs.count()
        if catalogs_count > 0:
            messages.error(request, f"Cette zone de diffusion est utilisée par {catalogs_count} catalogue(s). Veuillez d'abord modifier ces catalogues.")
            return redirect('company:zone_list')

        if request.method == 'POST':
            zone.delete()
            messages.success(request, "La zone de diffusion a été supprimée avec succès.")
            return redirect('company:zone_list')

        return render(request, 'company/zone_confirm_delete.html', {
            'zone': zone
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')


@login_required
def zone_detail(request, zone_id):
    """Vue pour afficher les détails d'une zone de diffusion"""
    zone = get_object_or_404(DistributionZone, id=zone_id)

    # Vérifier si l'utilisateur a accès à cette zone
    try:
        profile = Profil.objects.get(owner=request.user)
        if profile.company != zone.company and not request.user.is_staff:
            messages.error(request, "Vous n'avez pas accès à cette zone de diffusion.")
            return redirect('/account')

        # Récupérer les catalogues associés à cette zone
        catalogs = zone.catalogs.all().order_by('-created_at')

        return render(request, 'company/zone_detail.html', {
            'zone': zone,
            'company': zone.company,
            'catalogs': catalogs,
            'is_owner': profile.is_company_owner() and profile.company == zone.company
        })
    except Profil.DoesNotExist:
        messages.error(request, "Profil utilisateur non trouvé.")
        return redirect('/account')
