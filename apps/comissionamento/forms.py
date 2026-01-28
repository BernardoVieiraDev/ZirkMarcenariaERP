from decimal import Decimal
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
    # Campos extras para controle do financeiro
    gerar_financeiro = forms.BooleanField(
        initial=True, required=False, label="Gerar Comissão a Pagar Automaticamente?"
    )
    banco_pagamento = forms.ModelChoiceField(
        queryset=Banco.objects.all(), 
        required=False,  # Banco agora é opcional
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
        
        # Define valor_rt como não obrigatório no formulário para permitir
        # que o usuário deixe em branco (acionando o cálculo automático no clean)
        self.fields['valor_rt'].required = False

        # Se o formulário já tem uma instância (está editando), 
        # desativamos a geração automática para evitar duplicidade ou erros.
        if self.instance and self.instance.pk:
            self.fields['gerar_financeiro'].initial = False
            self.fields['gerar_financeiro'].widget = forms.HiddenInput()
            self.fields['banco_pagamento'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # --- LÓGICA DE CÁLCULO AUTOMÁTICO ---
        valor_rt = cleaned_data.get('valor_rt')
        valor_servico = cleaned_data.get('valor_servico')
        percentual = cleaned_data.get('percentual')

        # Se o usuário não preencheu o Valor da RT, mas preencheu serviço e percentual:
        if not valor_rt and valor_servico and percentual:
            # Calcula: (Serviço * Percentual) / 100
            novo_valor_rt = (valor_servico * percentual) / 100
            
            # Arredonda e atribui ao cleaned_data e à instância
            cleaned_data['valor_rt'] = novo_valor_rt.quantize(Decimal('0.01'))
            self.instance.valor_rt = cleaned_data['valor_rt']

        # --- VALIDAÇÃO DE BANCO REMOVIDA ---
        # A validação que obrigava o banco foi removida conforme solicitado.
        # O sistema aceitará gerar financeiro com 'banco_origem' NULL.
        
        return cleaned_data