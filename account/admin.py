from django.contrib import admin

from .models import Profil


class ProfilAdmin(admin.ModelAdmin):

    list_display = ("owner", "plan")
    search_fields = ["owner__username", "plan__name"]
    search_help_text = "Rechercher un profil à l'aide du nom de l'utilisateur ou du nom du plan associé"
    readonly_fields = ["stripe_customer_id"]
    list_filter = ["plan"]

admin.site.register(Profil, ProfilAdmin)


