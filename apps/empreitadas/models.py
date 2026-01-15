from decimal import Decimal

from django.db import models
from django.db.models import Sum

from apps.clientes.models import Cliente
from apps.configuracoes.mixin import SoftDeleteMixin
from apps.funcionarios.models import Funcionario


class Empreitada(SoftDeleteMixin):
    STATUS_CHOICES = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDA', 'Concluída'),
        ('CANCELADA', 'Cancelada'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='empreitadas')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='empreitadas')
    ambiente = models.CharField(max_length=200, help_text="Ex: Cozinha, Quarto Casal, etc.")
    descricao = models.TextField(blank=True, verbose_name="Descrição Detalhada")
    
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total da Empreitada")
    data_inicio = models.DateField()
    data_fim_estimada = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EM_ANDAMENTO')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.ambiente} - {self.funcionario.nome}"

    @property
    def total_pago(self):
        """Soma tudo que o funcionário já 'pegou'"""
        soma = self.pagamentos.filter(is_deleted=False).aggregate(total=Sum('valor'))['total']
        return soma or Decimal('0.00')

    @property
    def valor_restante(self):
        """Calcula quanto falta receber"""
        return self.valor_total - self.total_pago

    @property
    def percentual_pago(self):
        if self.valor_total > 0:
            return (self.total_pago / self.valor_total) * 100
        return 0

class PagamentoEmpreitada(SoftDeleteMixin):
    """Registra os valores que são pegos 'aos poucos'"""
    empreitada = models.ForeignKey(Empreitada, on_delete=models.CASCADE, related_name='pagamentos')
    data = models.DateField(default=models.functions.Now)
    valor = models.DecimalField(max_digits=10, decimal_places=2, help_text="Valor retirado pelo funcionário")
    observacao = models.CharField(max_length=200, blank=True, verbose_name="Observação (Ex: Adiantamento p/ almoço)")
    
    # Integração opcional: Se quiser ligar isso ao financeiro geral depois
    # conta_pagar = models.ForeignKey('pagar.Pagar', null=True, blank=True, ...)

    def __str__(self):
        return f"R$ {self.valor} - {self.empreitada}"