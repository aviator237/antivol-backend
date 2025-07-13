
from rest_framework.serializers import ModelSerializer
 
from box.models import Box
from authentification.serializers import UserSerializer
 
class BoxSerializer(ModelSerializer):
    owner = UserSerializer(required=False, read_only=True, allow_null=True, label="Propriétaire", help_text="Le propriétaire de la boîte")
    
    class Meta:
        model = Box
        fields = ['id', 'mac_address', 'created_at', 'socket_id', 'last_updated', 'owner']


# comment faire en sorte que le champs owner soit non obligatoire lors de la creation de l'objet. ex: 