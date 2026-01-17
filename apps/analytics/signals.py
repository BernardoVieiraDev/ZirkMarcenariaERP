from datetime import date
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

# Importar TODOS os modelos que mexem com dinheiro
from apps.financeiro.receber.models import Receber, MovimentoBanco, CaixaDiario
from apps.financeiro.pagar.models import (
    Boleto, Cheque, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
    GastoContabilidade, GastoGasolina, GastoGeral, GastoImovel,
    GastoUtilidade, GastoVeiculoConsorcio, PrestacaoEmprestimo
)
from apps.financeiro.fluxo.services import FluxoCaixaService

# Lista completa para garantir integridade
MODELOS_FINANCEIROS = [
    Receber, MovimentoBanco, CaixaDiario,
    Boleto, Cheque, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
    GastoContabilidade, GastoGasolina, GastoGeral, GastoImovel,
    GastoUtilidade, GastoVeiculoConsorcio, PrestacaoEmprestimo
]

@receiver(post_save)
@receiver(post_delete)
def invalidar_cache_financeiro(sender, instance, **kwargs):
    """
    Observer central: Se qualquer tabela financeira for tocada,
    invalida os caches relacionados.
    """
    if sender in MODELOS_FINANCEIROS:
        # 1. Limpa Fluxo de Caixa (Saldos e Timeline) - CRÍTICO
        FluxoCaixaService.clear_fluxo_cache()
        
        # 2. Limpa Totais do Topo do Dashboard
        cache.delete("dashboard_header_totals")
        
        # 3. Limpa Analytics (Gráficos)
        # Tenta descobrir o ano da transação para limpar apenas o cache daquele ano
        data_ref = (
            getattr(instance, 'data_vencimento', None) or 
            getattr(instance, 'data_pagamento', None) or 
            getattr(instance, 'data_gasto', None) or 
            getattr(instance, 'data_recebimento', None) or 
            getattr(instance, 'data', date.today())
        )
        
        if data_ref:
            year = data_ref.year
            # Limpa as chaves definidas no apps/analytics/services.py
            keys_to_delete = [
                f"analytics_cash_flow_{year}",
                f"analytics_expense_breakdown_{year}",
                f"analytics_managerial_costs_{year}"
            ]
            cache.delete_many(keys_to_delete)