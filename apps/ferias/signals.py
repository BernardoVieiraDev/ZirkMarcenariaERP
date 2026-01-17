from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

# Importa os modelos que afetam o saldo de férias e os alertas
from .models import PeriodoAquisitivo, Ferias

# Define a chave de cache usada no Dashboard (apps/dashboard/views.py)
CACHE_KEY_DASHBOARD_FERIAS = "dashboard_ferias_alerts"

@receiver(post_save, sender=PeriodoAquisitivo)
@receiver(post_delete, sender=PeriodoAquisitivo)
@receiver(post_save, sender=Ferias)
@receiver(post_delete, sender=Ferias)
def invalidar_cache_alertas_ferias(sender, instance, **kwargs):
    """
    Sempre que um Período Aquisitivo ou uma Féria marcada for criada,
    alterada ou excluída, limpamos o cache de alertas do dashboard.
    Isso força o sistema a recalcular quem está com férias vencendo
    na próxima vez que alguém abrir a página inicial.
    """
    cache.delete(CACHE_KEY_DASHBOARD_FERIAS)
    # Opcional: Log para debug (remova em produção se quiser limpar os logs)
    # print(f"Cache de Férias invalidado por alteração em: {instance}")