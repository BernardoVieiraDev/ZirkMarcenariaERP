from django import forms

from apps.clientes.models import Cliente
from apps.financeiro.pagar.models import FormaPagamento
from apps.financeiro.receber.models import Banco

from .models import Arquiteta, ContratoRT


class ArquitetaForm(forms.ModelForm):
    class Meta:
        model = Arquiteta
        fields = ['nome', 'cpf', 'banco', 'agencia', 'conta']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '000.000.000-00'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ContratoRTForm(forms.ModelForm):
    # Campos extras mantidos...
    gerar_financeiro = forms.BooleanField(
        initial=True, required=False, label="Gerar Comissão a Pagar Automaticamente?"
    )
    banco_pagamento = forms.ModelChoiceField(
        queryset=Banco.objects.all(), 
        required=False, 
        label="Conta/Banco de Saída",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    qtd_parcelas = forms.IntegerField(
        initial=1, min_value=1, required=False, label="Qtd. Parcelas",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    primeiro_vencimento = forms.DateField(
        required=False, label="Data 1ª Parcela",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    forma_pagamento = forms.ChoiceField(
        choices=FormaPagamento.choices, 
        initial=FormaPagamento.PIX,
        required=False, 
        label="Forma de Pagamento",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ContratoRT
        fields = [
            'arquiteta', 'cliente', 'data_contrato', 
            'valor_servico', 'percentual', 'valor_rt', 
            'observacoes'
        ]
        # (Widgets mantidos iguais ao seu código original)
        widgets = {
            'arquiteta': forms.Select(attrs={'class': 'form-select select2'}),
            'cliente': forms.Select(attrs={'class': 'form-select select2'}),
            'data_contrato': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_servico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_rt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CORREÇÃO PARA A EDIÇÃO:
        # Se o formulário já tem uma instância (está editando), 
        # desativamos a geração automática para evitar erro de validação do banco.
        if self.instance and self.instance.pk:
            self.fields['gerar_financeiro'].initial = False
            self.fields['gerar_financeiro'].widget = forms.HiddenInput()
            # Opcional: Você pode esconder os outros campos também se desejar
            self.fields['banco_pagamento'].required = False

    def clean(self):
        cleaned_data = super().clean()
        gerar = cleaned_data.get('gerar_financeiro')
        banco = cleaned_data.get('banco_pagamento')
        
        # Só valida banco se for criar financeiro
        if gerar and not banco:
            self.add_error('banco_pagamento', 'Selecione um banco para gerar o financeiro.')
        
        return cleaned_data