from django.apps import AppConfig

class CompoundsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.compound'

    def ready(self):
        import src.data.models