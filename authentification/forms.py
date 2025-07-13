from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from company.models import Company, Category
from account.models import UserRole
import re
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Mot de passe'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirmer le mot de passe'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Téléphone (Avec indicatif du pays)'}))
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'light',
                'data-size': 'normal',
                'class': 'recaptcha-container',
            }
        ),
        label="Vérification de sécurité"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'password', 'password1']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nom'}),
            'last_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Prénom'}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not re.match(r'^\+?1?\d{9,15}$', phone_number):
            raise ValidationError("Le numéro de téléphone doit être au format international (9 à 15 chiffres).")
        if User.objects.filter(username=phone_number).exists():
            raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone_number

    def clean_password1(self):
        password = self.cleaned_data.get('password')
        password1 = self.cleaned_data.get('password1')
        if password and password1 and password != password1:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return password1

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        return password


class CompanyOwnerRegistrationForm(UserRegistrationForm):
    """Form for registering company owners. Inherits from UserRegistrationForm."""
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Email'}))
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'light',
                'data-size': 'normal',
                'class': 'recaptcha-container',
            }
        ),
        label="Vérification de sécurité"
    )

    class Meta(UserRegistrationForm.Meta):
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'password1']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['phone_number']
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

            # Create or update profile with company owner role
            from account.models import Profil
            profile, created = Profil.objects.get_or_create(owner=user)
            profile.role = UserRole.COMPANY_OWNER
            profile.save()

        return user


class CombinedCompanyRegistrationForm(forms.Form):
    """
    Form that combines user registration and company creation in one step.
    """
    # User information fields
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nom'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Prénom'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Email'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Téléphone (Avec indicatif du pays)'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Mot de passe'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirmer le mot de passe'}))

    # Company information fields
    company_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nom de l\'entreprise'}))
    company_siret = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Numéro SIRET'}))
    company_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={'class': 'input catagory-select'}),
        empty_label="Sélectionnez une catégorie"
    )

    # Address fields
    address_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Rechercher une adresse...',
            'id': 'address-search'
        }),
        label="Recherche d'adresse"
    )
    company_address = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Adresse', 'id': 'address-field'}))
    company_postal_code = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Code postal', 'id': 'postal-code-field'}))
    company_city = forms.CharField(widget=forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ville', 'id': 'city-field'}))

    # Hidden fields for coordinates
    company_latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
    company_longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

    # Business hours
    company_opening_hour = forms.TimeField(
        initial='08:00',
        widget=forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
        label="Heure d'ouverture"
    )
    company_closing_hour = forms.TimeField(
        initial='16:00',
        widget=forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
        label="Heure de fermeture"
    )

    # Captcha
    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-theme': 'light',
                'data-size': 'normal',
                'class': 'recaptcha-container',
            }
        ),
        label="Vérification de sécurité"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not re.match(r'^\+?1?\d{9,15}$', phone_number):
            raise ValidationError("Le numéro de téléphone doit être au format international (9 à 15 chiffres).")
        if User.objects.filter(username=phone_number).exists():
            raise ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone_number

    def clean_password1(self):
        password = self.cleaned_data.get('password')
        password1 = self.cleaned_data.get('password1')
        if password and password1 and password != password1:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return password1

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre majuscule.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Le mot de passe doit contenir au moins une lettre minuscule.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial.")
        return password

    def clean_company_siret(self):
        siret = self.cleaned_data.get('company_siret')
        if not re.match(r'^\d{14}$', siret):
            raise ValidationError("Le numéro SIRET doit contenir exactement 14 chiffres.")
        if Company.objects.filter(siret=siret).exists():
            raise ValidationError("Ce numéro SIRET est déjà utilisé.")
        return siret

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('company_latitude')
        longitude = cleaned_data.get('company_longitude')

        if not latitude or not longitude:
            raise ValidationError("Veuillez définir l'emplacement de votre entreprise sur la carte ou en utilisant la recherche d'adresse.")

        return cleaned_data

    def save(self):
        """
        Save both the user and company in one transaction.
        """
        # Create the user
        user = User.objects.create_user(
            username=self.cleaned_data['phone_number'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.is_active = False  # User needs to activate account via email
        user.save()

        # Create the company
        company = Company.objects.create(
            name=self.cleaned_data['company_name'],
            category=self.cleaned_data['company_category'],
            address=self.cleaned_data['company_address'],
            postal_code=self.cleaned_data['company_postal_code'],
            city=self.cleaned_data['company_city'],
            siret=self.cleaned_data['company_siret'],
            latitude=self.cleaned_data['company_latitude'],
            longitude=self.cleaned_data['company_longitude'],
            opening_hour=self.cleaned_data['company_opening_hour'],
            closing_hour=self.cleaned_data['company_closing_hour']
        )

        # Create or update profile with company owner role and link to company
        from account.models import Profil
        profile = Profil.objects.get_or_create(owner=user)[0]
        profile.role = UserRole.COMPANY_OWNER
        profile.company = company
        profile.save()

        return user


class CompanyCreationForm(forms.ModelForm):
    """Form for creating a company."""

    # Champs cachés pour stocker les coordonnées GPS
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=True)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=True)

    # Champ pour la recherche d'adresse
    address_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Rechercher une adresse...',
            'id': 'address-search'
        }),
        label="Recherche d'adresse"
    )

    # Champs pour les heures d'ouverture et de fermeture avec valeurs par défaut
    opening_hour = forms.TimeField(
        initial='08:00',
        widget=forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
        label="Heure d'ouverture"
    )
    closing_hour = forms.TimeField(
        initial='16:00',
        widget=forms.TimeInput(attrs={'class': 'input', 'type': 'time'}),
        label="Heure de fermeture"
    )

    class Meta:
        model = Company
        fields = ['name', 'address', 'postal_code', 'city', 'siret', 'category',
                 'opening_hour', 'closing_hour', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nom de l\'entreprise'}),
            'address': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Adresse', 'id': 'address-field'}),
            'postal_code': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Code postal', 'id': 'postal-code-field'}),
            'city': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ville', 'id': 'city-field'}),
            'siret': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Numéro SIRET'}),
            'category': forms.Select(attrs={'class': 'input catagory-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if not latitude or not longitude:
            raise ValidationError("Veuillez définir l'emplacement de votre entreprise sur la carte ou en utilisant la recherche d'adresse.")

        return cleaned_data

    def clean_siret(self):
        siret = self.cleaned_data.get('siret')
        if not re.match(r'^\d{14}$', siret):
            raise ValidationError("Le numéro SIRET doit contenir exactement 14 chiffres.")
        if Company.objects.filter(siret=siret).exists():
            raise ValidationError("Ce numéro SIRET est déjà utilisé.")
        return siret
