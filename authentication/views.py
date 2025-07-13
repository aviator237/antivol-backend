from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    EmailVerificationSerializer,
    UserProfileSerializer
)
from .models import EmailVerification

class RegisterView(generics.CreateAPIView):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Envoie l'email de vérification
        self.send_verification_email(user)

        return Response({
            'message': 'Compte créé avec succès. Veuillez vérifier votre email.',
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)

    def send_verification_email(self, user):
        """Envoie l'email de vérification"""
        try:
            verification = user.email_verification
            verification_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/verify-email/{verification.verification_token}"

            subject = 'Vérifiez votre adresse email - Antivol'

            # Template HTML
            html_message = render_to_string('authentication/verification_email.html', {
                'user': user,
                'verification_url': verification_url,
                'verification_code': verification.verification_code,
            })

            # Version texte simple
            plain_message = f"""
Bonjour {user.first_name},

Merci de vous être inscrit sur Antivol. Pour activer votre compte, vous avez deux options :

1. Cliquer sur ce lien : {verification_url}

2. Ou saisir ce code dans l'application : {verification.verification_code}

Si vous n'avez pas créé ce compte, vous pouvez ignorer cet email.

Cordialement,
L'équipe Antivol
            """

            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email: {e}")

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Vue pour la connexion d'un utilisateur"""
    serializer = UserLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']

    # Génère les tokens JWT
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    # Vérifie si l'email est vérifié
    email_verified = False
    try:
        email_verified = user.email_verification.is_verified
    except EmailVerification.DoesNotExist:
        pass

    return Response({
        'message': 'Connexion réussie',
        'access_token': str(access_token),
        'refresh_token': str(refresh),
        'user': {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'email_verified': email_verified,
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_view(request):
    """Vue pour vérifier l'email avec le token ou le code"""
    serializer = EmailVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    verification = serializer.validated_data['verification']
    verification.verify()

    return Response({
        'message': 'Email vérifié avec succès. Veuillez vous connecter pour accéder à l\'application.',
        'user': {
            'id': verification.user.id,
            'first_name': verification.user.first_name,
            'last_name': verification.user.last_name,
            'email': verification.user.email,
            'email_verified': True,
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """Renvoie l'email de vérification"""
    email = request.data.get('email')

    if not email:
        return Response({
            'error': 'Email requis'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        verification = user.email_verification

        if verification.is_verified:
            return Response({
                'message': 'Cet email est déjà vérifié'
            }, status=status.HTTP_200_OK)

        # Régénère un nouveau code et renvoie l'email
        verification.regenerate_code()
        register_view = RegisterView()
        register_view.send_verification_email(user)

        return Response({
            'message': 'Email de vérification renvoyé'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'error': 'Aucun utilisateur trouvé avec cet email'
        }, status=status.HTTP_404_NOT_FOUND)
    except EmailVerification.DoesNotExist:
        return Response({
            'error': 'Aucune vérification d\'email trouvée pour cet utilisateur'
        }, status=status.HTTP_404_NOT_FOUND)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Vue pour récupérer et mettre à jour le profil utilisateur"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
