from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Phone, UnlockAttempt, IntrusionPhoto

class UnlockAttemptInline(admin.TabularInline):
    """Inline pour afficher les tentatives de déverrouillage"""
    model = UnlockAttempt
    extra = 0
    readonly_fields = ('timestamp', 'is_suspicious')
    fields = ('attempt_type', 'result', 'timestamp', 'latitude', 'longitude', 'is_suspicious')

    def is_suspicious(self, obj):
        return obj.is_suspicious
    is_suspicious.boolean = True
    is_suspicious.short_description = 'Suspect'

class IntrusionPhotoInline(admin.TabularInline):
    """Inline pour afficher les photos d'intrusion"""
    model = IntrusionPhoto
    extra = 0
    readonly_fields = ('timestamp', 'file_size', 'photo_preview')
    fields = ('photo_preview', 'camera_type', 'timestamp', 'file_size')

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.photo.url
            )
        return "Pas de photo"
    photo_preview.short_description = 'Aperçu'

@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    """Admin pour les téléphones"""
    list_display = (
        'name', 'user', 'brand', 'model', 'status', 'is_primary',
        'is_online_display', 'last_seen', 'unlock_attempts_count'
    )
    list_filter = ('status', 'os_type', 'is_primary', 'photo_capture_enabled', 'created_at')
    search_fields = ('name', 'user__username', 'user__email', 'brand', 'model', 'imei')
    readonly_fields = ('device_id', 'created_at', 'updated_at', 'last_seen', 'is_online_display')

    fieldsets = (
        ('Informations de base', {
            'fields': ('user', 'name', 'device_id', 'status', 'is_primary')
        }),
        ('Informations techniques', {
            'fields': ('brand', 'model', 'os_type', 'os_version', 'app_version')
        }),
        ('Identifiants', {
            'fields': ('imei', 'serial_number'),
            'classes': ('collapse',)
        }),
        ('Paramètres de sécurité', {
            'fields': (
                'unlock_attempts_threshold',
                'photo_capture_enabled',
                'location_tracking_enabled'
            )
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'last_seen', 'is_online_display'),
            'classes': ('collapse',)
        }),
    )

    inlines = [UnlockAttemptInline]

    def is_online_display(self, obj):
        """Affiche le statut en ligne avec une couleur"""
        if obj.is_online:
            return format_html(
                '<span style="color: green; font-weight: bold;">● En ligne</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">● Hors ligne</span>'
            )
    is_online_display.short_description = 'Statut'

    def unlock_attempts_count(self, obj):
        """Compte le nombre de tentatives de déverrouillage"""
        return obj.unlock_attempts.count()
    unlock_attempts_count.short_description = 'Tentatives'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(UnlockAttempt)
class UnlockAttemptAdmin(admin.ModelAdmin):
    """Admin pour les tentatives de déverrouillage"""
    list_display = (
        'phone', 'attempt_type', 'result', 'timestamp',
        'is_suspicious', 'has_location', 'photos_count'
    )
    list_filter = ('result', 'attempt_type', 'timestamp', 'phone__user')
    search_fields = ('phone__name', 'phone__user__username', 'ip_address')
    readonly_fields = ('timestamp', 'is_suspicious')

    fieldsets = (
        ('Informations de base', {
            'fields': ('phone', 'attempt_type', 'result', 'timestamp')
        }),
        ('Localisation', {
            'fields': ('latitude', 'longitude', 'location_accuracy'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    inlines = [IntrusionPhotoInline]

    def is_suspicious(self, obj):
        return obj.is_suspicious
    is_suspicious.boolean = True
    is_suspicious.short_description = 'Suspect'

    def has_location(self, obj):
        return obj.latitude is not None and obj.longitude is not None
    has_location.boolean = True
    has_location.short_description = 'Localisation'

    def photos_count(self, obj):
        return obj.photos.count()
    photos_count.short_description = 'Photos'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('phone', 'phone__user')

@admin.register(IntrusionPhoto)
class IntrusionPhotoAdmin(admin.ModelAdmin):
    """Admin pour les photos d'intrusion"""
    list_display = (
        'unlock_attempt', 'camera_type', 'timestamp',
        'file_size_display', 'photo_preview'
    )
    list_filter = ('camera_type', 'timestamp', 'unlock_attempt__phone__user')
    search_fields = ('unlock_attempt__phone__name', 'unlock_attempt__phone__user__username')
    readonly_fields = ('timestamp', 'file_size', 'photo_preview_large')

    fieldsets = (
        ('Informations de base', {
            'fields': ('unlock_attempt', 'photo', 'camera_type')
        }),
        ('Métadonnées', {
            'fields': ('timestamp', 'file_size', 'exif_data'),
            'classes': ('collapse',)
        }),
        ('Aperçu', {
            'fields': ('photo_preview_large',)
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                obj.photo.url
            )
        return "Pas de photo"
    photo_preview.short_description = 'Aperçu'

    def photo_preview_large(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px;" />',
                obj.photo.url
            )
        return "Pas de photo"
    photo_preview_large.short_description = 'Photo'

    def file_size_display(self, obj):
        """Affiche la taille du fichier en format lisible"""
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "N/A"
    file_size_display.short_description = 'Taille'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'unlock_attempt', 'unlock_attempt__phone', 'unlock_attempt__phone__user'
        )
