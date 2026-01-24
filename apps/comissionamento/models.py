from django.db import models
from decimal import Decimal
from apps.configuracoes.mixin import SoftDeleteMixin
# Importe o modelo de Cliente
from apps.clientes.models import Cliente 

class Arquiteta(SoftDeleteMixin):
    nome = models.CharField(max_length=150)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    banco = models.CharField(max_length=50, verbose_name="Banco de Pagamento")
    agencia = models.CharField(max_length=20, verbose_name="Agência")
    conta = models.CharField(max_length=50, verbose_name="Conta Bancária")
    
    class Meta:
        verbose_name = "Arquiteta"
        verbose_name_plural = "Arquitetas"

    def __str__(self):
        return self.nome

class ContratoRT(SoftDeleteMixin):
    arquiteta = models.ForeignKey(Arquiteta, on_delete=models.PROTECT, verbose_name="Arquiteta Responsável")
    
    # VÍNCULO REAL COM O CLIENTE
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, verbose_name="Cliente")
    
    data_contrato = models.DateField(verbose_name="Data do Contrato", null=True, blank=True)
    
    # Valores
    percentual = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Porcentagem RT (%)", default=Decimal('0.00'))
    valor_servico = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total do Projeto")
    valor_rt = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Comissão (Valor da RT)")
    
    observacoes = models.TextField(verbose_name="Observações", null=True, blank=True)

    @property
    def banco_saida_previsto(self):
        """Retorna o banco da primeira parcela de comissão encontrada"""
        # A relação 'comissoes_pagar' vem do related_name em ComissaoArquiteto
        primeira_comissao = self.comissoes_pagar.filter(is_deleted=False).first()
        if primeira_comissao and primeira_comissao.banco_origem:
            return primeira_comissao.banco_origem
        return None

    # Campos calculados (somente leitura, baseados no Financeiro)
# ... (mantenha o código anterior)

    # Campos calculados existentes...
    @property
    def total_recebido(self):
        return self.parcelas_receber.filter(status='Recebido').aggregate(models.Sum('valor_recebido'))['valor_recebido__sum'] or Decimal('0.00')


    @property
    def total_pago_arquiteto(self):
        """
        Calcula o total efetivamente pago de RT para a arquiteta.
        Usa 'valor_pago' se disponível, caso contrário usa o valor nominal.
        """
        # Filtra apenas comissões ativas e com status 'Pago'
        comissoes_pagas = self.comissoes_pagar.filter(is_deleted=False, status='Pago')
        
        # Soma: Se tiver valor_pago (real), usa ele. Se não, usa valor_comissao (previsto).
        total = sum((c.valor_pago or c.valor_comissao) for c in comissoes_pagas)
        return total
    # --- ADICIONE ISTO ---
    @property
    def total_previsto_financeiro(self):
        """Soma total das parcelas geradas no contas a receber"""
        return self.parcelas_receber.aggregate(models.Sum('valor'))['valor__sum'] or Decimal('0.00')

    @property
    def qtd_parcelas_pendentes(self):
        """Retorna quantas parcelas ainda não foram recebidas"""
        return self.parcelas_receber.filter(status='Pendente').count()

    @property
    def status_pagamento(self):
        total = self.parcelas_receber.count()
        if total == 0:
            return "Sem Financeiro"
        
        pendentes = self.qtd_parcelas_pendentes
        pagas = total - pendentes
        
        if pendentes == 0:
            return "Quitado"
        elif pagas > 0:
            return f"Parcial ({pagas}/{total} pagas)"
        return f"Pendente ({pendentes} restantes)"
    class Meta:
        verbose_name = "Contrato de RT"
        verbose_name_plural = "Contratos de RT"
        ordering = ['-data_contrato']
    
    def __str__(self):
        return f"{self.arquiteta.nome} - {self.cliente.nome_completo}"