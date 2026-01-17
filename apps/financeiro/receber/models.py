import uuid
from decimal import Decimal

from django.db import models

from apps.configuracoes.mixin import SoftDeleteMixin


class CaixaDiario(SoftDeleteMixin):
    TIPO_CHOICES = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
    ]
    data = models.DateField()
    historico = models.CharField(max_length=255)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.data} - {self.historico} - {self.valor}"

class Banco(models.Model):
    nome = models.CharField(max_length=100)
    agencia = models.CharField(max_length=20, blank=True, null=True)
    conta = models.CharField(max_length=20, blank=True, null=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.nome

class MovimentoBanco(SoftDeleteMixin):
    TIPO_CHOICES = [
        ('E', 'Entrada'),
        ('S', 'Saída'),
    ]
    banco = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name='movimentos')
    data = models.DateField()
    historico = models.CharField(max_length=255)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.banco} - {self.data} - {self.valor}"


# --- Model Principal ---

class Receber(SoftDeleteMixin):
    TIPO_CHOICES = [
        ('VISTA', 'À Vista'),
        ('PRAZO', 'A Prazo'),
    ]
    parcelamento_uuid = models.UUIDField(null=True, blank=True, editable=False)
    
    class FormaRecebimento(models.TextChoices):
        DINHEIRO = 'DINHEIRO', 'Dinheiro'
        PIX = 'PIX', 'Pix'
        DEBITO = 'DEBITO', 'Cartão de Débito'
        CREDITO = 'CREDITO', 'Cartão de Crédito'
        BOLETO = 'BOLETO', 'Boleto'
        TRANSFERENCIA = 'TRANSFERENCIA', 'Transferência'
        OUTROS = 'OUTROS', 'Outros'

    contrato_rt = models.ForeignKey(
        'comissionamento.ContratoRT', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='parcelas_receber', # Permite acessar as parcelas a partir do contrato: contrato.parcelas_receber.all()
        verbose_name="Contrato RT Vinculado"
    )
        

    banco_destino = models.ForeignKey(
        'Banco', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Conta Bancária (Destino)"
    )
    
    # Campos de vínculo interno (para o sistema saber qual linha do extrato pertence a este recebimento)
    movimento_banco = models.OneToOneField(
        'MovimentoBanco', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recebimento_origem'
    )
    movimento_caixa = models.OneToOneField(
        'CaixaDiario', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='recebimento_origem'
    )

    cliente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Cliente"
    )
    # Campos Básicos
    descricao = models.CharField("Descrição", max_length=255, blank=True, null=True)
    categoria = models.CharField("Categoria", max_length=255, blank=True, null=True)
    
    # Valores e Datas
    valor = models.DecimalField("Valor Previsto", max_digits=10, decimal_places=2)
    data_vencimento = models.DateField("Data de Vencimento")
    
    # Recebimento Real
    valor_recebido = models.DecimalField(
        "Valor Recebido", 
        max_digits=10, 
        decimal_places=2,
        null=True, 
        default=Decimal('0.00'), 
        blank=True
    )
    data_recebimento = models.DateField("Data do Recebimento", blank=True, null=True)
    
    # Classificação
    tipo_recebimento = models.CharField(
        "Tipo de Recebimento",  # Alterado para algo mais claro.
        max_length=10,
        choices=TIPO_CHOICES,
        default='VISTA'
    )
    
    forma_recebimento = models.CharField(
        "Forma de Pagamento",
        max_length=20,
        choices=FormaRecebimento.choices,
        default=FormaRecebimento.OUTROS
    )

    status = models.CharField(
        max_length=20, 
        choices=[('Pendente', 'Pendente'), ('Recebido', 'Recebido')],
        default='Pendente'
    )
    
    observacoes = models.TextField("Observações", blank=True, null=True)

    def __str__(self):
        return f"{self.descricao} - {self.valor}"

