from datetime import date

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.financeiro.pagar.models import FolhaPagamento

# Adicione RecibosContabilidade aos imports
from .models import (Ferias, PagamentoFerias, PeriodoAquisitivo,
                     RecibosContabilidade)

# Define a chave de cache usada no Dashboard
CACHE_KEY_DASHBOARD_FERIAS = "dashboard_ferias_alerts"

@receiver(post_save, sender=PeriodoAquisitivo)
@receiver(post_delete, sender=PeriodoAquisitivo)
@receiver(post_save, sender=Ferias)
@receiver(post_delete, sender=Ferias)
def invalidar_cache_alertas_ferias(sender, instance, **kwargs):
    """
    Invalida o cache do dashboard ao alterar férias ou períodos.
    """
    cache.delete(CACHE_KEY_DASHBOARD_FERIAS)


# --- NOVA FUNCIONALIDADE: GERAR RECIBO AUTOMÁTICO ---
@receiver(post_save, sender=Ferias)
def gerar_recibo_automatico(sender, instance, created, **kwargs):
    """
    Toda vez que uma Féria for criada (created=True), gera um Recibo Contábil automaticamente.
    """
    if created:
        # Pega o funcionário vinculado ao período aquisitivo dessas férias
        funcionario = instance.periodo.funcionario
        
        # Cria a observação automática
        obs_texto = (
            f""
        )

        # Cria o recibo
        RecibosContabilidade.objects.create(
            funcionario=funcionario,
            recibo_de_ferias_contabilidade=date.today(),  # Data de hoje
            observacoes=obs_texto
        )

@receiver(post_save, sender=PagamentoFerias)
def sincronizar_conta_pagar_ferias(sender, instance, created, **kwargs):
    """
    Sincroniza o Pagamento de Férias com o Contas a Pagar (FolhaPagamento).
    Gera o registro como 'Pendente' para ser pago posteriormente pelo financeiro.
    """
    # Só gera se houver valor > 0
    if instance.valor_a_pagar and instance.valor_a_pagar > 0:
        
        # Mapeamento de dados
        dados_conta = {
            'funcionario': instance.funcionario,
            'data_referencia': instance.vencimento, # Usa o vencimento das férias como referência
            'ferias_terco': instance.valor_a_pagar, # Lança no campo de 1/3 (ou val_ferias se preferir)
            'observacoes': f"Férias (1/3) Ref: {instance.pk}. {instance.observacoes or ''}",
            # Força o status Pendente se não estiver pago, para cair no "Contas a Pagar"
            'status': 'Pago' if instance.status == 'Pago' else 'Pendente',
            'referencia_holerite': 'Férias 1/3'
        }

        if instance.conta_pagar:
            # ATUALIZAÇÃO: Se já existe, atualiza os valores
            conta = instance.conta_pagar
            for key, value in dados_conta.items():
                setattr(conta, key, value)
            conta.save()
        else:
            # CRIAÇÃO: Cria um novo registro em FolhaPagamento
            nova_conta = FolhaPagamento.objects.create(**dados_conta)
            
            # Atualiza o PagamentoFerias com o ID da conta criada (sem disparar o signal novamente usando update)
            PagamentoFerias.objects.filter(pk=instance.pk).update(conta_pagar=nova_conta)

@receiver(post_delete, sender=PagamentoFerias)
def remover_conta_pagar_ferias(sender, instance, **kwargs):
    """
    Se apagar o pagamento de férias, remove a conta a pagar vinculada.
    """
    if instance.conta_pagar:
        instance.conta_pagar.delete()