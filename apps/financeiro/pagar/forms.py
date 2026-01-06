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
    """
    Formulário Base. 
    REMOVIDOS: valor_pago, data_pagamento, juros (pois nem todos os filhos usam).
    """
    class Meta:
        fields = [
            'descricao',
            'valor',
            'data_vencimento',
            "banco_origem",
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # Adiciona nota_fiscal E os campos de pagamento exclusivos
        fields = GastoBaseForm.Meta.fields + ['nota_fiscal', 'valor_pago', 'data_pagamento', 'juros']
        widgets = GastoBaseForm.Meta.widgets.copy()
        
        # Widgets extras
        widgets['nota_fiscal'] = forms.TextInput(attrs={'class': 'form-control'})
        widgets['valor_pago'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['juros'] = forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        widgets['data_pagamento'] = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d')


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
        widgets['numero_inscricao'] = forms.TextInput(attrs={'class': 'form-select'})
        widgets['local_lote'] = forms.TextInput(attrs={'class': 'form-select'})
        widgets['tipo_gasto'] = forms.Select(attrs={'class': 'form-select'})


# ----------------------------------------------------
# 4. FORMULÁRIOS INDEPENDENTES (Sem mudanças drásticas, apenas manutenção)
# ----------------------------------------------------

class ChequeForm(forms.ModelForm):
    class Meta:
        model = Cheque
        fields = '__all__'
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_emissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),      
            'numero_cheque': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'tipo_entidade': forms.Select(attrs={'class': 'form-select'}),
        }

class GastoGeralForm(forms.ModelForm):
    class Meta:
        model = GastoGeral
        fields = '__all__'
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

class GastoGasolinaForm(GastoGeralForm):
    class Meta(GastoGeralForm.Meta):
        model = GastoGasolina

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

class ComissaoArquitetoForm(forms.ModelForm):
    class Meta:
        model = ComissaoArquiteto
        fields = '__all__'
        widgets = {
            'arquiteto': forms.Select(attrs={'class': 'form-select'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor_comissao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select'}),
        }

class FolhaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FolhaPagamento
        fields = [
            'funcionario', 'data_referencia', 'salario_real', 'adiantamento',
            'ferias_terco', 'empreitada', 'decimo_terceiro', 'vale',
            'horas_extras_valor', 'observacoes'
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
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }