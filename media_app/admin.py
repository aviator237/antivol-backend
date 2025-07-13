from django.contrib import admin
from django.contrib.auth.models import User


class MyAdminSite(admin.AdminSite):
    site_header = "Administration du serveur photo"
    
# # from django.core.mail import send_mass_mail

# # def send_welcome_email(request, queryset):
# #     for user in queryset:
# #         send_mass_mail(subject='Bienvenue sur notre site!',
# #                        message='Salut {}! Merci de vous être inscrit sur notre site.'.format(user.username),
# #                        from_email='noreply@example.com',
# #                        to_list=[user.email])

# # class UserAdmin(admin.ModelAdmin):
# #     list_display = ['username', 'email', 'is_active', 'is_staff']
# #     actions = [send_welcome_email, admin.site.empty_trash]

# # admin.site.register(User, UserAdmin)
# # from django.contrib import admin
# # from .models import MyUserAdmin

# # admin.site.register(User, MyUserAdmin)





# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.models import User
# from django.utils.translation import gettext_lazy as _
# from django.shortcuts import redirect

# class MyUserAdmin(UserAdmin):
#     actions = ['supprimer_utilisateurs_selectionnes', 'desactiver_utilisateurs_selectionnes', 'activer_utilisateurs_selectionnes']

#     def supprimer_utilisateurs_selectionnes(self, request, queryset):
#         """Supprime les utilisateurs sélectionnés."""
#         queryset.delete()
#         self.message_user(request, _("Les utilisateurs sélectionnés ont été supprimés."))

#     def desactiver_utilisateurs_selectionnes(self, request, queryset):
#         """Désactive les utilisateurs sélectionnés."""
#         queryset.update(is_active=False)
#         self.message_user(request, _("Les utilisateurs sélectionnés ont été désactivés."))

#     def activer_utilisateurs_selectionnes(self, request, queryset):
#         """Active les utilisateurs sélectionnés."""
#         queryset.update(is_active=True)
#         self.message_user(request, _("Les utilisateurs sélectionnés ont été activés."))

#     supprimer_utilisateurs_selectionnes.short_description = _("Supprimer les utilisateurs sélectionnés")
#     desactiver_utilisateurs_selectionnes.short_description = _("Désactiver les utilisateurs sélectionnés")
#     activer_utilisateurs_selectionnes.short_description = _("Activer les utilisateurs sélectionnés")



# # from django.contrib import admin
# # from django.contrib.auth.admin import UserAdmin
# # from .models import UserProfile  # Remplacez par votre modèle de profil
# from .admin import MyUserAdmin

# admin.site.unregister(User)
# admin.site.register(User, MyUserAdmin)
# scp -r "/Users/user/Desktop/MEDIA PROJET/media_server/media_app/.env" root@212.227.52.188:media_server/meda_app
# cd media_server/meda_app
# python3 -m venv venv
# source venv/bin/activate
# sudo apt-get install python3-dev default-libmysqlclient-dev build-essential pkg-config
# git ls-tree HEAD afficher les fichiers traqués
# ps aux | grep -i apt
# sudo kill <process_id>