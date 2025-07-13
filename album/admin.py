from django.contrib import admin

from .models import *
from django.utils.html import format_html

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 2  # Nombre de formulaires de photos supplémentaires à afficher


class AlbumAdmin(admin.ModelAdmin):

    # inlines = [PhotoInline]

    list_display = ("name", "owner", "created_at", "last_updated")
    list_filter = ["owner"]
    search_fields = ["name", "owner__username"]
    search_help_text = "Rechercher un album à l'aide de son nom ou du nom de son propriétaire"



class PhotoAdmin(admin.ModelAdmin):
    def illustration_img(self, obj):
        try:
            obj.file.url
            return format_html('<img src="{}" style="max-width:100px; max-height:100px"/>'.format(obj.file.url))
        except:
                return format_html("<div style='width:100px; height:100px; background-color: #121212'></div>")


    list_display = ("album", "owner", "created_at", 'illustration_img')
    search_fields = ["album__name", "owner__username"]
    search_help_text = "Rechercher une photo à l'aide du nom de l'album ou du nom de son propriétaire"
    list_filter = ["album", "owner"]

class SharedAlbumAdmin(admin.ModelAdmin):

    # list_select_related = ["album"]

    list_display = ("album", "album__owner", "shared_with", "status", "created_at", 'last_updated')
    list_filter = ["album", "album__owner", "shared_with"]
    search_fields = ["album__name", "shared_with__username"]
    
    search_help_text = "Rechercher un album à l'aide de son nom ou du nom de son propriétaire"







admin.site.register(SharedAlbum, SharedAlbumAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Photo, PhotoAdmin)