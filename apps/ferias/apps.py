from django.apps import AppConfig


class FeriasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ferias"
    
    def ready(self):
            # Importa os signals para registrar os listeners
            import apps.ferias.signals