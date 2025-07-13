from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Exists, OuterRef
from math import cos, radians

from .models import Category, Company, Catalog, DistributionZone, PublicService
from .serializers import (
    CategorySerializer, CompanySerializer, CompanyLightSerializer,
    CatalogSerializer, DistributionZoneSerializer, DistributionZoneLightSerializer
)
from .api_serializers import PublicServiceSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """
    Liste toutes les catégories d'entreprises
    """
    categories = Category.objects.all().order_by('name')
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_list_by_category(request, category_id):
    """
    Liste toutes les entreprises d'une catégorie donnée
    """
    # Vérifier si la catégorie existe
    category = get_object_or_404(Category, id=category_id)

    # Récupérer les entreprises de cette catégorie
    companies = Company.objects.filter(category=category).order_by('name')
    serializer = CompanyLightSerializer(companies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_detail(request, company_id):
    """
    Détails d'une entreprise spécifique
    """
    company = get_object_or_404(Company, id=company_id)
    serializer = CompanySerializer(company)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def catalog_list_by_company(request, company_id):
    """
    Liste tous les catalogues d'une entreprise donnée
    """
    # Vérifier si l'entreprise existe
    company = get_object_or_404(Company, id=company_id)

    # Vérifier si les catalogues de l'entreprise sont visibles
    if not company.are_catalogs_visible():
        return Response(
            {"error": "Les catalogues de cette entreprise ne sont pas disponibles actuellement."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Récupérer les catalogues de cette entreprise
    catalogs = Catalog.objects.filter(company=company).order_by('-created_at')
    serializer = CatalogSerializer(catalogs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def catalog_detail(request, catalog_id):
    """
    Détails d'un catalogue spécifique
    """
    catalog = get_object_or_404(Catalog, id=catalog_id)

    # Vérifier si les catalogues de l'entreprise sont visibles
    if not catalog.company.are_catalogs_visible():
        return Response(
            {"error": "Ce catalogue n'est pas disponible actuellement."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = CatalogSerializer(catalog)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_list(request):
    """
    Liste toutes les entreprises
    """
    companies = Company.objects.all().order_by('name')
    serializer = CompanyLightSerializer(companies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_search_by_location(request):
    """
    Recherche des entreprises par proximité géographique
    """
    # Récupérer les paramètres de la requête
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km

    if not latitude or not longitude:
        return Response(
            {"error": "Les paramètres 'lat' et 'lng' sont requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)
    except ValueError:
        return Response(
            {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Ici, nous utilisons une approche simplifiée pour la recherche par proximité
    # Dans une application réelle, vous pourriez utiliser GeoDjango ou une bibliothèque spécialisée

    # Récupérer toutes les entreprises qui ont des coordonnées
    companies = Company.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )

    # Filtrer les entreprises en fonction de la distance
    # Cette méthode est approximative et fonctionne mieux pour de petites distances
    from math import cos, radians

    # 1 degré de latitude = environ 111 km
    lat_min = latitude - (radius / 111.0)
    lat_max = latitude + (radius / 111.0)

    # 1 degré de longitude = environ 111 km * cos(latitude)
    # La distance en longitude varie selon la latitude
    lng_factor = cos(radians(latitude)) * 111.0
    lng_min = longitude - (radius / lng_factor)
    lng_max = longitude + (radius / lng_factor)

    companies = companies.filter(
        latitude__gte=lat_min,
        latitude__lte=lat_max,
        longitude__gte=lng_min,
        longitude__lte=lng_max
    )

    serializer = CompanyLightSerializer(companies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def distribution_zone_list(request):
    """
    Liste toutes les zones de diffusion
    """
    zones = DistributionZone.objects.all().order_by('name')
    serializer = DistributionZoneSerializer(zones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def distribution_zone_detail(request, zone_id):
    """
    Détails d'une zone de diffusion spécifique
    """
    zone = get_object_or_404(DistributionZone, id=zone_id)
    serializer = DistributionZoneSerializer(zone)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def distribution_zone_list_by_company(request, company_id):
    """
    Liste toutes les zones de diffusion d'une entreprise donnée
    """
    # Vérifier si l'entreprise existe
    company = get_object_or_404(Company, id=company_id)

    # Récupérer les zones de diffusion de cette entreprise
    zones = DistributionZone.objects.filter(company=company).order_by('name')
    serializer = DistributionZoneSerializer(zones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def catalog_list_by_zone(request, zone_id):
    """
    Liste tous les catalogues associés à une zone de diffusion donnée
    """
    # Vérifier si la zone existe
    zone = get_object_or_404(DistributionZone, id=zone_id)

    # Récupérer les catalogues associés à cette zone
    # Filtrer pour n'inclure que les catalogues des entreprises avec abonnement actif ou en période d'essai
    catalogs_query = zone.catalogs.all()
    visible_catalogs = []

    for catalog in catalogs_query:
        if catalog.company.are_catalogs_visible():
            visible_catalogs.append(catalog.id)

    catalogs = Catalog.objects.filter(id__in=visible_catalogs).order_by('-created_at')
    serializer = CatalogSerializer(catalogs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def distribution_zone_search_by_location(request):
    """
    Recherche des zones de diffusion par proximité géographique
    """
    # Récupérer les paramètres de la requête
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km

    if not latitude or not longitude:
        return Response(
            {"error": "Les paramètres 'lat' et 'lng' sont requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)
    except ValueError:
        return Response(
            {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Récupérer toutes les zones qui ont des coordonnées
    zones = DistributionZone.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )

    # Filtrer les zones en fonction de la distance
    # 1 degré de latitude = environ 111 km
    lat_min = latitude - (radius / 111.0)
    lat_max = latitude + (radius / 111.0)

    # 1 degré de longitude = environ 111 km * cos(latitude)
    lng_factor = cos(radians(latitude)) * 111.0
    lng_min = longitude - (radius / lng_factor)
    lng_max = longitude + (radius / lng_factor)

    zones = zones.filter(
        latitude__gte=lat_min,
        latitude__lte=lat_max,
        longitude__gte=lng_min,
        longitude__lte=lng_max
    )

    serializer = DistributionZoneSerializer(zones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def companies_with_catalogs_in_zone(request):
    """
    Récupère la liste des entreprises qui ont publié au moins un catalogue dans la zone du client.
    Le client peut spécifier sa localisation par ville (city) ou par coordonnées (lat, lng).

    Paramètres:
    - city: Nom de la ville (optionnel)
    - lat: Latitude (optionnel, mais requis si lng est fourni)
    - lng: Longitude (optionnel, mais requis si lat est fourni)
    - radius: Rayon de recherche en km (optionnel, par défaut: 10km)
    - categories: Liste d'IDs de catégories séparés par des virgules pour filtrer les entreprises (optionnel)
    """
    # Récupérer les paramètres de la requête
    city = request.query_params.get('city')
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km
    categories = request.query_params.get('categories')

    # Vérifier qu'au moins un des paramètres de localisation est fourni
    if not city and (not latitude or not longitude):
        return Response(
            {"error": "Vous devez fournir soit le paramètre 'city', soit les paramètres 'lat' et 'lng'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Initialiser la requête pour les zones de diffusion
    zones_query = DistributionZone.objects.all()

    # Filtrer par ville si spécifiée
    if city:
        zones_query = zones_query.filter(name__icontains=city)

    # Filtrer par coordonnées si spécifiées
    elif latitude and longitude:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculer les limites de la zone de recherche
        lat_min = latitude - (radius / 111.0)
        lat_max = latitude + (radius / 111.0)

        lng_factor = cos(radians(latitude)) * 111.0
        lng_min = longitude - (radius / lng_factor)
        lng_max = longitude + (radius / lng_factor)

        zones_query = zones_query.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max
        )

    # Récupérer les IDs des zones trouvées
    zone_ids = zones_query.values_list('id', flat=True)

    # Récupérer les entreprises qui ont des catalogues dans ces zones
    # et qui ont un abonnement actif ou sont en période d'essai
    companies_with_catalogs = Company.objects.filter(
        catalogs__distribution_zones__id__in=zone_ids
    ).distinct()

    # Filtrer par catégories si spécifiées
    if categories:
        try:
            # Convertir la chaîne de caractères en liste d'IDs
            category_ids = [int(cat_id.strip()) for cat_id in categories.split(',')]
            companies_with_catalogs = companies_with_catalogs.filter(category_id__in=category_ids)
        except ValueError:
            return Response(
                {"error": "Le paramètre 'categories' doit être une liste d'IDs numériques séparés par des virgules"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Filtrer pour n'inclure que les entreprises actives (en période d'essai, avec abonnement ou explicitement activées)
    visible_companies = []
    for company in companies_with_catalogs:
        trial_status = company.get_trial_status()
        if trial_status['is_trial'] or trial_status['has_subscription'] or company.is_active:
            visible_companies.append(company.id)

    companies = Company.objects.filter(id__in=visible_companies)

    serializer = CompanySerializer(companies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def company_catalogs_in_zone(request, company_id):
    """
    Récupère les catalogues d'une entreprise spécifique qui sont diffusés dans la zone du client.
    Le client peut spécifier sa localisation par ville (city) ou par coordonnées (lat, lng).

    Paramètres:
    - company_id: ID de l'entreprise
    - city: Nom de la ville (optionnel)
    - lat: Latitude (optionnel, mais requis si lng est fourni)
    - lng: Longitude (optionnel, mais requis si lat est fourni)
    - radius: Rayon de recherche en km (optionnel, par défaut: 10km)
    """
    # Vérifier si l'entreprise existe
    company = get_object_or_404(Company, id=company_id)

    # Récupérer le statut d'essai de l'entreprise
    trial_status = company.get_trial_status()

    # Vérifier si l'entreprise est active (en période d'essai, avec abonnement ou explicitement activée)
    if not (trial_status['is_trial'] or trial_status['has_subscription'] or company.is_active):
        return Response(
            {"error": "Cette entreprise n'est pas active actuellement."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Vérifier si les catalogues de l'entreprise sont visibles
    if not company.are_catalogs_visible():
        return Response(
            {"error": "Les catalogues de cette entreprise ne sont pas disponibles actuellement."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Récupérer les paramètres de la requête
    city = request.query_params.get('city')
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km

    # Vérifier qu'au moins un des paramètres de localisation est fourni
    if not city and (not latitude or not longitude):
        return Response(
            {"error": "Vous devez fournir soit le paramètre 'city', soit les paramètres 'lat' et 'lng'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Initialiser la requête pour les zones de diffusion
    zones_query = DistributionZone.objects.all()

    # Filtrer par ville si spécifiée
    if city:
        zones_query = zones_query.filter(name__icontains=city)

    # Filtrer par coordonnées si spécifiées
    elif latitude and longitude:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculer les limites de la zone de recherche
        lat_min = latitude - (radius / 111.0)
        lat_max = latitude + (radius / 111.0)

        lng_factor = cos(radians(latitude)) * 111.0
        lng_min = longitude - (radius / lng_factor)
        lng_max = longitude + (radius / lng_factor)

        zones_query = zones_query.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max
        )

    # Récupérer les IDs des zones trouvées
    zone_ids = zones_query.values_list('id', flat=True)

    # Récupérer les catalogues de l'entreprise qui sont diffusés dans ces zones
    catalogs = Catalog.objects.filter(
        company=company,
        distribution_zones__id__in=zone_ids
    ).distinct().order_by('-created_at')

    serializer = CatalogSerializer(catalogs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_service_list(request):
    """
    Liste tous les services publics (mairies et pharmacies de garde)

    Paramètres optionnels:
    - type: Filtrer par type de service ('city_hall' pour les mairies, 'pharmacy' pour les pharmacies)
    - city: Filtrer par ville
    - lat: Latitude (optionnel, mais requis si lng est fourni)
    - lng: Longitude (optionnel, mais requis si lat est fourni)
    - radius: Rayon de recherche en km (optionnel, par défaut: 10km)
    """
    # Récupérer les paramètres de la requête
    service_type = request.query_params.get('type')
    city = request.query_params.get('city')
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km

    # Initialiser la requête
    services = PublicService.objects.all()

    # Filtrer par type si spécifié
    if service_type:
        if service_type in [PublicService.ServiceType.CITY_HALL, PublicService.ServiceType.PHARMACY]:
            services = services.filter(service_type=service_type)
        else:
            return Response(
                {"error": f"Type de service invalide. Valeurs acceptées: {PublicService.ServiceType.CITY_HALL}, {PublicService.ServiceType.PHARMACY}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Filtrer par ville si spécifiée
    if city:
        services = services.filter(city__icontains=city)

    # Filtrer par coordonnées si spécifiées
    if latitude and longitude:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            radius = float(radius)
        except ValueError:
            return Response(
                {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculer les limites de la zone de recherche
        lat_min = latitude - (radius / 111.0)
        lat_max = latitude + (radius / 111.0)

        lng_factor = cos(radians(latitude)) * 111.0
        lng_min = longitude - (radius / lng_factor)
        lng_max = longitude + (radius / lng_factor)

        services = services.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max
        )

    # Ordonner les résultats
    services = services.order_by('service_type', 'city', 'name')

    serializer = PublicServiceSerializer(services, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_service_detail(request, service_id):
    """
    Détails d'un service public spécifique
    """
    service = get_object_or_404(PublicService, id=service_id)
    serializer = PublicServiceSerializer(service)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_service_search_by_location(request):
    """
    Recherche des services publics par proximité géographique

    Paramètres:
    - lat: Latitude (requis)
    - lng: Longitude (requis)
    - radius: Rayon de recherche en km (optionnel, par défaut: 10km)
    - type: Filtrer par type de service ('city_hall' pour les mairies, 'pharmacy' pour les pharmacies) (optionnel)
    """
    # Récupérer les paramètres de la requête
    latitude = request.query_params.get('lat')
    longitude = request.query_params.get('lng')
    radius = request.query_params.get('radius', 10)  # Rayon par défaut: 10km
    service_type = request.query_params.get('type')

    if not latitude or not longitude:
        return Response(
            {"error": "Les paramètres 'lat' et 'lng' sont requis"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        radius = float(radius)
    except ValueError:
        return Response(
            {"error": "Les paramètres 'lat', 'lng' et 'radius' doivent être des nombres"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Récupérer tous les services qui ont des coordonnées
    services = PublicService.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    )

    # Filtrer par type si spécifié
    if service_type:
        if service_type in [PublicService.ServiceType.CITY_HALL, PublicService.ServiceType.PHARMACY]:
            services = services.filter(service_type=service_type)
        else:
            return Response(
                {"error": f"Type de service invalide. Valeurs acceptées: {PublicService.ServiceType.CITY_HALL}, {PublicService.ServiceType.PHARMACY}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Filtrer les services en fonction de la distance
    # 1 degré de latitude = environ 111 km
    lat_min = latitude - (radius / 111.0)
    lat_max = latitude + (radius / 111.0)

    # 1 degré de longitude = environ 111 km * cos(latitude)
    lng_factor = cos(radians(latitude)) * 111.0
    lng_min = longitude - (radius / lng_factor)
    lng_max = longitude + (radius / lng_factor)

    services = services.filter(
        latitude__gte=lat_min,
        latitude__lte=lat_max,
        longitude__gte=lng_min,
        longitude__lte=lng_max
    )

    serializer = PublicServiceSerializer(services, many=True)
    return Response(serializer.data)