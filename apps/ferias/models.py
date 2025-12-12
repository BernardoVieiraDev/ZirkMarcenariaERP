from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.utils import timezone

from apps.funcionarios.models import Funcionario

class PeriodoAquisitivo(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='periodos_aquisitivos')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias_direito = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.funcionario.nome} - {self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}"

    def dias_gozados(self):
        """Soma total de dias já tirados nesse período (descontando faltas já aplicadas nas férias)."""
        total = 0
        for f in self.ferias_registradas.all(): #type: ignore
            # dias efetivamente consumidos no saldo = dias_tirados - faltas_justificadas_descontadas
            total += max(0, (f.dias_tirados - (f.faltas_justificadas_descontadas or 0)))
        return total

    def saldo_restante(self):
        """Dias ainda disponíveis"""
        saldo = self.dias_direito - self.dias_gozados()
        return max(0, saldo)

    @property
    def total_dias_tirados(self):
        """Total bruto de dias tirados (sem subtrair faltas)"""
        return sum(f.dias_tirados for f in self.ferias_registradas.all()) #type: ignore


class Ferias(models.Model):
    periodo = models.ForeignKey(PeriodoAquisitivo, on_delete=models.CASCADE, related_name='ferias_registradas')
    dias_tirados = models.PositiveIntegerField()
    faltas_justificadas_descontadas = models.PositiveIntegerField(default=0)  # novo
    observacoes = models.TextField(blank=True)  # novo
    
    ferias_no_recesso_final_ano = models.PositiveIntegerField()
    ferias_no_carnaval = models.PositiveIntegerField()

    
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Férias de {self.periodo.funcionario.nome} ({self.data_inicio:%d/%m/%Y} - {self.data_fim:%d/%m/%Y})" #type: ignore

    def clean(self):
        # validações adicionais (opcional: usar full_clean em views)
        if self.dias_tirados < 0:
            raise ValueError("Dias tirados deve ser >= 0")
        if self.faltas_justificadas_descontadas < 0:
            raise ValueError("Faltas descontadas deve ser >= 0")

    def save(self, *args, **kwargs):
        """Valida para não ultrapassar o saldo restante (considerando faltas que descontam)."""
        # calcula consumo real que será abatido do periodo
        consumo = max(0, self.dias_tirados - (self.faltas_justificadas_descontadas or 0))

        # se o objeto já existe (update), considerar os valores antigos para permitir edição
        if self.pk:
            old = Ferias.objects.get(pk=self.pk)
            # saldo antes deste registro = periodo.dias_direito - (total gozados sem este registro)
            outros_total = sum(max(0, f.dias_tirados - (f.faltas_justificadas_descontadas or 0))
                               for f in self.periodo.ferias_registradas.exclude(pk=self.pk)) #type: ignore
            saldo_disponivel = self.periodo.dias_direito - outros_total
        else:
            # saldo atual sem este registro
            saldo_disponivel = self.periodo.saldo_restante()

        if consumo > saldo_disponivel:
            raise ValueError("Dias tirados (ajustados por faltas) excedem o saldo restante do período.")

        super().save(*args, **kwargs)


class PagamentoFerias(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='pagamentos_ferias')
    vencimento = models.DateField(verbose_name="Data de Vencimento")
    valor_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data do Pagamento")
    observacoes = models.TextField(blank=True, null=True)

    # Recibo contábil
    data_recibo_contabilidade = models.DateField(blank=True, null=True, verbose_name="Data do Recibo Contábil")
    observacoes_recibo_contabilidade = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Calcula automaticamente o valor de 1/3 de férias se não for informado manualmente.
        """
        if not self.valor_a_pagar and hasattr(self.funcionario, 'salario'):
            salario = Decimal(self.funcionario.salario) #type: ignore
            valor = salario / Decimal(3)
            # arredondamento contábil: 2 casas, com meio para cima
            self.valor_a_pagar = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento 1/3 Férias - {self.funcionario} ({self.vencimento})"
"""    

class RecibosContabilidade(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='recibo contabilidade')
    recibo_de_ferias_contabilidade = models.DateField()
    observacoes = models.TextField()"""