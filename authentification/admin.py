from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from authentification.models import Otp

class OtpAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "created_at")
 


class MyUserAdmin(UserAdmin):

    actions = ['supprimer_utilisateurs_selectionnes', 
               'desactiver_utilisateurs_selectionnes', 
               'activer_utilisateurs_selectionnes',
               ]
    save_on_top = True

    def desactiver_utilisateurs_selectionnes(self, request, queryset):
        """Désactive les utilisateurs sélectionnés."""
        queryset.update(is_active=False)
        self.message_user(request, _("Les utilisateurs sélectionnés ont été désactivés."))

    def activer_utilisateurs_selectionnes(self, request, queryset):
        """Active les utilisateurs sélectionnés."""
        queryset.update(is_active=True)
        self.message_user(request, _("Les utilisateurs sélectionnés ont été activés."))

    desactiver_utilisateurs_selectionnes.short_description = _("Désactiver les utilisateurs sélectionnés")
    activer_utilisateurs_selectionnes.short_description = _("Activer les utilisateurs sélectionnés")



admin.site.unregister(User)
admin.site.register(Otp, OtpAdmin)
admin.site.register(User, MyUserAdmin)
