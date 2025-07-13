from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Company, Category, Catalog, PublicService, DistributionZone

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'city', 'postal_code', 'siret')
    search_fields = ('name', 'city', 'postal_code', 'siret')
    list_filter = ('category', 'city')
    autocomplete_fields = ['category']


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'publisher', 'created_at', 'updated_at')
    search_fields = ('title', 'company__name', 'publisher__username')
    list_filter = ('company', 'created_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['company', 'publisher']


@admin.register(PublicService)
class PublicServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type_display', 'city', 'postal_code', 'phone', 'map_link')
    search_fields = ('name', 'city', 'postal_code', 'phone', 'email')
    list_filter = ('service_type', 'city')
    readonly_fields = ('latitude', 'longitude', 'geocoding_preview')
    fieldsets = (
        ('Informations générales', {
            'fields': ('service_type', 'name')
        }),
        ('Localisation', {
            'fields': ('address', 'postal_code', 'city', 'geocoding_preview', 'latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Horaires', {
            'fields': ('opening_hour', 'closing_hour'),
            'classes': ('collapse',),
            'description': 'Horaires d\'ouverture et de fermeture (par défaut: 19h00-09h00)'
        }),
        ('Informations supplémentaires', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def service_type_display(self, obj):
        """Affiche le type de service avec une couleur différente selon le type"""
        if obj.service_type == PublicService.ServiceType.CITY_HALL:
            return format_html('<span style="color: #0066cc; font-weight: bold;">Mairie</span>')
        elif obj.service_type == PublicService.ServiceType.PHARMACY:
            return format_html('<span style="color: #009900; font-weight: bold;">Pharmacie</span>')
        return obj.get_service_type_display()
    service_type_display.short_description = 'Type de service'

    def map_link(self, obj):
        """Affiche un lien vers Google Maps pour visualiser l'emplacement"""
        if obj.latitude and obj.longitude:
            url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">Voir sur la carte</a>', url)
        elif obj.address:
            return format_html('<a href="{}" target="_blank">Rechercher sur la carte</a>', obj.get_google_maps_url())
        return "Adresse non définie"
    map_link.short_description = 'Carte'

    def geocoding_preview(self, obj):
        """Affiche une prévisualisation de la géolocalisation"""
        if obj.latitude and obj.longitude:
            return format_html(
                '<div style="margin-top: 10px; margin-bottom: 10px;">'
                '<p style="margin-bottom: 5px;">Coordonnées actuelles: <strong>{}, {}</strong></p>'
                '<p style="color: #666; font-size: 0.9em;">Les coordonnées seront automatiquement mises à jour lors de la sauvegarde si l\'adresse est modifiée.</p>'
                '<iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" '
                'src="https://www.openstreetmap.org/export/embed.html?bbox={}%2C{}%2C{}%2C{}&amp;layer=mapnik&amp;marker={}%2C{}" '
                'style="border: 1px solid #ddd; border-radius: 4px;"></iframe>'
                '</div>',
                obj.latitude, obj.longitude,
                obj.longitude - 0.01, obj.latitude - 0.01, obj.longitude + 0.01, obj.latitude + 0.01,
                obj.latitude, obj.longitude
            )
        elif obj.address:
            return format_html(
                '<p style="color: #666;">'
                'Entrez une adresse et sauvegardez pour obtenir automatiquement les coordonnées GPS.'
                '</p>'
            )
        return "Aucune adresse définie"
    geocoding_preview.short_description = "Aperçu de la localisation"

    def save_model(self, request, obj, form, change):
        """
        Surcharge de la méthode de sauvegarde pour ajouter un message
        indiquant que les coordonnées seront mises à jour automatiquement.
        """
        super().save_model(request, obj, form, change)
        if obj.address and (not obj.latitude or not obj.longitude):
            self.message_user(
                request,
                "Les coordonnées GPS seront calculées automatiquement à partir de l'adresse.",
                level=messages.INFO
            )


@admin.register(DistributionZone)
class DistributionZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'latitude', 'longitude', 'created_at', 'map_link')
    search_fields = ('name', 'company__name')
    list_filter = ('company', 'created_at')
    autocomplete_fields = ['company']
    readonly_fields = ('geocoding_preview',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'company')
        }),
        ('Coordonnées géographiques', {
            'fields': ('latitude', 'longitude', 'geocoding_preview')
        }),
    )

    def map_link(self, obj):
        """Affiche un lien vers Google Maps pour visualiser l'emplacement"""
        if obj.latitude and obj.longitude:
            url = f"https://www.google.com/maps?q={obj.latitude},{obj.longitude}"
            return format_html('<a href="{}" target="_blank">Voir sur la carte</a>', url)
        return "Coordonnées non définies"
    map_link.short_description = 'Carte'

    def geocoding_preview(self, obj):
        """Affiche une prévisualisation de la géolocalisation"""
        if obj.latitude and obj.longitude:
            return format_html(
                '<div style="margin-top: 10px; margin-bottom: 10px;">'
                '<p style="margin-bottom: 5px;">Coordonnées: <strong>{}, {}</strong></p>'
                '<iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" '
                'src="https://www.openstreetmap.org/export/embed.html?bbox={}%2C{}%2C{}%2C{}&amp;layer=mapnik&amp;marker={}%2C{}" '
                'style="border: 1px solid #ddd; border-radius: 4px;"></iframe>'
                '</div>',
                obj.latitude, obj.longitude,
                obj.longitude - 0.01, obj.latitude - 0.01, obj.longitude + 0.01, obj.latitude + 0.01,
                obj.latitude, obj.longitude
            )
        return "Aucune coordonnée définie"
    geocoding_preview.short_description = "Aperçu de la localisation"
