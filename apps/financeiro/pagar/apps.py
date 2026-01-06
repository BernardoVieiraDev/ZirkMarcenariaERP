from django.apps import AppConfig


class PagarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.financeiro.pagar"
    def ready(self):
            # Importa os signals quando o app estiver pronto
            import apps.financeiro.pagar.signals