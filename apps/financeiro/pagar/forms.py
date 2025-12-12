# minha_app/forms.py

from decimal import \
    Decimal  # Boas práticas de precisão, embora menos crítico em Forms do que Models

from django import forms

# Importa todos os modelos necessários
from .models import (Boleto, Cheque, ComissaoArquiteto, Emprestimo,
                     FaturaCartao, GastoContabilidade, GastoGasolina,
                     GastoGeral, GastoImovel, GastoUtilidade,
                     GastoVeiculoConsorcio, PagamentoFuncionario,
                     Pessoa, PrestacaoEmprestimo, StatusPagamento, FolhaPagamento)

# ----------------------------------------------------
# 1. ESCOLHA INICIAL DO TIPO DE GASTO (Para a UX dinâmica)
# ----------------------------------------------------

# Lista de todos os Modelos de Gasto a Pagar (o valor deve ser o nome da classe do modelo)
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
    ('FolhaPagamento', 'Folha de pagamento')
]

class TipoGastoForm(forms.Form):
    """Formulário inicial para o usuário selecionar a categoria do gasto."""
    categoria = forms.ChoiceField(
        choices=[('', '--- Selecione a Categoria ---')] + GASTO_MODEL_CHOICES,
        label='Categoria (Modelo Django)',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'categoria-selector'})
    )



# ----------------------------------------------------
# 2. FORMULÁRIO BASE ABSTRATO (Herdado por modelos GastoBase)
# ----------------------------------------------------

class GastoBaseForm(forms.ModelForm):
    """
    Formulário Base. Define campos e widgets comuns a todos os modelos que herdam de GastoBase.
    Este formulário não será instanciado diretamente.
    """
    class Meta:
        # A lista de campos é definida aqui para ser reusada pelos filhos.
        fields = [
            'descricao',
            'valor',
            'data_vencimento',
            'data_pagamento',
            'valor_pago',
            'juros',
            'status',
            'observacoes',
        ]
        
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'juros': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            'data_vencimento': forms.DateInput( 
                attrs={'type': 'date', 'class': 'form-control'}, 
                format='%Y-%m-%d' # Formato exigido pelo HTML5 input type="date"        
                ),         
            
            'data_pagamento': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d' # Formato exigido pelo HTML5 input type="date"
            ),            
            
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplica uma classe CSS padrão para todos os campos (pode ser usado para Bootstrap)
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                 field.widget.attrs['class'] = 'form-control'


# ----------------------------------------------------
# 3. FORMULÁRIOS ESPECÍFICOS (Herança de GastoBaseForm)
# ----------------------------------------------------

# Campos: GastoBase + nota_fiscal
class BoletoForm(GastoBaseForm):
    class Meta:
        model = Boleto 
        fields = GastoBaseForm.Meta.fields + ['nota_fiscal']
        widgets = GastoBaseForm.Meta.widgets
        widgets['nota_fiscal'] = forms.TextInput(attrs={'class': 'form-control'})


# Campos: GastoBase + tipo_cliente
class GastoUtilidadeForm(GastoBaseForm):
    class Meta:
        model = GastoUtilidade
        fields = GastoBaseForm.Meta.fields + ['tipo_cliente']
        widgets = GastoBaseForm.Meta.widgets
        widgets['tipo_cliente'] = forms.Select(attrs={'class': 'form-select'})


# Campos: GastoBase + cartao
class FaturaCartaoForm(GastoBaseForm):
    class Meta:
        model = FaturaCartao
        # Manter a lógica de remoção da descrição:
        base_fields = GastoBaseForm.Meta.fields[:]
        fields = base_fields + ['cartao']
        widgets = GastoBaseForm.Meta.widgets
        widgets['cartao'] = forms.Select(attrs={'class': 'form-select'})
# Campos: GastoBase + emprestimo, numero_parcela
class PrestacaoEmprestimoForm(GastoBaseForm):
    class Meta:
        model = PrestacaoEmprestimo
        fields = GastoBaseForm.Meta.fields + ['prestacao']
        widgets = GastoBaseForm.Meta.widgets
        widgets['prestacao'] = forms.NumberInput(attrs={'class': 'form-control'})


# Campos: GastoBase + -, veiculo_referencia
class GastoVeiculoConsorcioForm(GastoBaseForm):
    class Meta:
        model = GastoVeiculoConsorcio
        fields = GastoBaseForm.Meta.fields + ['tipo_gasto', 'veiculo_referencia']
        widgets = GastoBaseForm.Meta.widgets
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})
        widgets['veiculo_referencia'] = forms.TextInput(attrs={'class': 'form-control'})

# Campos: GastoBase + 
class GastoContabilidadeForm(GastoBaseForm):
    class Meta:
        model = GastoContabilidade
        fields = GastoBaseForm.Meta.fields + ['tipo_gasto']
        widgets = GastoBaseForm.Meta.widgets
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})


# Campos: GastoBase + imovel, tipo_gasto
class GastoImovelForm(GastoBaseForm):
    class Meta:
        model = GastoImovel
        fields = GastoBaseForm.Meta.fields + ['numero_inscricao', 'tipo_gasto','local_lote']
        widgets = GastoBaseForm.Meta.widgets
        widgets['numero_inscricao'] = forms.TextInput(attrs={'class': 'form-select'})
        widgets['local_lote'] = forms.TextInput(attrs={'class': 'form-select'})
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})


# ----------------------------------------------------
# 4. FORMULÁRIOS INDEPENDENTES (Modelos sem GastoBase)
# ----------------------------------------------------

# Modelo Cheque
class ChequeForm(forms.ModelForm):
    class Meta:
        model = Cheque
        fields = '__all__'
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),

            'data_emissao': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d' # Formato exigido pelo HTML5 input type="date"
            ),      
            
            'numero_cheque': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tipo_entidade': forms.Select(attrs={'class': 'form-select'}),
        }


# Modelo GastoGeral (e Gasolina, que é proxy)
class GastoGeralForm(forms.ModelForm):
    class Meta:
        model = GastoGeral
        fields = '__all__'
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'data_gasto': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_dinheiro_pix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_cartao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'forma_principal_pagamento': forms.Select(attrs={'class': 'form-select'}),
            'motorista': forms.TextInput(attrs={'class': 'form-control'}),
            'carro': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
        'status': forms.Select(attrs={'class': 'form-select'}), # Novo widget
        }

# Modelo GastoGasolina (usa o mesmo form, mas você pode personalizá-lo se necessário)
class GastoGasolinaForm(GastoGeralForm):
    class Meta(GastoGeralForm.Meta):
        model = GastoGasolina
        # Não precisa redefinir fields, usa a mesma lógica de GastoGeralForm.

# Modelo PagamentoFuncionario (RH)
class PagamentoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = PagamentoFuncionario
        fields = '__all__'
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'mes_referencia': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
            'salario_real': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'adiantamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'terco_ferias': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'empreitadas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'decimo_terceiro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_liquido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Modelo ComissaoArquiteto (RH)
class ComissaoArquitetoForm(forms.ModelForm):
    class Meta:
        model = ComissaoArquiteto
        fields = '__all__'
        widgets = {
            'arquiteto': forms.Select(attrs={'class': 'form-select'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_comissao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class FolhaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FolhaPagamento
        fields = [
            'funcionario',
            'data_referencia',
            'salario_real',
            'adiantamento',
            'ferias_terco',
            'empreitada',
            'decimo_terceiro',
            'vale',
            'horas_extras_valor',
            'observacoes'
        ]
        widgets = {
            'funcionario': forms.Select(attrs={
                'class': 'form-control select2',  # Adicione 'select2' se usar essa lib para busca
                'placeholder': 'Selecione o funcionário'
            }),
            'data_referencia': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'salario_real': forms.NumberInput(attrs={
                'class': 'form-control money-mask', # Classe para máscaras de JS se tiver
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'adiantamento': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'ferias_terco': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'empreitada': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'decimo_terceiro': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'vale': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'horas_extras_valor': forms.NumberInput(attrs={
                'class': 'form-control money-mask',
                'step': '0.01',
                'placeholder': 'R$ 0,00'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações adicionais sobre o pagamento...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Definir labels personalizados se não vierem do verbose_name do model
        # self.fields['funcionario'].label = "Colaborador"