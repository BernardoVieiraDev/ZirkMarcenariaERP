from django import forms
from .models import Pagar

class PagarForm(forms.ModelForm):
    class Meta:
        model = Pagar
        fields = [
            'desc',
            'nota_fiscal',
            'value',
            'valor_pago',
            'juros',
            'data_pagamento',
            'due',
            'status',
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'input-text'}),
            'value': forms.NumberInput(attrs={'class': 'input-number', 'step': '0.01'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            'due': forms.DateInput(attrs={'type': 'date'}),

        }

        labels = {
            'descricao': 'Descrição',
            'value': 'Valor',
        }


