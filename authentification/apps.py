from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class AuthentificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentification'

    # def ready(self):
    #     # Implicitly connect signal handlers decorated with @receiver.
    #     from authentification import signals

        # Explicitly connect a signal handler.
        # user_logged_in.connect(signals.add_user_profile_to_session)