from django.db import models

class StatusPagamento(models.TextChoices):
    PENDENTE = 'Pendente', 'Pendente'
    PAGO = 'Pago', 'Pago'
    ATRASADO = 'Atrasado', 'Atrasado'
    # Adicione mais status aqui se quiser, por exemplo:
    # ATRASADO = 'atrasado', 'Atrasado'
    # CANCELADO = 'cancelado', 'Cancelado'

class Pagar(models.Model):
    desc = models.CharField('Descrição', max_length=255, blank=True)
    nota_fiscal = models.CharField('Nota Fiscal', max_length=100, blank=True, null=True)
    value = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    due = models.DateField('Data de Vencimento', null=True, blank=True)
    valor_pago = models.DecimalField('Valor Pago', max_digits=12, decimal_places=2, null=True, blank=True)
    juros = models.DecimalField('Juros', max_digits=12, decimal_places=2, null=True, blank=True)
    data_pagamento = models.DateField('Data do Pagamento', null=True, blank=True)

    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
    )

    def __str__(self):
        return f"{self.desc} - {self.value}"
#Descrição
#Nota fiscal 
#Valor
#Data Venc.
#Valor Pago
#Juros
#Data do Pagamento