from django.db import models
from apps.funcionarios.models import Funcionario
from decimal import Decimal

class BancoHoras(models.Model):
    funcionario = models.OneToOneField(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='banco_horas'
    )
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Saldo atual de horas no banco de horas", editable=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Banco de Horas - {self.funcionario.nome}"


class LancamentoHoras(models.Model):
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='lancamentos_horas'
    )
    horas = models.DecimalField(max_digits=6, decimal_places=2)
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.horas}h - {self.funcionario.nome}"