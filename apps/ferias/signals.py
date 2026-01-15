from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.funcionarios.models import DadosTrabalhistas
from apps.ferias.service import gerar_novo_periodo_aquisitivo

@receiver(post_save, sender=DadosTrabalhistas)
def criar_primeiro_periodo_signal(sender, instance, created, **kwargs):
    """
    Acionado sempre que salvar DadosTrabalhistas (onde fica a data de admissão).
    Cria o primeiro período automaticamente.
    """
    if instance.funcionario:
        gerar_novo_periodo_aquisitivo(instance.funcionario)