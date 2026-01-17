from django.apps import AppConfig


class RescisaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rescisao"
    def ready(self):
            import apps.rescisao.signals