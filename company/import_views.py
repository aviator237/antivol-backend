import os
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from .data_import import (
    import_mairies_data,
    import_pharmacies_1_data,
    import_pharmacies_2_data,
    import_pharmacies_3_data,
    run_import_in_thread
)

logger = logging.getLogger(__name__)

def is_superuser(user):
    """
    Check if the user is a superuser
    """
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser)
def import_mairies(request):
    """
    View for importing data from mairies.json
    """
    file_path = os.path.join(settings.BASE_DIR, 'company', 'static', 'datas', 'mairies.json')

    if not os.path.exists(file_path):
        return JsonResponse({
            'success': False,
            'message': f"File not found: {file_path}"
        })

    # Start import in a separate thread
    thread = run_import_in_thread(import_mairies_data, file_path)

    return JsonResponse({
        'success': True,
        'message': "Import started in background. Check logs for progress.",
        'info': "This import will handle duplicate entries, empty coordinates, and API rate limiting automatically."
    })

@user_passes_test(is_superuser)
def import_pharmacies_1(request):
    """
    View for importing data from liste-des-pharmacies-1.json
    """
    file_path = os.path.join(settings.BASE_DIR, 'company', 'static', 'datas', 'liste-des-pharmacies-1.json')

    if not os.path.exists(file_path):
        return JsonResponse({
            'success': False,
            'message': f"File not found: {file_path}"
        })

    # Start import in a separate thread
    thread = run_import_in_thread(import_pharmacies_1_data, file_path)

    return JsonResponse({
        'success': True,
        'message': "Import started in background. Check logs for progress.",
        'info': "This import will handle duplicate entries, empty coordinates, and API rate limiting automatically."
    })

@user_passes_test(is_superuser)
def import_pharmacies_2(request):
    """
    View for importing data from liste-des-pharmacies-2.json
    """
    file_path = os.path.join(settings.BASE_DIR, 'company', 'static', 'datas', 'liste-des-pharmacies-2.json')

    if not os.path.exists(file_path):
        return JsonResponse({
            'success': False,
            'message': f"File not found: {file_path}"
        })

    # Start import in a separate thread
    thread = run_import_in_thread(import_pharmacies_2_data, file_path)

    return JsonResponse({
        'success': True,
        'message': "Import started in background. Check logs for progress.",
        'info': "This import will handle duplicate entries, geocoding, and API rate limiting automatically."
    })

@user_passes_test(is_superuser)
def import_pharmacies_3(request):
    """
    View for importing data from liste-des-pharmacies-3.json
    """
    file_path = os.path.join(settings.BASE_DIR, 'company', 'static', 'datas', 'liste-des-pharmacies-3.json')

    if not os.path.exists(file_path):
        return JsonResponse({
            'success': False,
            'message': f"File not found: {file_path}"
        })

    # Start import in a separate thread
    thread = run_import_in_thread(import_pharmacies_3_data, file_path)

    return JsonResponse({
        'success': True,
        'message': "Import started in background. Check logs for progress.",
        'info': "This import will handle various data formats, geocoding, and API rate limiting automatically."
    })

@user_passes_test(is_superuser)
def import_dashboard(request):
    """
    Dashboard view for data import
    """
    # Check if files exist
    base_path = os.path.join(settings.BASE_DIR, 'company', 'static', 'datas')
    files = {
        'mairies_exists': os.path.exists(os.path.join(base_path, 'mairies.json')),
        'pharmacies1_exists': os.path.exists(os.path.join(base_path, 'liste-des-pharmacies-1.json')),
        'pharmacies2_exists': os.path.exists(os.path.join(base_path, 'liste-des-pharmacies-2.json')),
        'pharmacies3_exists': os.path.exists(os.path.join(base_path, 'liste-des-pharmacies-3.json'))
    }

    return render(request, 'company/import_dashboard.html', {
        'files': files,
        'title': 'Data Import Dashboard'
    })
