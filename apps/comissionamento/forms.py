from django import forms
from .models import Arquiteta, ContratoRT

class ArquitetaForm(forms.ModelForm):
    class Meta:
        model = Arquiteta
        fields = ['nome', 'cpf', 'banco', 'agencia', 'conta']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ContratoRTForm(forms.ModelForm):
    class Meta:
        model = ContratoRT
        fields = [
            'arquiteta', 'cliente', 'data_contrato', 
            'percentual', 'valor_servico', 'valor_rt', # Percentual adicionado
            'data_pagamento', 'valor_pago', 'observacoes'
        ]
        widgets = {
            'arquiteta': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'data_contrato': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'percentual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_servico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_rt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }