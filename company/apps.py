from django.apps import AppConfig


class CompanyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "company"

    def ready(self):
        """
        Importe les signaux lorsque l'application est prête.
        Cela permet d'enregistrer les gestionnaires de signaux.
        """
        import company.signals  # noqa
