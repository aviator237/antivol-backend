from django.urls import path
from . import views
from . import api_views
from . import import_views

app_name = "company"
urlpatterns = [
    # URL pour le tableau de bord de l'entreprise
    path('', views.company_dashboard, name='dashboard'),

    # URL pour la création d'entreprise
    path('create/', views.company_create, name='company_create'),

    # URLs pour les informations de l'entreprise
    path('info/', views.company_detail, name='company_detail'),
    path('info/update/', views.company_update, name='company_update'),

    # URLs pour les catalogues
    path('catalogs/', views.catalog_list, name='catalog_list'),
    path('catalogs/create/', views.catalog_create, name='catalog_create'),
    path('catalogs/<int:catalog_id>/', views.catalog_detail, name='catalog_detail'),
    path('catalogs/<int:catalog_id>/update/', views.catalog_update, name='catalog_update'),
    path('catalogs/<int:catalog_id>/delete/', views.catalog_delete, name='catalog_delete'),
    path('catalogs/<int:catalog_id>/download/', views.catalog_download, name='catalog_download'),

    # URLs pour les zones de diffusion
    path('zones/', views.zone_list, name='zone_list'),
    path('zones/create/', views.zone_create, name='zone_create'),
    path('zones/<int:zone_id>/', views.zone_detail, name='zone_detail'),
    path('zones/<int:zone_id>/update/', views.zone_update, name='zone_update'),
    path('zones/<int:zone_id>/delete/', views.zone_delete, name='zone_delete'),

    # API endpoints
    path('api/categories/', api_views.category_list, name='api_category_list'),
    path('api/companies/', api_views.company_list, name='api_company_list'),
    path('api/companies/category/<int:category_id>/', api_views.company_list_by_category, name='api_company_list_by_category'),
    path('api/companies/<int:company_id>/', api_views.company_detail, name='api_company_detail'),
    path('api/companies/search/location/', api_views.company_search_by_location, name='api_company_search_by_location'),
    path('api/catalogs/company/<int:company_id>/', api_views.catalog_list_by_company, name='api_catalog_list_by_company'),
    path('api/catalogs/<int:catalog_id>/', api_views.catalog_detail, name='api_catalog_detail'),

    # API endpoints pour les zones de diffusion
    path('api/zones/', api_views.distribution_zone_list, name='api_zone_list'),
    path('api/zones/<int:zone_id>/', api_views.distribution_zone_detail, name='api_zone_detail'),
    path('api/zones/company/<int:company_id>/', api_views.distribution_zone_list_by_company, name='api_zone_list_by_company'),
    path('api/catalogs/zone/<int:zone_id>/', api_views.catalog_list_by_zone, name='api_catalog_list_by_zone'),
    path('api/zones/search/location/', api_views.distribution_zone_search_by_location, name='api_zone_search_by_location'),

    # Nouveaux API endpoints pour la recherche par localisation
    path('api/companies/in-zone/', api_views.companies_with_catalogs_in_zone, name='api_companies_with_catalogs_in_zone'),
    path('api/companies/<int:company_id>/catalogs/in-zone/', api_views.company_catalogs_in_zone, name='api_company_catalogs_in_zone'),

    # API endpoints pour les services publics (mairies et pharmacies de garde)
    path('api/public-services/', api_views.public_service_list, name='api_public_service_list'),
    path('api/public-services/<int:service_id>/', api_views.public_service_detail, name='api_public_service_detail'),
    path('api/public-services/search/location/', api_views.public_service_search_by_location, name='api_public_service_search_by_location'),

    # URL publique pour voir tous les catalogues
    path('public/catalogs/', views.public_catalog_list, name='public_catalog_list'),

    # Documentation API
    path('api/docs/', views.api_documentation, name='api_documentation'),

    # Data import URLs (superadmin only)
    path('admin/import/', import_views.import_dashboard, name='import_dashboard'),
    path('admin/import/mairies/', import_views.import_mairies, name='import_mairies'),
    path('admin/import/pharmacies-1/', import_views.import_pharmacies_1, name='import_pharmacies_1'),
    path('admin/import/pharmacies-2/', import_views.import_pharmacies_2, name='import_pharmacies_2'),
    path('admin/import/pharmacies-3/', import_views.import_pharmacies_3, name='import_pharmacies_3'),
]
