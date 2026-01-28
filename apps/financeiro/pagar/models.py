from decimal import Decimal

from django.db import models

from apps.comissionamento.models import Arquiteta
from apps.configuracoes.mixin import SoftDeleteMixin
from apps.funcionarios.models import Funcionario


class ParcelamentoPagar(SoftDeleteMixin):
    """
    Entidade pai que agrupa diversas contas (parcelas).
    """
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Parcelamento")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    # Congelamos o valor total original aqui para facilitar consultas
    valor_total_original = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    qtd_parcelas = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Parcelamento (A Pagar)"
        verbose_name_plural = "Gestão de Parcelamentos"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.descricao} ({self.qtd_parcelas}x)"

    # --- Lógica de Negócio (Dashboards) ---

    def get_related_objects(self):
        """
        Retorna todas as parcelas vinculadas, independente da classe filha (Boleto, Cheque, etc).
        Como GastoBase é abstrata, precisamos varrer os reverse relations conhecidos ou
        usar uma lógica polimórfica. Aqui, faremos uma busca dinâmica simples.
        """
        parcelas = []
        # Lista de related_names gerados pelo GastoBase no padrão 'parcelas_NOMECLASSE'
        # Você deve garantir que os models filhos herdam de GastoBase
        modelos_filhos = [
            'parcelas_boleto', 'parcelas_gastogeral', 'parcelas_cheque', 
            'parcelas_faturacartao', 'parcelas_gastoveiculoconsorcio',
            'parcelas_gastocontabilidade', 'parcelas_gastoimovel', 
            'parcelas_gastoutilidade', 'parcelas_gastogasolina',
            'parcelas_comissaoarquiteto', 'parcelas_gastoalmoco'
        ]
        
        for related in modelos_filhos:
            if hasattr(self, related):
                manager = getattr(self, related)
                parcelas.extend(list(manager.filter(is_deleted=False)))
        
        # Ordena por vencimento
        parcelas.sort(key=lambda x: x.data_vencimento if hasattr(x, 'data_vencimento') else x.data_gasto)
        return parcelas

    @property
    def resumo(self):
        """Retorna dicionário com status atualizado"""
        parcelas = self.get_related_objects()
        total_obj = len(parcelas)
        if total_obj == 0:
            return {'pendente': 0, 'pago': 0, 'progresso': 0, 'valor_pago': 0, 'valor_aberto': 0}

        pagas = [p for p in parcelas if p.status in ['Pago', 'Recebido', 'PG', 'COM']]
        qtd_pagas = len(pagas)
        
        valor_pago = sum([p.get_valor_consolidado() for p in pagas])
        # O valor total atual pode diferir do original se houver juros nas parcelas
        valor_total_atual = sum([p.get_valor_consolidado() for p in parcelas])
        valor_aberto = valor_total_atual - valor_pago

        progresso = (qtd_pagas / total_obj) * 100

        return {
            'total_parcelas': total_obj,
            'qtd_pagas': qtd_pagas,
            'qtd_pendentes': total_obj - qtd_pagas,
            'progresso': round(progresso, 1),
            'valor_pago': valor_pago,
            'valor_aberto': valor_aberto,
            'valor_total_atual': valor_total_atual
        }


    
    # ... resto da classe ...

class FormaPagamento(models.TextChoices):
    DINHEIRO = 'DINHEIRO', 'Dinheiro'
    PIX = 'PIX', 'Pix'
    DEBITO = 'DEBITO', 'Cartão de Débito'
    CREDITO = 'CREDITO', 'Cartão de Crédito'
    BOLETO = 'BOLETO', 'Boleto'
    TRANSFERENCIA = 'TRANSFERENCIA', 'Transferência'
    OUTROS = 'OUTROS', 'Outros'

class StatusPagamento(models.TextChoices):
    PENDENTE = 'Pendente', 'Pendente'
    PAGO = 'Pago', 'Pago'
    ATRASADO = 'Atrasado', 'Atrasado'


class GastoBase(SoftDeleteMixin):
    """
    Classe Abstrata Base.
    - Para contas que 'nascem pagas': 'valor' é o valor pago e 'data_vencimento' é a data do pagamento.
    - Para contas 'a pagar': 'valor' é o valor nominal/previsto e 'data_vencimento' é o vencimento do título.
    """

    parcelamento = models.ForeignKey(
            ParcelamentoPagar, 
            on_delete=models.CASCADE, # Se apagar o pai, apaga as parcelas (ou use PROTECT/SET_NULL conforme regra)
            null=True, 
            blank=True,
            related_name='parcelas_%(class)s', # Ex: parcelas_boleto, parcelas_cheque
            verbose_name="Vínculo de Parcelamento"
        )


    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.SET_NULL,  
        null=True, 
        blank=True, 
        verbose_name="Conta Bancária"
    )
    
    # Vínculos automáticos
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.SET_NULL,  
        null=True, 
        blank=True,
        related_name='%(class)s_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT,  # Alterado para PROTECT
        null=True, 
        blank=True,
        related_name='%(class)s_origem'
    )
    credor = models.CharField(
        max_length=150, 
        verbose_name="Credor / Fornecedor", 
        null=True, 
        blank=True,
        help_text="Nome da empresa ou pessoa que receberá o pagamento (Igual à planilha)"
    )

    descricao = models.CharField(
        max_length=255, 
        verbose_name="Descrição do Gasto",
        blank=True 
    )
    
    # Este é o valor PRINCIPAL (Nominal para boletos, Pago para despesas imediatas)
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor",
        default=Decimal('0.00'),
        null=True
    )
    
    # Esta é a data PRINCIPAL (Vencimento para boletos, Data do Gasto para despesas imediatas)
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    
    observacoes = models.TextField(null=True, blank=True, verbose_name="Observações")
    
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PENDENTE, db_index=True)
    
    forma_pagamento = models.CharField(
            max_length=20,
            choices=FormaPagamento.choices,
            default=FormaPagamento.BOLETO,
            verbose_name="Forma de Pagamento"
        )
    
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
        indexes = [
            models.Index(fields=['data_vencimento', 'status']),
        ]
        
    def __str__(self):
        """Representação padrão caso a sub-classe não defina."""
        identificacao = self.descricao or self.credor or "Despesa"
        valor_fmt = f"R$ {self.valor}" if self.valor else "R$ 0,00"
        return f"{identificacao} - {valor_fmt}"

    def get_valor_consolidado(self):
        """Retorna o valor principal por padrão."""
        return self.valor 
            
    def get_data_consolidada(self):
        return self.data_vencimento
    
    def get_model_name(self):
        return self.MODEL_NAMES.get(self.__class__.__name__, self.__class__.__name__)

    def get_tipo_classe(self):
            return self.__class__.__name__

# ==============================================================================
# CLASSES QUE PRECISAM DE CONTROLE "A PAGAR" vs "PAGO" (Boleto, Consórcio)
# Adicionamos manualmente os campos de pagamento aqui.
# ==============================================================================

class Boleto(GastoBase):
    nota_fiscal = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nota Fiscal")
    
    # Campos específicos para controle de pagamento diferido
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do Pagamento")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago")
    juros = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Juros/Multa", null=True, blank=True)

    class Meta:
        verbose_name = "Boleto"
        verbose_name_plural = "Boletos"

    def __str__(self):
        desc = self.descricao or self.credor or "Boleto"
        if self.nota_fiscal:
            return f"{desc} (NF: {self.nota_fiscal})"
        return f"{desc} - {self.data_vencimento.strftime('%d/%m')}"

    def get_valor_consolidado(self):
        """Para fluxo de caixa: se já pagou, retorna o valor pago (com juros). Se não, o nominal."""
        if self.status in [StatusPagamento.PAGO, 'Pago'] and self.valor_pago:
            return self.valor_pago
        return self.valor

class GastoVeiculoConsorcio(GastoBase):
    TIPO_GASTO_CHOICES = [
        ('CONS', 'Consórcio'),
        ('IPVA', 'IPVA'),
        ('SEGURO', 'Seguro'),
        ('LICEN', 'Licenciamento'),
        ('OUTRO', 'Outro Gasto Veicular'),
    ]
    
    tipo_gasto = models.CharField(max_length=10, choices=TIPO_GASTO_CHOICES, verbose_name="Tipo de Gasto")
    veiculo_referencia = models.CharField(max_length=100, null=True, blank=True, verbose_name="Veículo/Consórcio")
    
    # Campos específicos para controle de pagamento diferido
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento Real")
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago Real")
    juros = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Juros/Multa", null=True, blank=True)

    class Meta:
        verbose_name = "Gasto de Veículo/Consórcio"
        verbose_name_plural = "Consórcios e Carros"

    def __str__(self):
        tipo = self.get_tipo_gasto_display()
        veiculo = f" - {self.veiculo_referencia}" if self.veiculo_referencia else ""
        return f"{tipo}{veiculo}"

    def get_valor_consolidado(self):
        if self.status in [StatusPagamento.PAGO, 'Pago'] and self.valor_pago:
            return self.valor_pago
        return self.valor

# ==============================================================================
# CLASSES QUE "NASCEM PAGAS" (Utilizam apenas a estrutura Base simplificada)
# 'valor' = valor pago | 'data_vencimento' = data do pagamento
# ==============================================================================

class GastoUtilidade(GastoBase):
    TIPO_CHOICES = [
        ('CEL', 'Celulares'),
        ('CESAN_ALPHA', 'Cesan - Alphaville'),
        ('ESC_MARCENARIA', 'Escelsa - Marcenaria'), 
        ('INT_ALPHA', 'Internet - Alphaville'),
        ('CESAN_MARCENARIA', 'Cesan - Marcenaria'), 
        ('ESC_ALPHA', 'Escelsa - Alphaville'), 
        ('INT_MARCENARIA', 'Internet - Marcenaria'),
    ]
    tipo_cliente = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Cliente/Tipo de Utilidade")

    class Meta:
        verbose_name = "Gasto com Utilidade"
        verbose_name_plural = "Água, Luz e Telefone"
    
    def __str__(self):
        # Ex: Escelsa - Alphaville (05/2024)
        return f"{self.get_tipo_cliente_display()} ({self.data_vencimento.strftime('%m/%Y')})"

class FaturaCartao(GastoBase):
    TIPO_CHOICES = [
        ('PF_SICOOB', 'Sicoob PF'),
        ('PF_BRADESCO', 'Bradesco PF'),
        ('BNDES', 'Cartão BNDES'),
    ]
    cartao = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Cartão/Conta")

    class Meta:
        verbose_name = "Fatura de Cartão"
        verbose_name_plural = "Faturas de Cartão"

    def __str__(self):
        return f"Fatura {self.get_cartao_display()} - {self.data_vencimento.strftime('%m/%Y')}"

class PrestacaoEmprestimo(GastoBase):
    prestacao = models.IntegerField(null=True, blank=True, verbose_name="Prestação")
    
    class Meta:
        verbose_name = "Prestação de Empréstimo"
        verbose_name_plural = "Prestações de Empréstimos"
    
    def __str__(self):
        return f"{self.descricao or 'Empréstimo'} - Parc. {self.prestacao or '?'}"

class GastoContabilidade(GastoBase):
    TIPO_CHOICES = [
        ('SIMPLES', 'DAS Simples'),
        ('FGTS', 'FGTS'),
        ('HONORARIO', 'Honorário Contábil'),
        ('INSS', 'INSS'),
        ('IR', 'Imposto de Renda'),
        ('SeguroFuncionarios', 'Seguro dos Funcionarios'),
    ]
    tipo_gasto = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Encargo")
    
    class Meta:
        verbose_name = "Gasto Contábil"
        verbose_name_plural = "Encargos e Contabilidade"

    def __str__(self):
        return f"{self.get_tipo_gasto_display()} - {self.data_vencimento.strftime('%m/%Y')}"

class GastoImovel(GastoBase):
    TIPO_CHOICES = [
        ('IPTU', 'IPTU'),
        ('CONDO', 'Condomínio (Alphaville)'),
        ('TAXA', 'Taxa de Averbação'),
        ('ACORDO', 'Acordo de Condomínio'),
    ]
    
    local_lote = models.CharField(max_length=150, verbose_name="Local/Lote (Referência)", null=True, blank=True)
    numero_inscricao = models.CharField(max_length=50, verbose_name="Número de Inscrição", null=True, blank=True)
    tipo_gasto = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo de Gasto Imobiliário")
    
    class Meta:
        verbose_name = "Gasto Imobiliário"
        verbose_name_plural = "IPTU e Condomínios"

    def __str__(self):
        return f"{self.get_tipo_gasto_display()} - {self.local_lote or ''}"

# ==============================================================================
# CLASSES INDEPENDENTES (Não herdam de GastoBase ou já possuem estrutura própria)
# ==============================================================================

# Em zirk_rh_financeiro/apps/financeiro/pagar/models.py

class Cheque(SoftDeleteMixin):
    TIPO_ENTIDADE_CHOICES = [('F', 'Física'), ('J', 'Jurídica')]
    
    # ALTERADO: A opção 'Compensado' agora grava o valor 'Pago'
    STATUS_CHOICES = [
        ('EMI', 'Emitido'),
        ('Pago', 'Compensado'),  # Valor: Pago, Label: Compensado
        ('DEV', 'Devolvido'),
        ('CAN', 'Cancelado')
    ]    
    
    descricao = models.CharField(max_length=255, verbose_name="Despesa")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    numero_cheque = models.CharField(max_length=20, verbose_name="Nº do Cheque")
    
    # ALTERADO: max_length aumentado para 20 (era 3) para aceitar 'Pago'
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='EMI', verbose_name="Status")
    
    tipo_entidade = models.CharField(max_length=1, choices=TIPO_ENTIDADE_CHOICES, verbose_name="Tipo de Entidade")

    parcelamento = models.ForeignKey(
        ParcelamentoPagar, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='parcelas_%(class)s',
        verbose_name="Vínculo de Parcelamento"
    )

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        related_name='cheque_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        related_name='cheque_origem_origem'
    )

    class Meta:
        verbose_name = "Cheque"
        verbose_name_plural = "Cheques"

    def __str__(self):
        return f"Cheque {self.numero_cheque} - {self.descricao}"

    def get_model_name(self): return self.__class__.__name__
    def get_valor_consolidado(self): return self.valor
    def get_data_consolidada(self): return self.data_emissao
    def get_tipo_classe(self): return self.__class__.__name__ 

class Emprestimo(SoftDeleteMixin):
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Empréstimo")
    valor_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Total do Empréstimo")
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_final_prevista = models.DateField(verbose_name="Data Final Prevista")
    
    def __str__(self): return self.descricao

class Pessoa(models.Model):
    TIPO_CHOICES = [('FUNC', 'Funcionário')]
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=4, choices=TIPO_CHOICES)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_entrada = models.DateField(null=True, blank=True)
    def __str__(self): return self.nome

class PagamentoFuncionario(models.Model):
    # PROTECT mantido (já estava correto no código original para Funcionario)
    funcionario = models.ForeignKey(Pessoa, on_delete=models.PROTECT, limit_choices_to={'tipo': 'FUNC'}, verbose_name="Funcionário")
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

class ComissaoArquiteto(SoftDeleteMixin):
    arquiteto = models.ForeignKey(Arquiteta, on_delete=models.PROTECT, verbose_name="Arquiteta")
    
    # RENOMEADO: De data_pagamento para data_vencimento (Data prevista)
    data_vencimento = models.DateField(verbose_name="Data de Vencimento / Previsão")
    
    # NOVO CAMPO: Data real do pagamento (só preenche quando pagar)
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data do Pagamento Real")
    
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Comissão")
    
    # NOVO CAMPO: Valor efetivamente pago
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Pago Real")
    
    observacoes = models.TextField(null=True, blank=True, verbose_name="Observações")
    forma_pagamento = models.CharField(max_length=20, choices=FormaPagamento.choices, default=FormaPagamento.PIX, verbose_name="Forma de Pagamento")
    
    # ALTERADO: Default para PENDENTE (nasce como conta a pagar)
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PENDENTE)
    
    parcelamento = models.ForeignKey(
        ParcelamentoPagar, 
        on_delete=models.CASCADE, # Se apagar o pai, apaga as parcelas (ou use PROTECT/SET_NULL conforme regra)
        null=True, 
        blank=True,
        related_name='parcelas_%(class)s', # Ex: parcelas_boleto, parcelas_cheque
        verbose_name="Vínculo de Parcelamento"
    )

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='comissao_arquiteto_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='comissao_arquiteto_origem'
    )

    contrato_rt = models.ForeignKey(
        'comissionamento.ContratoRT',
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True,
        blank=True,
        related_name='comissoes_pagar',
        verbose_name="Contrato RT Vinculado"
    )

    class Meta:
        verbose_name = "Comissão de Arquiteto"
        verbose_name_plural = "Comissões de Arquitetos"

    def __str__(self):
        return f"Comissão: {self.arquiteto} - {self.valor_comissao}"

    # Lógica ajustada para considerar o valor pago se o status for 'Pago'
    def get_valor_consolidado(self): 
        if self.status in [StatusPagamento.PAGO, 'Pago'] and self.valor_pago:
            return self.valor_pago
        return self.valor_comissao
    
    # A data principal para ordenação passa a ser o Vencimento
    def get_data_consolidada(self): 
        return self.data_vencimento
        
    def get_model_name(self): return self.__class__.__name__
    def get_tipo_classe(self): return self.__class__.__name__

    
class GastoGeral(SoftDeleteMixin):
    credor = models.CharField(max_length=150, verbose_name="Credor / Fornecedor", null=True, blank=True)
    forma_pagamento = models.CharField(max_length=20, choices=FormaPagamento.choices, verbose_name="Forma de Pagamento", null=True, blank=True, default=FormaPagamento.PIX)
    FORMA_PAGAMENTO_CHOICES = [('PIX', 'Pix'), ('DINHEIRO', 'Dinheiro'), ('CARTAO', 'Cartão')]
    TIPO_PAGAMENTO_CHOICES = [('VISTA', 'À Vista'), ('PRAZO', 'A Prazo')]
    
    tipo_pagamento = models.CharField(max_length=10, choices=TIPO_PAGAMENTO_CHOICES, default='VISTA', verbose_name="Classificação Gerencial")
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Item")
    data_gasto = models.DateField(verbose_name="Data do Gasto")
    
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total", null=True, blank=True)
    valor_dinheiro_pix = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor em Pix/Dinheiro", null=True, blank=True)
    valor_cartao = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor em Cartão", null=True, blank=True)
    forma_principal_pagamento = models.CharField(max_length=10, choices=FORMA_PAGAMENTO_CHOICES, verbose_name="Forma de Pagamento", null=True, blank=True)

    motorista = models.CharField(max_length=100, null=True, blank=True)
    carro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Carro/Veículo")
    cliente = models.CharField(max_length=150, null=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PAGO)

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='gasto_geral_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='gasto_geral_origem'
    )

    class Meta:
        verbose_name = "Gasto Geral"
        verbose_name_plural = "Gastos Gerais (Almoço, Material, etc.)"

    def __str__(self):
        return f"{self.descricao} - {self.valor_total}"

    def get_valor_consolidado(self): return self.valor_total
    def get_data_consolidada(self): return self.data_gasto
    def get_model_name(self): return self.__class__.__name__
    def get_tipo_classe(self): return self.__class__.__name__

class GastoGasolina(SoftDeleteMixin):
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Item")
    data_gasto = models.DateField(verbose_name="Data do Gasto")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    carro = models.CharField(max_length=50, null=True, blank=True, verbose_name="Carro/Veículo")
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PAGO)
    

    forma_pagamento = models.CharField(
        max_length=20, 
        choices=FormaPagamento.choices, 
        default=FormaPagamento.PIX, 
        verbose_name="Forma de Pagamento"
    )

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='gasto_gasolina_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='gasto_gasolina_origem'
    )

    class Meta:
        verbose_name = "Gasto com Gasolina"
        verbose_name_plural = "Gastos com Gasolina"

    def __str__(self):
        return f"Combustível: {self.descricao} ({self.valor_total})"
        
    def get_valor_consolidado(self): return self.valor_total
    def get_data_consolidada(self): return self.data_gasto
    def get_model_name(self): return self.__class__.__name__
    def get_tipo_classe(self): return self.__class__.__name__

class FolhaPagamento(SoftDeleteMixin):
    @property
    def credor(self): return "Pessoal"
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name="Funcionário")
    data_referencia = models.DateField(verbose_name="Mês de Referência")
    salario_real = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Salário Real/Combinado")
    adiantamento = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Adiantamento")
    ferias_terco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="1/3 Férias")
    empreitada = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Empreitadas")
    decimo_terceiro = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="13º Salário")
    vale = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Vales")
    horas_extras_valor = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Horas Extras (R$)")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    val_ferias = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Férias")
    
    ferias_terco = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="1/3 Férias")


    parcelamento = models.ForeignKey(
        ParcelamentoPagar, 
        on_delete=models.CASCADE, # Se apagar o pai, apaga as parcelas (ou use PROTECT/SET_NULL conforme regra)
        null=True, 
        blank=True,
        related_name='parcelas_%(class)s', # Ex: parcelas_boleto, parcelas_cheque
        verbose_name="Vínculo de Parcelamento"
    )

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='folha_pagamento_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT, # Alterado para PROTECT
        null=True, 
        blank=True, 
        related_name='folha_pagamento_origem'
    )

    forma_pagamento = models.CharField(max_length=20, choices=FormaPagamento.choices, default=FormaPagamento.PIX, verbose_name="Forma de Pagamento")
    status = models.CharField('Status', max_length=20, choices=StatusPagamento.choices, default=StatusPagamento.PENDENTE)

    referencia_holerite = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        default="30d", 
        verbose_name="Referência (ex: 30d)"
    )

    class Meta:
        verbose_name = "Pagamento de Folha"
        verbose_name_plural = "Pagamentos de Folha"
        ordering = ['-data_referencia', 'funcionario__nome']

    def __str__(self): return f"{self.funcionario.nome} - {self.data_referencia.strftime('%m/%Y')}"

    @property
    def total_funcionario(self):
        return (self.salario_real + self.ferias_terco + self.empreitada + self.decimo_terceiro + self.horas_extras_valor)
    
    def get_valor_consolidado(self): return self.total_funcionario
    def get_model_name(self): return self.__class__.__name__
    def get_tipo_classe(self): return self.__class__.__name__
    def get_data_consolidada(self): return self.data_referencia


class GastoAlmoco(SoftDeleteMixin):
    funcionario = models.ForeignKey(
        Funcionario, 
        on_delete=models.PROTECT, 
        verbose_name="Funcionário"
    )
    # --- ALTERADO: De restaurante para observacoes (TextField) ---
    observacoes = models.TextField(verbose_name="Observações", null=True, blank=True)
    # -------------------------------------------------------------
    
    descricao = models.CharField(default=f"Almoço", max_length=255, verbose_name="Descrição (Opcional)", null=True, blank=True)
    data_gasto = models.DateField(verbose_name="Data do Almoço")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    
    forma_pagamento = models.CharField(
        max_length=20, 
        choices=FormaPagamento.choices, 
        default=FormaPagamento.PIX, 
        verbose_name="Forma de Pagamento"
    )
    status = models.CharField(
        'Status', 
        max_length=20, 
        choices=StatusPagamento.choices, 
        default=StatusPagamento.PAGO
    )

    banco_origem = models.ForeignKey(
        'receber.Banco', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        verbose_name="Conta de Saída"
    )
    movimento_banco = models.OneToOneField(
        'receber.MovimentoBanco', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        related_name='gasto_almoco_origem'
    )
    movimento_caixa = models.OneToOneField(
        'receber.CaixaDiario', 
        on_delete=models.PROTECT,
        null=True, 
        blank=True, 
        related_name='gasto_almoco_origem'
    )

    origem_pagamento = models.CharField(
        max_length=10,
        choices=[('BANCO', 'Banco'), ('CAIXA', 'Caixa')],
        default='BANCO',
        verbose_name="Origem do Pagamento"
    )
    
    parcelamento = models.ForeignKey(
        ParcelamentoPagar, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='parcelas_%(class)s',
        verbose_name="Vínculo de Parcelamento"
    )

    class Meta:
        verbose_name = "Gasto com Almoço"
        verbose_name_plural = "Almoços de Funcionários"

    def __str__(self):
        # Atualizado para remover referência a self.restaurante
        return f"Almoço: {self.funcionario.nome} - R$ {self.valor_total}"

    def save(self, *args, **kwargs):
        # Se não houver descrição, gera uma automática baseada no funcionário
        if not self.descricao and self.funcionario:
            self.descricao = f"Almoço - {self.funcionario.nome}"
        
        super().save(*args, **kwargs)

    @property
    def descricao_formatada(self):
        """Retorna a descrição salva ou um padrão 'Almoço - Funcionario'"""
        if self.descricao:
            return self.descricao
        if self.funcionario:
            return f"Almoço - {self.funcionario.nome}"
        return "Gasto com Almoço"
    def get_valor_consolidado(self): return self.valor_total
    def get_data_consolidada(self): return self.data_gasto
    def get_model_name(self): return "Almoço"
    def get_tipo_classe(self): return self.__class__.__name__