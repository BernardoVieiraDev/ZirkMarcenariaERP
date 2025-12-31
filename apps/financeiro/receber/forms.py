from django import forms

from .models import Banco, CaixaDiario, MovimentoBanco, Receber


class ReceberForm(forms.ModelForm):
    class Meta:
        model = Receber
        fields = ['forma_de_recebimento','tipo_recebimento','data_vencimento','cliente','categoria','valor',
                  'valor_estoque','observacoes','data_pagamento']

        widgets = {'data_vencimento': forms.DateInput(attrs={'type':'date'}, format='%Y-%m-%d'),
                   'data_pagamento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                   'tipo_recebimento': forms.Select(attrs={'class': 'form-control'})
                   
                   }

class CaixaDiarioForm(forms.ModelForm):
    class Meta:
        model = CaixaDiario
        fields = ['data', 'tipo', 'descricao', 'valor', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Café, Motoboy, Sangria...'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nome', 'agencia', 'conta', 'saldo_inicial']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Banco do Brasil, Santander...'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class MovimentoBancoForm(forms.ModelForm):
    class Meta:
        model = MovimentoBanco
        fields = ['data', 'tipo', 'descricao', 'valor', 'observacoes'] # O campo 'banco' será injetado na view
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Pagto Fornecedor, Recebimento Cartão...'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }