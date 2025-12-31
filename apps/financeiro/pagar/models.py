from decimal import Decimal
from django.db import models
from apps.funcionarios.models import Funcionario
from apps.comissionamento.models import Arquiteta


class StatusPagamento(models.TextChoices):
    PENDENTE = 'Pendente', 'Pendente'
    PAGO = 'Pago', 'Pago'
    ATRASADO = 'Atrasado', 'Atrasado'


class GastoBase(models.Model):
    """
    Classe Abstrata Base para reusar campos comuns em todos os modelos de gastos.
    """
    descricao = models.CharField(
        max_length=255, 
        verbose_name="Descrição do Gasto",
        blank=True 
    )
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor",
        default=Decimal('0.00'),
        null=True
    )
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago")
    juros = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Juros/Multa", null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True, verbose_name="Observações")
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PENDENTE)

    # Dicionário com nomes legíveis para cada modelo
    MODEL_NAMES = {
        "Boleto": "Boleto",
        "GastoUtilidade": "Utilidade",
        "FaturaCartao": "Fatura de Cartão",
        "Cheque": "Cheque",
        "PrestacaoEmprestimo": "Prestação de Empréstimo",
        "GastoVeiculoConsorcio": "Veículo Consórcio",
        "GastoContabilidade": "Contabilidade",
        "GastoImovel": "Imóvel",
        "GastoGeral": "Gasto Geral",
        "GastoGasolina": "Gasolina",
        "FolhaPagamento": "Folha de Pagamento",
        "ComissaoArquiteto": "Comissão de Arquiteto",
        "Emprestimo": "Empréstimo",
        "Pessoa": "Pessoa",
    }

    class Meta:
        abstract = True
        ordering = ['-data_vencimento']

    def get_valor_consolidado(self):
        return self.valor 
            
    def get_data_consolidada(self):
        return self.data_vencimento
    
    def get_model_name(self):
        """Retorna o nome amigável do modelo."""
        return self.MODEL_NAMES.get(self.__class__.__name__, self.__class__.__name__)


class Boleto(GastoBase):
    nota_fiscal = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="Nota Fiscal"
    )

    class Meta:
        verbose_name = "Boleto"
        verbose_name_plural = "Boletos"

class GastoUtilidade(GastoBase):
    TIPO_CHOICES = [
        ('CEL', 'Celulares'),
        ('CESAN_ALPHA', 'Cesan - Alphaville'),
        ('ESC_MARCENARIA', 'Escelsa - Marcenaria'), 
        ('INT_ALPHA', 'Internet - Alphaville'),
        ('CESAN_MARCENARIA', 'Cesan - Marcenaria'), 
        ('ESC_ALPHA', 'Escelsa - Alphaville'), 
        ('INT_MARCENARIA', 'Internet - Marcenaria'),
        # Adicione outros tipos conforme necessário
    ]
    tipo_cliente = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name="Cliente/Tipo de Utilidade"
    )

    class Meta:
        verbose_name = "Gasto com Utilidade"
        verbose_name_plural = "Água, Luz e Telefone"

class FaturaCartao(GastoBase):
    TIPO_CHOICES = [
        ('PF_SICOOB', 'Sicoob PF'),
        ('PF_BRADESCO', 'Bradesco PF'),
        ('BNDES', 'Cartão BNDES'),
        # Adicione outros cartões
    ]
    cartao = models.CharField(
        max_length=50,
        choices=TIPO_CHOICES,
        verbose_name="Cartão/Conta"
    )

    class Meta:
        verbose_name = "Fatura de Cartão"
        verbose_name_plural = "Faturas de Cartão"

class Cheque(models.Model):
    TIPO_ENTIDADE_CHOICES = [
        ('F', 'Física'),
        ('J', 'Jurídica'),
    ]
    STATUS_CHOICES = [
        ('EMI', 'Emitido'),
        ('COM', 'Compensado'),
        ('DEV', 'Devolvido'),
        ('CAN', 'Cancelado'),
    ]

    descricao = models.CharField(max_length=255, verbose_name="Despesa")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    numero_cheque = models.CharField(max_length=20, unique=True, verbose_name="Nº do Cheque")
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='EMI', verbose_name="Status")
    tipo_entidade = models.CharField(max_length=1, choices=TIPO_ENTIDADE_CHOICES, verbose_name="Tipo de Entidade")

    class Meta:
        verbose_name = "Cheque"
        verbose_name_plural = "Cheques"

    def get_model_name(self):
        return self.__class__.__name__

    def get_valor_consolidado(self):
        """Retorna o valor para a lista unificada."""
        return self.valor

    def get_data_consolidada(self):
        """Retorna a data de emissão para a lista unificada."""
        return self.data_emissao
        

class Emprestimo(models.Model):
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Empréstimo")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total do Empréstimo")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_final_prevista = models.DateField(verbose_name="Data Final Prevista")
    
    def __str__(self):
        return self.descricao

class PrestacaoEmprestimo(GastoBase):

    prestacao = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Prestação"
    )
    
    class Meta:
        verbose_name = "Prestação de Empréstimo"
        verbose_name_plural = "Prestações de Empréstimos"


class GastoVeiculoConsorcio(GastoBase):
    TIPO_GASTO_CHOICES = [
        ('CONS', 'Consórcio'),
        ('IPVA', 'IPVA'),
        ('SEGURO', 'Seguro'),
        ('LICEN', 'Licenciamento'),
        ('OUTRO', 'Outro Gasto Veicular'),
    ]
    
    tipo_gasto = models.CharField(
        max_length=10,
        choices=TIPO_GASTO_CHOICES,
        verbose_name="Tipo de Gasto"
    )
    veiculo_referencia = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Veículo/Consórcio" 
    )

    class Meta:
        verbose_name = "Gasto de Veículo/Consórcio"
        verbose_name_plural = "Consórcios e Carros"


class Pessoa(models.Model):
    TIPO_CHOICES = [
        ('FUNC', 'Funcionário'),
    ]
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=4, choices=TIPO_CHOICES)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_entrada = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.nome

# Modelo para o registro mensal de pagamento (Folha)
class PagamentoFuncionario(models.Model):
    funcionario = models.ForeignKey(
        Pessoa, 
        on_delete=models.PROTECT, 
        limit_choices_to={'tipo': 'FUNC'}, 
        verbose_name="Funcionário"
    )
    mes_referencia = models.DateField(verbose_name="Mês de Referência")
    salario_real = models.DecimalField(max_digits=10, decimal_places=2)
    adiantamento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    terco_ferias = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    empreitadas = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    decimo_terceiro = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_liquido = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Pago")

    class Meta:
        verbose_name = "Pagamento de Funcionário"
        verbose_name_plural = "Folha de Pagamento"
        unique_together = ('funcionario', 'mes_referencia')

# Modelo para as comissões de arquitetos
class ComissaoArquiteto(models.Model):
    arquiteto = models.ForeignKey(
        Arquiteta,
        on_delete=models.PROTECT,
        verbose_name="Arquiteta"
    )
    data_pagamento = models.DateField()
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(null=True, blank=True)
    
    # Campo adicionado para compatibilidade com a view
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PAGO 
    )

    class Meta:
        verbose_name = "Comissão de Arquiteto"
        verbose_name_plural = "Comissões de Arquitetos"

    def get_valor_consolidado(self):
        return self.valor_comissao

    def get_model_name(self):
        return self.__class__.__name__


class GastoContabilidade(GastoBase):
    TIPO_CHOICES = [
        ('SIMPLES', 'DAS Simples'),
        ('FGTS', 'FGTS'),
        ('HONORARIO', 'Honorário Contábil'),
        ('INSS', 'INSS'),
        ('IR', 'Imposto de Renda'),
        ('SeguroFuncionarios', 'Seguro dos Funcionarios'),
        # Adicione outros
    ]
    tipo_gasto = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Encargo"
    )
    
    class Meta:
        verbose_name = "Gasto Contábil"
        verbose_name_plural = "Encargos e Contabilidade"


class GastoImovel(GastoBase):
    TIPO_CHOICES = [
        ('IPTU', 'IPTU'),
        ('CONDO', 'Condomínio (Alphaville)'),
        ('TAXA', 'Taxa de Averbação'),
        ('ACORDO', 'Acordo de Condomínio'),
    ]
    
    local_lote = models.CharField(
            max_length=150,
            verbose_name="Local/Lote (Referência)",
            null=True,
            blank=True
        )
    
    numero_inscricao = models.CharField(
        max_length=50,
        verbose_name="Número de Inscrição",
        null=True,
        blank=True
    )
    
    tipo_gasto = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Gasto Imobiliário"
    )
    
    class Meta:
        verbose_name = "Gasto Imobiliário"
        verbose_name_plural = "IPTU e Condomínios"


class GastoGeral(models.Model):
    FORMA_PAGAMENTO_CHOICES = [
        ('PIX', 'Pix'),
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão'),
    ]

    TIPO_PAGAMENTO_CHOICES = [
        ('VISTA', 'À Vista'),
        ('PRAZO', 'A Prazo'),
    ]
    tipo_pagamento = models.CharField(
        max_length=10,
        choices=TIPO_PAGAMENTO_CHOICES,
        default='VISTA', # Padrão À Vista, pois gastos gerais costumam ser do dia a dia
        verbose_name="Classificação Gerencial"
    )
    
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Item")
    data_gasto = models.DateField(verbose_name="Data do Gasto")
    
    # Valores de Pagamento
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total", null=True, blank=True)
    valor_dinheiro_pix = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor em Pix/Dinheiro", null=True, blank=True)
    valor_cartao = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor em Cartão", null=True, blank=True)
    forma_principal_pagamento = models.CharField(max_length=10, choices=FORMA_PAGAMENTO_CHOICES, verbose_name="Forma de Pagamento", null=True, blank=True)

    # Campos Adicionais
    motorista = models.CharField(max_length=100, null=True, blank=True)
    carro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Carro/Veículo")
    cliente = models.CharField(max_length=150, null=True, blank=True)
    
    status = models.CharField(
            'Status',
            max_length=20,
            choices=StatusPagamento.choices,
            default=StatusPagamento.PAGO, # Valor sugerido para gastos gerais pagos no ato.
        )

    class Meta:
        verbose_name = "Gasto Geral"
        verbose_name_plural = "Gastos Gerais (Almoço, Material, etc.)"

    # ✅ CORRIGIDO: Getter de Valor Consolidado (Usa valor_total)
    def get_valor_consolidado(self):
        return self.valor_total

    # ✅ CORRIGIDO: Getter de Data Consolidada (Usa data_gasto)
    def get_data_consolidada(self):
        return self.data_gasto
        
    def get_model_name(self):
        return self.__class__.__name__


class GastoGasolina(models.Model):
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Item")
    data_gasto = models.DateField(verbose_name="Data do Gasto")
    
    # Valores de Pagamento
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")

    carro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Carro/Veículo")
    
    status = models.CharField(
            'Status',
            max_length=20,
            choices=StatusPagamento.choices,
            default=StatusPagamento.PAGO, # Valor sugerido para gastos gerais pagos no ato.
        )

    class Meta:
        verbose_name = "Gasto com Gasolina"
        verbose_name_plural = "Gastos com Gasolina"
        
    # ✅ CORRIGIDO: Getter de Valor Consolidado (Usa valor_total)
    def get_valor_consolidado(self):
        return self.valor_total

    # ✅ CORRIGIDO: Getter de Data Consolidada (Usa data_gasto)
    def get_data_consolidada(self):
        return self.data_gasto
        
    def get_model_name(self):
        return self.__class__.__name__

class FolhaPagamento(models.Model):
    """
    Registra os pagamentos variáveis de um funcionário em um mês específico.
    """
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name="Funcionário")
    data_referencia = models.DateField(verbose_name="Mês de Referência")
    
    # Valores Fixos/Base (podem ser puxados auto, mas bom ter histórico)
    salario_real = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Salário Real/Combinado")
    
    # Variáveis do Mês
    adiantamento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Adiantamento")
    ferias_terco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="1/3 Férias")
    empreitada = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Empreitadas")
    decimo_terceiro = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="13º Salário")
    vale = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Vales")
    horas_extras_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Horas Extras (R$)")
    
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    # Campo adicionado para compatibilidade com a view
    status = models.CharField(
        'Status',
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE
    )

    class Meta:
        verbose_name = "Pagamento de Folha"
        verbose_name_plural = "Pagamentos de Folha"
        ordering = ['-data_referencia', 'funcionario__nome']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.data_referencia.strftime('%m/%Y')}"

    @property
    def total_funcionario(self):
        """Soma todos os proventos registrados neste objeto."""
        return (
            self.salario_real + 
            self.ferias_terco + 
            self.empreitada + 
            self.decimo_terceiro + 
            self.horas_extras_valor
            # Note: Adiantamento e Vale geralmente são descontos do líquido, 
            # mas se a planilha é de "Custo" ou "Saída de Caixa", eles somam como dinheiro que saiu.
            # Vou somar tudo como 'Saída de Caixa' para a empresa.
            # Se a lógica for Saldo a Pagar, teria que subtrair.
        )
    
    # Método adicionado para compatibilidade com a view
    def get_valor_consolidado(self):
        return self.total_funcionario

    def get_model_name(self):
        return self.__class__.__name__