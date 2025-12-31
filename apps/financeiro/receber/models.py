
from django.db import models
from django.db.models import Sum


class Receber(models.Model):
    TIPO_CHOICES = [
            ('VISTA', 'À Vista'),
            ('PRAZO', 'A Prazo'),
        ]
        
    tipo_recebimento = models.CharField(
            max_length=10, 
            choices=TIPO_CHOICES, 
            default='PRAZO',
            verbose_name="Classificação Gerencial"
        )

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



class CaixaDiario(models.Model):
    TIPO_CHOICES = [
        ('E', 'Entrada (+)'),
        ('S', 'Saída (-)'),
    ]

    data = models.DateField('Data', default=models.functions.Now)
    tipo = models.CharField('Tipo', max_length=1, choices=TIPO_CHOICES, default='S')
    descricao = models.CharField('Histórico/Descrição', max_length=255)
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Metadados para ordenação
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lançamento de Caixa"
        verbose_name_plural = "Caixa Diário"
        ordering = ['-data', '-created_at']

    def __str__(self):
        return f"{self.data} - {self.descricao} ({self.get_tipo_display()})"
    


class Banco(models.Model):
    nome = models.CharField('Nome do Banco', max_length=100)
    agencia = models.CharField('Agência', max_length=20, blank=True, null=True)
    conta = models.CharField('Conta', max_length=30, blank=True, null=True)
    saldo_inicial = models.DecimalField('Saldo Inicial da Conta', max_digits=12, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f"{self.nome} (Ag: {self.agencia} / CC: {self.conta})"

class MovimentoBanco(models.Model):
    TIPO_CHOICES = [
        ('E', 'Entrada (+)'),
        ('S', 'Saída (-)'),
    ]

    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, verbose_name="Banco/Conta")
    data = models.DateField('Data', default=models.functions.Now)
    tipo = models.CharField('Tipo', max_length=1, choices=TIPO_CHOICES, default='S')
    descricao = models.CharField('Histórico/Descrição', max_length=255)
    valor = models.DecimalField('Valor (R$)', max_digits=12, decimal_places=2)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimento Bancário"
        verbose_name_plural = "Movimentações Bancárias"
        ordering = ['-data', '-created_at']

    def __str__(self):
        return f"{self.banco} - {self.descricao} ({self.valor})"