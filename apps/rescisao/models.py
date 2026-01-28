from django.db import models
from decimal import Decimal
from apps.configuracoes.mixin import SoftDeleteMixin
from apps.funcionarios.models import Funcionario

class TipoOutro(models.TextChoices):
    PROVENTO = 'P', 'Provento (+)'
    DESCONTO = 'D', 'Desconto (-)'

class Rescisao(SoftDeleteMixin):
    funcionario = models.OneToOneField(Funcionario, on_delete=models.CASCADE, related_name='rescisao')
    data_demissao = models.DateField(verbose_name="Data de Demissão")
    
    # Proventos Fixo
    val_dias_trabalhados = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Dias Trabalhados")
    val_ferias = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Férias")
    val_terco_ferias = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="1/3 de Férias")
    val_13_salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="13º Salário")
    val_remunerados = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Remunerados")

    # Descontos Fixos
    val_adiantamento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Adiantamento")
    val_atrasos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Atrasos")
    val_multa_480 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Desconto Multa Art. 480")
    val_faltas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Faltas")
    desc_faltas = models.CharField(max_length=100, blank=True, null=True, verbose_name="Detalhamento Faltas")

    # REMOVIDOS OS CAMPOS: outro_nome, outro_valor, outro_tipo

    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rescisão - {self.funcionario.nome}"

    @property
    def total_liquido(self):
        """Calcula o valor líquido (Proventos - Descontos)"""
        proventos = (self.val_dias_trabalhados or 0) + \
                    (self.val_ferias or 0) + \
                    (self.val_terco_ferias or 0) + \
                    (self.val_13_salario or 0) + \
                    (self.val_remunerados or 0)
        
        descontos = (self.val_adiantamento or 0) + \
                    (self.val_atrasos or 0) + \
                    (self.val_multa_480 or 0) + \
                    (self.val_faltas or 0)

        # Soma os itens dinâmicos relacionados
        # Verifica se o objeto já foi salvo para evitar erro de acesso a ManyToMany antes de salvar
        if self.pk:
            for item in self.itens_adicionais.all():
                if item.tipo == TipoOutro.PROVENTO:
                    proventos += (item.valor or 0)
                else:
                    descontos += (item.valor or 0)
        
        return proventos - descontos

# Novo Modelo para múltiplos itens
class ItemRescisao(models.Model):
    rescisao = models.ForeignKey(Rescisao, on_delete=models.CASCADE, related_name='itens_adicionais')
    descricao = models.CharField(max_length=100, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    tipo = models.CharField(max_length=1, choices=TipoOutro.choices, default=TipoOutro.PROVENTO, verbose_name="Tipo")