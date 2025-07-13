from django.contrib import admin

from .models import Box
from django.utils.html import format_html


class BoxAdmin(admin.ModelAdmin):

    # readonly_fields = ["socket_id", "created_at", "last_updated"]
    list_display = ("mac_address", "is_connected", "owner", "created_at", "last_updated")
    search_fields = ["mac_address", "owner"]
    search_help_text = "Rechercher un appareil à l'aide de son adresse mac ou du nom de son propriétaire"
    list_filter = ["is_connected"]
    readonly_fields = ["socket_id", "is_connected"]






admin.site.register(Box, BoxAdmin)