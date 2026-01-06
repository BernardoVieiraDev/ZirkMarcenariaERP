from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from datetime import date

# Importe seus modelos
from apps.financeiro.receber.models import Banco, MovimentoBanco, CaixaDiario, Receber
from apps.financeiro.pagar.models import (
    Boleto, GastoUtilidade, FaturaCartao, PrestacaoEmprestimo,
    GastoVeiculoConsorcio, GastoContabilidade, GastoImovel,
    GastoGeral, GastoGasolina, FolhaPagamento, ComissaoArquiteto
)

# Lista de modelos que devem disparar a automação
MODELOS_FINANCEIROS = [
    Boleto, GastoUtilidade, FaturaCartao, PrestacaoEmprestimo,
    GastoVeiculoConsorcio, GastoContabilidade, GastoImovel,
    GastoGeral, GastoGasolina, FolhaPagamento, ComissaoArquiteto,
    Receber
]

def atualizar_extrato(sender, instance, **kwargs):
    """
    Função universal para sincronizar Contas(Pagar/Receber) com Extrato(Banco/Caixa).
    """
    # 1. Identificar se é Receita ou Despesa
    eh_receita = isinstance(instance, Receber)
    tipo_movimento = 'E' if eh_receita else 'S'
    
    # 2. Obter Status e Valores
    status = getattr(instance, 'status', '').lower() # pendente, pago, recebido
    esta_pago = status in ['pago', 'recebido', 'pg']
    
    # Determinar valor efetivo (se tiver valor_pago/recebido, usa ele, senão usa o valor previsto)
    valor = getattr(instance, 'valor_pago', None) or getattr(instance, 'valor_recebido', None) or getattr(instance, 'valor', None) or getattr(instance, 'valor_total', None) or Decimal(0)
    
    # Determinar Data (data_pagamento > data_recebimento > data_vencimento > data_gasto)
    data_mov = getattr(instance, 'data_pagamento', None) or getattr(instance, 'data_recebimento', None) or getattr(instance, 'data_vencimento', None) or getattr(instance, 'data_gasto', None) or date.today()

    # Determinar Forma de Pagamento e Banco
    forma = getattr(instance, 'forma_pagamento', '') or getattr(instance, 'forma_recebimento', '')
    banco_obj = getattr(instance, 'banco_origem', None) or getattr(instance, 'banco_destino', None) # Pega o banco se houver

    descricao_historico = f"{'Rec.' if eh_receita else 'Pgto.'}: {str(instance)}"[:255]

    # --- LÓGICA DE SINCRONIZAÇÃO ---

    # CASO A: O item foi marcado como PAGO/RECEBIDO
    if esta_pago and valor > 0:
        
        # 1. Lógica para CAIXA (Se for Dinheiro e NÃO tiver banco selecionado)
        if forma == 'DINHEIRO' and not banco_obj:
            # Se já existia movimento bancário erroneamente, apaga
            if instance.movimento_banco:
                instance.movimento_banco.delete()
                instance.movimento_banco = None
            
            # Cria ou Atualiza no Caixa
            cx, created = CaixaDiario.objects.update_or_create(
                id=instance.movimento_caixa.id if instance.movimento_caixa else None,
                defaults={
                    'data': data_mov,
                    'historico': descricao_historico,
                    'tipo': tipo_movimento,
                    'valor': valor
                }
            )
            if instance.movimento_caixa != cx:
                instance.movimento_caixa = cx
                # Precisamos salvar o instance sem disparar o signal novamente (loop infinito)
                # O Django lida bem com isso se usarmos update, mas aqui vamos salvar direto
                instance.__class__.objects.filter(pk=instance.pk).update(movimento_caixa=cx)

        # 2. Lógica para BANCO (Se tiver banco selecionado)
        elif banco_obj:
            # Se já existia movimento de caixa erroneamente, apaga
            if instance.movimento_caixa:
                instance.movimento_caixa.delete()
                instance.movimento_caixa = None

            # Cria ou Atualiza no Banco
            mv, created = MovimentoBanco.objects.update_or_create(
                id=instance.movimento_banco.id if instance.movimento_banco else None,
                defaults={
                    'banco': banco_obj,
                    'data': data_mov,
                    'historico': descricao_historico,
                    'tipo': tipo_movimento,
                    'valor': valor
                }
            )
            if instance.movimento_banco != mv:
                instance.movimento_banco = mv
                instance.__class__.objects.filter(pk=instance.pk).update(movimento_banco=mv)

    # CASO B: O item voltou a ser PENDENTE ou valor zerou
    else:
        # Se existem movimentos vinculados, apague-os
        if instance.movimento_banco:
            instance.movimento_banco.delete()
            instance.movimento_banco = None
            instance.__class__.objects.filter(pk=instance.pk).update(movimento_banco=None)
            
        if instance.movimento_caixa:
            instance.movimento_caixa.delete()
            instance.movimento_caixa = None
            instance.__class__.objects.filter(pk=instance.pk).update(movimento_caixa=None)

def remover_do_extrato(sender, instance, **kwargs):
    """Se excluir a Conta, exclui o movimento financeiro associado."""
    if hasattr(instance, 'movimento_banco') and instance.movimento_banco:
        instance.movimento_banco.delete()
    if hasattr(instance, 'movimento_caixa') and instance.movimento_caixa:
        instance.movimento_caixa.delete()

# --- REGISTRO DOS SIGNALS ---
for model in MODELOS_FINANCEIROS:
    post_save.connect(atualizar_extrato, sender=model)
    post_delete.connect(remover_do_extrato, sender=model)