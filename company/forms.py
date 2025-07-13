from django import forms
from .models import Catalog, Company, DistributionZone, Category


class DistributionZoneForm(forms.ModelForm):
    """Formulaire pour la création et la modification de zones de diffusion"""

    class Meta:
        model = DistributionZone
        fields = ['name', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la ville'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': 'any'}),
        }


class CatalogForm(forms.ModelForm):
    """Formulaire pour la création et la modification de catalogues"""
    distribution_zones = forms.ModelMultipleChoiceField(
        queryset=DistributionZone.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'distribution-zones-checkbox'}),
        required=True,
        label="Zones de diffusion"
    )

    class Meta:
        model = Catalog
        fields = ['title', 'file', 'distribution_zones']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du catalogue'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super(CatalogForm, self).__init__(*args, **kwargs)

        if company:
            # Filtrer les zones de diffusion par entreprise
            self.fields['distribution_zones'].queryset = DistributionZone.objects.filter(company=company)
        elif self.instance and self.instance.pk:
            # Si on modifie un catalogue existant
            self.fields['distribution_zones'].queryset = DistributionZone.objects.filter(company=self.instance.company)

    def clean_file(self):
        """Valider que le fichier est un PDF"""
        file = self.cleaned_data.get('file')
        if file:
            # Vérifier l'extension du fichier
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError("Seuls les fichiers PDF sont acceptés.")
            # Vérifier la taille du fichier (max 10 Mo)
            if file.size > 10 * 1024 * 1024:  # 10 Mo en octets
                raise forms.ValidationError("La taille du fichier ne doit pas dépasser 10 Mo.")
        return file

    def clean_distribution_zones(self):
        """Valider qu'au moins une zone de diffusion est sélectionnée"""
        zones = self.cleaned_data.get('distribution_zones')
        if not zones or len(zones) == 0:
            raise forms.ValidationError("Vous devez sélectionner au moins une zone de diffusion.")
        return zones


# class CompanyCreateForm(forms.ModelForm):
#     """Formulaire pour la création d'une entreprise"""

#     # Champs cachés pour stocker les coordonnées GPS
#     latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
#     longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

#     # Champ pour la recherche d'adresse
#     address_search = forms.CharField(
#         required=False,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'Rechercher une adresse...',
#             'id': 'address-search'
#         }),
#         label="Recherche d'adresse"
#     )

#     class Meta:
#         model = Company
#         fields = ['name', 'category', 'address', 'postal_code', 'city', 'siret',
#                  'opening_hour', 'closing_hour', 'latitude', 'longitude']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse', 'id': 'address-field'}),
#             'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal', 'id': 'postal-code-field'}),
#             'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville', 'id': 'city-field'}),
#             'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro SIRET'}),
#             'opening_hour': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
#             'closing_hour': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         latitude = cleaned_data.get('latitude')
#         longitude = cleaned_data.get('longitude')

#         if not latitude or not longitude:
#             raise forms.ValidationError("Veuillez définir l'emplacement de votre entreprise sur la carte ou en utilisant la recherche d'adresse.")

#         # Vérifier que le SIRET est unique
#         siret = cleaned_data.get('siret')
#         if siret and Company.objects.filter(siret=siret).exists():
#             self.add_error('siret', "Une entreprise avec ce numéro SIRET existe déjà.")

#         return cleaned_data


class CompanyUpdateForm(forms.ModelForm):
    """Formulaire pour la modification des informations de l'entreprise"""

    # Champs cachés pour stocker les coordonnées GPS
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

    # Champ pour la recherche d'adresse
    address_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher une adresse...',
            'id': 'address-search'
        }),
        label="Recherche d'adresse"
    )

    class Meta:
        model = Company
        fields = ['name', 'category', 'address', 'postal_code', 'city', 'siret',
                 'opening_hour', 'closing_hour', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adresse', 'id': 'address-field'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code postal', 'id': 'postal-code-field'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville', 'id': 'city-field'}),
            'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro SIRET'}),
            'opening_hour': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'closing_hour': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if not latitude or not longitude:
            raise forms.ValidationError("Veuillez définir l'emplacement de votre entreprise sur la carte ou en utilisant la recherche d'adresse.")

        # Vérifier que le SIRET est unique (sauf pour l'entreprise actuelle)
        siret = cleaned_data.get('siret')
        if siret:
            existing = Company.objects.filter(siret=siret).exclude(pk=self.instance.pk)
            if existing.exists():
                self.add_error('siret', "Une entreprise avec ce numéro SIRET existe déjà.")

        return cleaned_data
