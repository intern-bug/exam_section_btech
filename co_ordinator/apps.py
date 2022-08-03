from django.apps import AppConfig


class CoOrdinatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'co_ordinator'

    def ready(self):
        import co_ordinator.signals