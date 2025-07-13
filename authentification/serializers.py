from rest_framework.serializers import ModelSerializer
from django.contrib.auth.models import User
from box.models import Box

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_active', 'date_joined', 'last_login']  # Ajoutez d'autres champs si nécessaire
