from django.contrib import admin
from django.contrib.auth.models import User


class MyAdminSite(admin.AdminSite):
    site_header = "Administration Antivol"
    