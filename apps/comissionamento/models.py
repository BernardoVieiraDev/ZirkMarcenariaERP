from django.db import models
from decimal import Decimal

class Arquiteta(models.Model):
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

class ContratoRT(models.Model):
    arquiteta = models.ForeignKey(Arquiteta, on_delete=models.PROTECT, verbose_name="Arquiteta Responsável")
    cliente = models.CharField(max_length=255, verbose_name="Nome do Cliente/Projeto")
    data_contrato = models.DateField(verbose_name="Data do Contrato", null=True, blank=True)
    
    # Novo Campo
    percentual = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Porcentagem (%)", default=Decimal('0.00'),)
    
    valor_servico = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor do Serviço")
    valor_rt = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor da RT")
    
    data_pagamento = models.DateField(verbose_name="Data do Pagamento", null=True, blank=True)
    valor_pago = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Pago", null=True, blank=True)
    observacoes = models.TextField(verbose_name="Observações", null=True, blank=True)
    
    class Meta:
        verbose_name = "Contrato de RT"
        verbose_name_plural = "Contratos de RT"
        ordering = ['-data_contrato']
    
    def __str__(self):
        return f"{self.arquiteta.nome} - {self.cliente}"