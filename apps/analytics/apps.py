from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analytics"
    def ready(self):
            # Importa os signals quando o app estiver pronto
            import apps.analytics.signals