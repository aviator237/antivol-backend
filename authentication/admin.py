from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import EmailVerification

class EmailVerificationInline(admin.StackedInline):
    """Inline pour afficher la vérification d'email dans l'admin utilisateur"""
    model = EmailVerification
    can_delete = False
    verbose_name_plural = "Vérification d'email"
    readonly_fields = ('verification_token', 'created_at', 'verified_at')

class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour les utilisateurs"""
    inlines = (EmailVerificationInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_email_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')

    def get_email_verified(self, obj):
        """Affiche le statut de vérification de l'email"""
        try:
            return obj.email_verification.is_verified
        except EmailVerification.DoesNotExist:
            return False
    get_email_verified.boolean = True
    get_email_verified.short_description = 'Email vérifié'

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Admin pour les vérifications d'email"""
    list_display = ('user', 'is_verified', 'created_at', 'verified_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('verification_token', 'created_at', 'verified_at')

    def has_add_permission(self, request):
        """Empêche la création manuelle de vérifications"""
        return False

# Désenregistre l'admin utilisateur par défaut et enregistre le nôtre
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
