from django.apps import AppConfig

class CompoundsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.compounds'

    def ready(self):
        import src.data.models