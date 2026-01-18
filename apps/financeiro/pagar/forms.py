# minha_app/forms.py

from decimal import Decimal
from django import forms

# Importa todos os modelos necessários
from .models import (Boleto, Cheque, ComissaoArquiteto, Emprestimo,
                     FaturaCartao, FolhaPagamento, GastoContabilidade,
                     GastoGasolina, GastoGeral, GastoImovel, GastoUtilidade,
                     GastoVeiculoConsorcio, PagamentoFuncionario, Pessoa,
                     PrestacaoEmprestimo, StatusPagamento, FormaPagamento)

# ----------------------------------------------------
# 1. ESCOLHA INICIAL DO TIPO DE GASTO
# ----------------------------------------------------
GASTO_MODEL_CHOICES = [
    ('Boleto', 'Boleto'),
    ('GastoUtilidade', 'Água, Luz e Telefone'),
    ('Cheque', 'Cheque'),
    ('GastoContabilidade', 'Encargos e Contabilidade'),
    ('PrestacaoEmprestimo', 'Prestação de Empréstimo'),
    ('FaturaCartao', 'Fatura de Cartão / BNDES'),
    ('GastoGeral', 'Gastos Gerais (Almoço, Material, etc.)'),
    ('GastoVeiculoConsorcio', 'Consórcios e Carros (IPVA/Seguro)'),
    ('GastoImovel', 'IPTU e Condomínio (Alphaville)'),
    ('GastoGasolina', 'Gastos com Gasolina'),
    ('FolhaPagamento', 'Folha de pagamento'),
    ('ComissaoArquiteto', 'Comissão Arquiteto'),
]



class TipoGastoForm(forms.Form):
    categoria = forms.ChoiceField(
        choices=[('', '--- Selecione a Categoria ---')] + GASTO_MODEL_CHOICES,
        label='Categoria (Modelo Django)',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'categoria-selector'})
    )

# ----------------------------------------------------
# 2. FORMULÁRIO BASE ABSTRATO (Refatorado)
# ----------------------------------------------------

class GastoBaseForm(forms.ModelForm):
    ORIGEM_CHOICES = [
        ('BANCO', 'Conta Bancária'),
        ('CAIXA', 'Caixa Interno (Dinheiro)'),
    ]
    origem_pagamento = forms.ChoiceField(
        choices=ORIGEM_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='BANCO',
        label="Origem do Recurso"
    )

    parcelas = forms.IntegerField(
        initial=1, min_value=1, label="Parcelamento", required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Qtd Parcelas'})
    )

    class Meta:
        fields = [
            'origem_pagamento', # Adicionado
            'descricao',
            'valor',
            'data_vencimento',
            'banco_origem',
            'status',
            'forma_pagamento',
            'observacoes',
        ]
        
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'banco_origem': forms.Select(attrs={'class': 'form-select'}),
            'data_vencimento': forms.DateInput( 
                attrs={'type': 'date', 'class': 'form-control'}, 
                format='%Y-%m-%d'
                ),         
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        origem = cleaned_data.get('origem_pagamento')
        banco = cleaned_data.get('banco_origem')

        # --- LÓGICA CORRIGIDA ---
        
        if origem == 'CAIXA':
            # 1. Se é Caixa, FORÇA o banco a ser vazio
            cleaned_data['banco_origem'] = None
            
            # 2. FORÇA a forma de pagamento para "DINHEIRO" automaticamente
            cleaned_data['forma_pagamento'] = 'DINHEIRO'
            
            # 3. Se houver erro de "Campo obrigatório" no banco, removemos o erro
            if 'banco_origem' in self._errors:
                del self._errors['banco_origem']
        
        elif origem == 'BANCO':
            # Se é Banco, aí sim exigimos que o usuário tenha selecionado um banco
            if not banco:
                self.add_error('banco_origem', 'Selecione uma conta bancária para esta operação.')

        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banco_origem'].required = False
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                 field.widget.attrs['class'] = 'form-control'


# ----------------------------------------------------
# 3. FORMULÁRIOS ESPECÍFICOS (Herança + Campos Extras)
# ----------------------------------------------------

class BoletoForm(GastoBaseForm):
    """Adiciona de volta os campos de pagamento que foram retirados do base"""
    class Meta:
        model = Boleto 
        # Mantemos a definição dos fields como está
        fields = GastoBaseForm.Meta.fields + ['nota_fiscal', 'valor_pago', 'data_pagamento', 'juros']
        widgets = GastoBaseForm.Meta.widgets.copy()
        
        widgets['nota_fiscal'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['valor_pago'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['juros'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['data_pagamento'] = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove o campo forma_pagamento para que o usuário não precise selecionar.
        # O Model Boleto já possui default=FormaPagamento.BOLETO, que será usado automaticamente.
        if 'forma_pagamento' in self.fields:
            del self.fields['forma_pagamento']

class GastoVeiculoConsorcioForm(GastoBaseForm):
    """Adiciona de volta os campos de pagamento"""
    class Meta:
        model = GastoVeiculoConsorcio
        fields = ['tipo_gasto', 'veiculo_referencia'] + GastoBaseForm.Meta.fields + ['valor_pago', 'data_pagamento', 'juros']
        widgets = GastoBaseForm.Meta.widgets.copy()
        
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})
        widgets['veiculo_referencia'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['valor_pago'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['juros'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['data_pagamento'] = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d')


# Os formulários abaixo NÃO recebem valor_pago/data_pagamento, 
# pois usam 'valor' e 'data_vencimento' como dados efetivos.

class GastoUtilidadeForm(GastoBaseForm):
    class Meta:
        model = GastoUtilidade
        fields = ['tipo_cliente'] + GastoBaseForm.Meta.fields 
        widgets = GastoBaseForm.Meta.widgets
        widgets['tipo_cliente'] = forms.Select(attrs={'class': 'form-select'})

class FaturaCartaoForm(GastoBaseForm):
    class Meta:
        model = FaturaCartao
        base_fields = GastoBaseForm.Meta.fields[:]
        fields = ['cartao'] + base_fields 
        widgets = GastoBaseForm.Meta.widgets
        widgets['cartao'] = forms.Select(attrs={'class': 'form-select'})

class PrestacaoEmprestimoForm(GastoBaseForm):
    class Meta:
        model = PrestacaoEmprestimo
        fields = GastoBaseForm.Meta.fields + ['prestacao']
        widgets = GastoBaseForm.Meta.widgets
        widgets['prestacao'] = forms.NumberInput(attrs={'class': 'form-control'})

class GastoContabilidadeForm(GastoBaseForm):
    class Meta:
        model = GastoContabilidade
        fields = GastoBaseForm.Meta.fields + ['tipo_gasto']
        widgets = GastoBaseForm.Meta.widgets
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})

class GastoImovelForm(GastoBaseForm):
    class Meta:
        model = GastoImovel
        fields = GastoBaseForm.Meta.fields + ['numero_inscricao', 'tipo_gasto','local_lote']
        widgets = GastoBaseForm.Meta.widgets
        widgets['numero_inscricao'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['local_lote'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})


# ----------------------------------------------------
# 4. FORMULÁRIOS INDEPENDENTES (Sem mudanças drásticas, apenas manutenção)
# ----------------------------------------------------

class ChequeForm(forms.ModelForm):
    parcelas = forms.IntegerField(
    initial=1, min_value=1, label="Parcelamento", required=False,
    widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Qtd Parcelas'})
    )
    class Meta:
        model = Cheque
        fields = 'descricao', 'valor','parcelas', 'data_emissao', 'numero_cheque', 'status','banco_origem', 'tipo_entidade'
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),      
            'numero_cheque': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tipo_entidade': forms.Select(attrs={'class': 'form-select'}),
        }

        

class GastoGeralForm(forms.ModelForm):
    ORIGEM_CHOICES = [
        ('BANCO', 'Conta Bancária'),
        ('CAIXA', 'Caixa Interno (Dinheiro)'),
    ]
    origem_pagamento = forms.ChoiceField(
        choices=ORIGEM_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input', 
            'onclick': 'toggleBancoField()'
        }),
        initial='BANCO',
        label="Origem do Recurso"
    )

    class Meta:
        model = GastoGeral
        fields = [
            'credor',
            'descricao',
            'data_gasto',
            'valor_total',
            'valor_dinheiro_pix',
            'valor_cartao',
            'forma_principal_pagamento',
            'motorista',
            'carro',
            'cliente',
            'tipo_pagamento',
            'status',
            'forma_pagamento',
            'banco_origem',  # <--- ADICIONE ESTE CAMPO
        ]
        widgets = {
            'credor': forms.TextInput(attrs={'class': 'form-control'}), 
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_gasto': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_dinheiro_pix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_cartao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'forma_principal_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'motorista': forms.TextInput(attrs={'class': 'form-control'}),
            'carro': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_pagamento': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['banco_origem'].required = False
        
        # Define inicial na edição
        if self.instance.pk:
            if self.instance.movimento_caixa:
                self.fields['origem_pagamento'].initial = 'CAIXA'
            elif self.instance.banco_origem:
                self.fields['origem_pagamento'].initial = 'BANCO'

    def clean(self):
        cleaned_data = super().clean()
        origem = cleaned_data.get('origem_pagamento')
        banco = cleaned_data.get('banco_origem')
        status = cleaned_data.get('status')

        # --- LÓGICA CORRIGIDA ---

        if origem == 'CAIXA':
            cleaned_data['banco_origem'] = None
            cleaned_data['forma_pagamento'] = 'DINHEIRO' # <--- Adicionado
            
            if 'banco_origem' in self._errors:
                del self._errors['banco_origem']
        
        elif origem == 'BANCO' and status == 'Pago' and not banco:
            self.add_error('banco_origem', 'Selecione a conta bancária para confirmar o pagamento.')

        return cleaned_data

class GastoGasolinaForm(GastoGeralForm):
    class Meta(GastoGeralForm.Meta):
        model = GastoGasolina
        fields = [
            'descricao',
            'data_gasto',
            'valor_total',
            'carro',
            'status',
            'forma_pagamento',
            'banco_origem', # Necessário pois é usado na lógica de clean() do GastoGeralForm
        ]

class PagamentoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = PagamentoFuncionario
        fields = '__all__'
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'mes_referencia': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}, format='%Y-%m-%d'),
            'salario_real': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'adiantamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'terco_ferias': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'empreitadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'decimo_terceiro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_liquido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
        }

# Em zirk_rh_financeiro/apps/financeiro/pagar/forms.py

class ComissaoArquitetoForm(forms.ModelForm):
    parcelas = forms.IntegerField(
        initial=1, min_value=1, label="Parcelamento", required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Qtd Parcelas'})
    )

    class Meta:
        model = ComissaoArquiteto
        fields = [
            'arquiteto',
            'data_vencimento',
            'data_pagamento',
            'valor_pago',
            'valor_comissao',
            'observacoes',
            'forma_pagamento',
            'status',
            'banco_origem',
        ]
        widgets = {
            'arquiteto': forms.Select(attrs={'class': 'form-select'}),
            'data_vencimento': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'data_pagamento': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'
            ),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_comissao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'banco_origem': forms.Select(attrs={'class': 'form-select'}),
        }

    
    # Adicionando validação básica de banco (igual ao GastoBaseForm)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'banco_origem' in self.fields:
            self.fields['banco_origem'].required = False

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        banco = cleaned_data.get('banco_origem')
        data_pgto = cleaned_data.get('data_pagamento')

        # Se marcar como Pago, exige Data de Pagamento e Banco (se for o caso)
        if status == 'Pago':
            if not data_pgto:
                 self.add_error('data_pagamento', 'Informe a data do pagamento para baixar o registro.')
            # Adicione aqui logica de banco se necessário
            
        return cleaned_data


class FolhaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FolhaPagamento
        fields = [
            'funcionario', 'data_referencia', 'salario_real', 'adiantamento',
            'ferias_terco', 'empreitada', 'decimo_terceiro', 'vale',
            'horas_extras_valor','referencia_holerite', 'observacoes'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-control select2', 'placeholder': 'Selecione o funcionário'}),
            'data_referencia': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'salario_real': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'adiantamento': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'ferias_terco': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'empreitada': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'decimo_terceiro': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'vale': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'horas_extras_valor': forms.NumberInput(attrs={'class': 'form-control money-mask', 'step': '0.01'}),
            'referencia_holerite': forms.TextInput(attrs={
                'class': 'form-control form-control-sm text-center p-0', 
                'style': 'width: 50px;' # Força o tamanho pequeno
            }),            
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    

class ConfirmarPagamentoForm(forms.Form):
    data_pagamento = forms.DateField(
        label="Data do Pagamento",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    valor_pago = forms.DecimalField(
        label="Valor Pago (R$)",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        required=True
    )
    banco_origem = forms.ModelChoiceField(
        queryset=None, # Será populado no __init__
        label="Conta de Saída / Banco",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Deixe em branco se foi pago em Dinheiro/Caixa"
    )
    observacoes = forms.CharField(
        label="Observações do Pagamento",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )
    forma_pagamento = forms.ChoiceField(
        choices=FormaPagamento.choices,
        label="Forma de Pagamento",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        # Precisamos importar o Banco aqui para evitar import circular se houver
        from apps.financeiro.receber.models import Banco
        super().__init__(*args, **kwargs)
        self.fields['banco_origem'].queryset = Banco.objects.all()