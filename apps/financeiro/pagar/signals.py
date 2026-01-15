from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal
from datetime import date
from django.db import transaction

# Importe seus modelos
from apps.financeiro.receber.models import Banco, MovimentoBanco, CaixaDiario, Receber
from apps.financeiro.pagar.models import (
    Boleto, GastoUtilidade, FaturaCartao, PrestacaoEmprestimo,
    GastoVeiculoConsorcio, GastoContabilidade, GastoImovel,
    GastoGeral, GastoGasolina, FolhaPagamento, ComissaoArquiteto, Cheque
)

# Lista de modelos que devem disparar a automação
MODELOS_FINANCEIROS = [
    Boleto, GastoUtilidade, FaturaCartao, PrestacaoEmprestimo,
    GastoVeiculoConsorcio, GastoContabilidade, GastoImovel,
    GastoGeral, GastoGasolina, FolhaPagamento, ComissaoArquiteto,
    Receber, Cheque
]

def atualizar_extrato(sender, instance, **kwargs):
    """
    Função universal para sincronizar Contas(Pagar/Receber) com Extrato(Banco/Caixa).
    Centraliza toda a lógica para evitar recursão e duplicidade.
    """
    # 0. Evitar execução em fixtures ou dados brutos (opcional, boa prática)
    if kwargs.get('raw', False):
        return

    # 1. Identificar se é Receita ou Despesa
    eh_receita = isinstance(instance, Receber)
    tipo_movimento = 'E' if eh_receita else 'S'
    
    # 2. Obter Status Normalizado
    status = getattr(instance, 'status', '').lower() # pendente, pago, recebido, com, emi
    
    # Lista de status que consideram o dinheiro como "realizado"
    STATUS_REALIZADO = ['pago', 'recebido', 'pg', 'com', 'compensado']
    esta_pago = status in STATUS_REALIZADO
    
    # 3. Determinar Valor Efetivo (Prioriza valor pago, senão valor nominal)
    valor = (
        getattr(instance, 'valor_pago', None) or 
        getattr(instance, 'valor_recebido', None) or 
        getattr(instance, 'valor', None) or 
        getattr(instance, 'valor_total', None) or 
        Decimal(0)
    )
    
    # 4. Determinar Data Efetiva (Prioriza data pagamento, senão vencimento)
    data_mov = (
        getattr(instance, 'data_pagamento', None) or 
        getattr(instance, 'data_recebimento', None) or 
        getattr(instance, 'data_vencimento', None) or 
        getattr(instance, 'data_gasto', None) or 
        getattr(instance, 'data_emissao', None) or 
        date.today()
    )

    # 5. Determinar Forma de Pagamento e Banco
    forma = getattr(instance, 'forma_pagamento', '') or getattr(instance, 'forma_recebimento', '')
    banco_obj = getattr(instance, 'banco_origem', None) or getattr(instance, 'banco_destino', None)

    # Descrição para o extrato
    prefixo = 'Rec.' if eh_receita else 'Pgto.'
    descricao_historico = f"{prefixo}: {str(instance)}"[:255]

    # --- LÓGICA CORE DE SINCRONIZAÇÃO ---

    # CASO A: O item está PAGO/REALIZADO e tem valor > 0
    if esta_pago and valor > 0:
        
        # --- SUB-CASO A1: É MOVIMENTO DE CAIXA (Dinheiro e sem Banco) ---
        if forma == 'DINHEIRO' and not banco_obj:
            
            # 1. Limpeza Cruzada: Se antes era Banco, apaga o registro bancário
            if instance.movimento_banco:
                instance.movimento_banco.delete()
                # Atualiza FK no banco de dados para evitar referências quebradas
                sender.objects.filter(pk=instance.pk).update(movimento_banco=None)
                instance.movimento_banco = None # Atualiza instância em memória
            
            # 2. Criar ou Atualizar no Caixa
            mov_caixa_id = instance.movimento_caixa.id if instance.movimento_caixa else None
            
            cx, created = CaixaDiario.objects.update_or_create(
                id=mov_caixa_id,
                defaults={
                    'data': data_mov,
                    'historico': descricao_historico,
                    'tipo': tipo_movimento,
                    'valor': valor
                }
            )
            
            # 3. Vincular de volta (SE for novo ou mudou)
            # USAMOS .update() PARA NÃO DISPARAR O SIGNAL NOVAMENTE (EVITA RECURSÃO)
            if instance.movimento_caixa != cx:
                sender.objects.filter(pk=instance.pk).update(movimento_caixa=cx)
                instance.movimento_caixa = cx # Mantém consistência na memória

        # --- SUB-CASO A2: É MOVIMENTO BANCÁRIO (Tem Banco ou é Cheque Compensado) ---
        elif banco_obj:
            
            # 1. Limpeza Cruzada: Se antes era Caixa, apaga o registro de caixa
            if instance.movimento_caixa:
                instance.movimento_caixa.delete()
                sender.objects.filter(pk=instance.pk).update(movimento_caixa=None)
                instance.movimento_caixa = None

            # 2. Criar ou Atualizar no Banco
            mov_banco_id = instance.movimento_banco.id if instance.movimento_banco else None

            mv, created = MovimentoBanco.objects.update_or_create(
                id=mov_banco_id,
                defaults={
                    'banco': banco_obj,
                    'data': data_mov,
                    'historico': descricao_historico,
                    'tipo': tipo_movimento,
                    'valor': valor
                }
            )
            
            # 3. Vincular de volta (Sem recursão)
            if instance.movimento_banco != mv:
                sender.objects.filter(pk=instance.pk).update(movimento_banco=mv)
                instance.movimento_banco = mv

    # CASO B: O item voltou a ser PENDENTE ou valor zerou (Estorno/Correção)
    else:
        # Se existia movimento bancário, apaga e desvincula
        if instance.movimento_banco:
            instance.movimento_banco.delete()
            sender.objects.filter(pk=instance.pk).update(movimento_banco=None)
            instance.movimento_banco = None
            
        # Se existia movimento de caixa, apaga e desvincula
        if instance.movimento_caixa:
            instance.movimento_caixa.delete()
            sender.objects.filter(pk=instance.pk).update(movimento_caixa=None)
            instance.movimento_caixa = None

def remover_do_extrato(sender, instance, **kwargs):
    """
    Se excluir a Conta (Pagar/Receber), exclui o movimento financeiro associado.
    """
    try:
        if getattr(instance, 'movimento_banco', None):
            instance.movimento_banco.delete()
    except Exception:
        pass # Já deletado ou erro de acesso
        
    try:
        if getattr(instance, 'movimento_caixa', None):
            instance.movimento_caixa.delete()
    except Exception:
        pass

# --- REGISTRO DOS SIGNALS ---
# Conecta todos os modelos da lista à função única
for model in MODELOS_FINANCEIROS:
    post_save.connect(atualizar_extrato, sender=model)
    post_delete.connect(remover_do_extrato, sender=model)