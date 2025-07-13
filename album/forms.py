from django import forms
from .models import Album


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['name', 
                #   'owner'
                  ]
        labels = {
            'name': "Nom de l'album photo",
            # 'owner': 'Propriétaire',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            # 'owner': forms.Select(attrs={'class': 'form-control'}),
        }