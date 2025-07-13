
from django.urls import path

from .views import *

app_name = "auth"
urlpatterns = [
    path("login", log_in, name="login"),
    path("register/<mac_address>/", register, name="register"),
    path("resent", resent, name="resent"),
    path("activate", activate, name="activate"),

    # Réinitialisation de mot de passe
    path("reset", reset, name="reset"),
    path("verify_reset_code/<uidb64>", verify_reset_code, name="verify_reset_code"),
    path("reset_pwd/<uidb64>/<token>", reset_pwd, name="reset_pwd"),
    path("new_password/<uidb64>", new_password, name="new_password"),

    path("logout", log_out, name="logout"),

    # Company authentication endpoints
    path("company/register", company_register, name="company_register"),
    path("company/create/<uid>", company_create, name="company_create"),
]
