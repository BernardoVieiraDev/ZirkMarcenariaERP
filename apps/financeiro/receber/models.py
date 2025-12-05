
from django.db import models

class Receber(models.Model):
    forma_de_recebimento = models.CharField('Forma de recebimento', max_length=255, null=True)
    data_vencimento = models.DateField('Data vencimento', null=True, blank=True)
    cliente = models.CharField('Cliente', max_length=255, null=True)
    categoria =  models.CharField('Categoria', max_length=255, null=True)
    valor = models.DecimalField('Valor a ser recebido', max_digits=12, decimal_places=2, null=True)
    valor_estoque = models.DecimalField('Valor em estoque', max_digits=12, decimal_places=2, null=True)
    observacoes = models.CharField('Observações', max_length=255, blank=True)
    data_pagamento = models.DateField('Data pagamento', null=True, blank=True)
    status = models.CharField('Status', max_length=30, default='Agendado')


    def __str__(self):
        return f"{self.cliente} - {self.valor}"

