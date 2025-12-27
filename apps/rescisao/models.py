from django.db import models
from decimal import Decimal
from apps.funcionarios.models import Funcionario

class MotivoDemissao(models.TextChoices):
    SEM_JUSTA_CAUSA = 'SJC', 'Dispensa sem Justa Causa'
    POR_JUSTA_CAUSA = 'PJC', 'Dispensa por Justa Causa'
    PEDIDO_DEMISSAO = 'PED', 'Pedido de Demissão'
    TERMINO_CONTRATO = 'TER', 'Término de Contrato'
    ACORDO = 'ACO', 'Acordo (Art. 484-A)'

class TipoOutro(models.TextChoices):
    PROVENTO = 'P', 'Provento (+)'
    DESCONTO = 'D', 'Desconto (-)'

class Rescisao(models.Model):
    funcionario = models.OneToOneField(Funcionario, on_delete=models.CASCADE, related_name='rescisao')
    data_demissao = models.DateField(verbose_name="Data de Demissão")
    motivo = models.CharField(max_length=3, choices=MotivoDemissao.choices, default=MotivoDemissao.SEM_JUSTA_CAUSA)
    
    # Proventos
    val_dias_trabalhados = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Dias Trabalhados")
    val_ferias = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Férias")
    val_terco_ferias = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="1/3 de Férias")
    val_13_salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="13º Salário")
    val_remunerados = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Remunerados")

    # Descontos
    val_adiantamento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Adiantamento")
    val_atrasos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Atrasos")
    val_multa_480 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Desconto Multa Art. 480")
    val_faltas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Faltas")
    desc_faltas = models.CharField(max_length=100, blank=True, null=True, verbose_name="Detalhamento Faltas")

    # Outros
    outro_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descrição (Outros)")
    outro_valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Valor (Outros)")
    outro_tipo = models.CharField(max_length=1, choices=TipoOutro.choices, default=TipoOutro.PROVENTO, verbose_name="Tipo (Outros)")

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rescisão - {self.funcionario.nome}"

    @property
    def total_liquido(self):
        """Calcula o valor líquido (Proventos - Descontos)"""
        # Soma Proventos
        proventos = (self.val_dias_trabalhados or 0) + \
                    (self.val_ferias or 0) + \
                    (self.val_terco_ferias or 0) + \
                    (self.val_13_salario or 0) + \
                    (self.val_remunerados or 0)
        
        # Soma Descontos
        descontos = (self.val_adiantamento or 0) + \
                    (self.val_atrasos or 0) + \
                    (self.val_multa_480 or 0) + \
                    (self.val_faltas or 0)

        # Processa campo 'Outros'
        if self.outro_valor:
            if self.outro_tipo == TipoOutro.PROVENTO:
                proventos += self.outro_valor
            else:
                descontos += self.outro_valor
        
        return proventos - descontos