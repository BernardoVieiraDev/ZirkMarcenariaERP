from django.db import models
from django.db.models import Sum
from decimal import Decimal

# --- Modelos de Entidade (Pode ser uma FK para seu app 'funcionarios' se já tiver Pessoa) ---
class Arquiteta(models.Model):
    """
    Modelo base para armazenar dados cadastrais e bancários da arquiteta/comissionada.
    """
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    banco = models.CharField(max_length=50, verbose_name="Banco de Pagamento")
    agencia = models.CharField(max_length=20, verbose_name="Agência")
    conta = models.CharField(max_length=50, verbose_name="Conta Bancária")
    
    class Meta:
        verbose_name = "Arquiteta"
        verbose_name_plural = "Arquitetas"

    def __str__(self):
        return self.nome

# --- Modelos de Passivo e Gasto ---

class ContratoRT(models.Model):
    """
    Representa o contrato de Remuneração Técnica (RT) e o passivo total com o cliente.
    (Equivale à linha de resumo na aba 'RTs POR CLIENTE')
    """
    arquiteta = models.ForeignKey(
        Arquiteta, 
        on_delete=models.PROTECT, 
        verbose_name="Arquiteta Responsável"
    )
    cliente = models.CharField(max_length=255, verbose_name="Nome do Cliente/Projeto")
    data_contrato = models.DateField(verbose_name="Data de Assinatura")
    valor_servico = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total do Serviço")
    
    # Valores de RT (base para o cálculo)
    valor_rt_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total da RT Devida")
    percentual_rt = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Percentual (%)")
    
    # Saldo (Calculado automaticamente)
    saldo_devedor = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), editable=False)
    
    class Meta:
        verbose_name = "Contrato de RT"
        verbose_name_plural = "Contratos de RT"
        ordering = ['-data_contrato']
    
    def __str__(self):
        return f"RT {self.arquiteta.nome} - Cliente {self.cliente}"

class PagamentoRT(models.Model):
    """
    Registra cada pagamento de parcela da Remuneração Técnica.
    (Equivale às linhas detalhadas na aba 'RT (2)')
    """
    contrato = models.ForeignKey(
        ContratoRT, 
        on_delete=models.CASCADE, 
        verbose_name="Contrato de Referência"
    )
    data_pagamento = models.DateField(verbose_name="Data do Pagamento")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Pago")
    observacoes = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Pagamento de RT"
        verbose_name_plural = "Pagamentos de RT"
        ordering = ['-data_pagamento']

    def __str__(self):
        return f"Pgto {self.contrato.cliente} - {self.data_pagamento}"

# --- Lógica de Negócio (Signals) ---

# Conecta esta função ao evento de salvar (post_save) e deletar (post_delete) o PagamentoRT
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=PagamentoRT)
def recalcula_saldo_rt(sender, instance, **kwargs):
    """Recalcula o saldo devedor do ContratoRT após cada pagamento ou exclusão."""
    contrato = instance.contrato
    
    # Soma todos os pagamentos feitos para este contrato
    total_pago = PagamentoRT.objects.filter(contrato=contrato).aggregate(
        total=Sum('valor_pago')
    )['total'] or Decimal('0.00')
    
    # Atualiza o saldo devedor
    saldo_novo = contrato.valor_rt_total - total_pago
    
    # Evita recursão infinita se o ContratoRT tivesse um save() que chamasse este signal
    ContratoRT.objects.filter(pk=contrato.pk).update(saldo_devedor=saldo_novo)