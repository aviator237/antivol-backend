from django.urls import path
from . import views

app_name = "payments"
urlpatterns = [
    path('checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
]