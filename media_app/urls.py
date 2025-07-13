"""
URL configuration for media_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""






from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.conf.urls.static import static
from django.conf import settings

from box.views import BoxApiView, BoxViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Ici nous créons notre routeur
router = routers.SimpleRouter()
router.register('box', BoxViewSet, basename='box')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api-box/', include('box.urls')),
    path("auth/", include("authentification.urls")),
    path("account/", include("account.urls")),
    path("album/", include("album.urls")),
    path("pricing/", include("pricing.urls")),
    path("payments/", include("payments.urls")),
    path("company/", include("company.urls")),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('api/box/', BoxApiView.as_view()),
    path('', include(router.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Je veux qu'en soumettant le formulaire, la liste des numeros de telephone soit aussi envoyée dans la requete sous le champs phone_numbers et accessible par phone_numbers = request.POST.getlist('phone_numbers').