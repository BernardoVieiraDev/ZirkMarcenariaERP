from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from apps.funcionarios.models import Funcionario


class PeriodoAquisitivo(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='periodos_aquisitivos')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    dias_direito = models.PositiveIntegerField(default=30)

    def __str__(self):
        return f"{self.funcionario.nome} - {self.data_inicio:%d/%m/%Y} a {self.data_fim:%d/%m/%Y}"

    def dias_gozados(self):
        total = 0
        for f in self.ferias_registradas.all():
            total += max(0, (f.dias_tirados - (f.faltas_justificadas_descontadas or 0)))
        return total

    def saldo_restante(self):
        saldo = self.dias_direito - self.dias_gozados()
        return max(0, saldo)

class Ferias(models.Model):
    periodo = models.ForeignKey(PeriodoAquisitivo, on_delete=models.CASCADE, related_name='ferias_registradas')
    dias_tirados = models.PositiveIntegerField()
    faltas_justificadas_descontadas = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True)
    
    ferias_no_recesso_final_ano = models.PositiveIntegerField(default=0, blank=True, null=True)
    ferias_no_carnaval = models.PositiveIntegerField(default=0, blank=True, null=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Férias de {self.periodo.funcionario.nome}"

    def clean(self):
        if self.dias_tirados < 0:
            raise ValueError("Dias tirados deve ser >= 0")

    def save(self, *args, **kwargs):
        consumo = max(0, self.dias_tirados - (self.faltas_justificadas_descontadas or 0))
        if self.pk:
            old = Ferias.objects.get(pk=self.pk)
            outros_total = sum(max(0, f.dias_tirados - (f.faltas_justificadas_descontadas or 0))
                               for f in self.periodo.ferias_registradas.exclude(pk=self.pk))
            saldo_disponivel = self.periodo.dias_direito - outros_total
        else:
            saldo_disponivel = self.periodo.saldo_restante()

        super().save(*args, **kwargs)

class PagamentoFerias(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='pagamentos_ferias')
    vencimento = models.DateField(verbose_name="Data de Vencimento")
    valor_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    data_pagamento = models.DateField(blank=True, null=True, verbose_name="Data do Pagamento")
    
    STATUS_CHOICES = (('pendente', 'Pendente'), ('pago', 'Pago'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', blank=True)
    observacoes = models.TextField(blank=True, null=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Verifica se o valor está vazio ou é zero
        if not self.valor_a_pagar:
            try:
                # Tenta acessar os dados trabalhistas. 
                # O uso de 'hasattr' evita erro se a relação não existir no banco ainda,
                # mas o ideal é garantir que existe via try/except ObjectDoesNotExist.
                if hasattr(self.funcionario, 'dados_trabalhistas'):
                    salario = self.funcionario.dados_trabalhistas.salario
                    if salario:
                        # Cálculo: Salário / 3
                        # É importante converter o divisor para Decimal para manter precisão
                        valor = salario / Decimal("3.0")
                        self.valor_a_pagar = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except ObjectDoesNotExist:
                # Caso o funcionário não tenha dados_trabalhistas vinculados
                pass
            except Exception:
                # Se houver outro erro (ex: salário inválido), mantém como None ou trata conforme necessário
                pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pgto 1/3 - {self.funcionario}"

# --- Adicionado para funcionar o relatório ---
class RecibosContabilidade(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='recibo_contabilidade')
    recibo_de_ferias_contabilidade = models.DateField(verbose_name="Data Recibo Contábil", null=True, blank=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Recibo - {self.funcionario.nome}"