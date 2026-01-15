from django.db import models
from apps.configuracoes.mixin import SoftDeleteMixin
from apps.funcionarios.models import Funcionario
from decimal import Decimal

class BancoHoras(SoftDeleteMixin):
    funcionario = models.OneToOneField(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='banco_horas'
    )
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Saldo atual de horas no banco de horas", editable=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Banco de Horas - {self.funcionario.nome}"


class LancamentoHoras(SoftDeleteMixin):
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='lancamentos_horas'
    )
    horas = models.DecimalField(max_digits=6, decimal_places=2)
    
    valor_hora = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name="Valor da Hora (R$)",
        help_text="Valor da hora neste lançamento específico"
    )
    
    data = models.DateTimeField(auto_now_add=True)

    @property
    def total_monetario(self):
        """Calcula quanto vale este lançamento em dinheiro"""
        return self.horas * self.valor_hora

    def __str__(self):
        return f"{self.horas}h - {self.funcionario.nome}"