from django import forms
from .models import Banco, CaixaDiario, MovimentoBanco, Receber

class ReceberForm(forms.ModelForm):
    class Meta:
        model = Receber
        fields = [
            'descricao', 
            'cliente', 
            'categoria',
            'valor',
            'data_vencimento', 
            'tipo_recebimento', 
            'forma_recebimento', 
            'status',
            'valor_recebido',
            'data_recebimento',
            'banco_destino',
            'observacoes',
        ]
        widgets = {
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_recebimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_recebido': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tipo_recebimento': forms.Select(attrs={'class': 'form-control'}),
            'banco_destino'
            '': forms.Select(attrs={'class': 'form-select'}),
            'forma_recebimento': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CaixaDiarioForm(forms.ModelForm):
    class Meta:
        model = CaixaDiario
        fields = ['data', 'historico', 'tipo', 'valor']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'historico': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nome', 'agencia', 'conta', 'saldo_inicial']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control'}),
            'conta': forms.TextInput(attrs={'class': 'form-control'}),
            'saldo_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class MovimentoBancoForm(forms.ModelForm):
    class Meta:
        model = MovimentoBanco
        fields = ['banco', 'data', 'historico', 'tipo', 'valor']
        widgets = {
            'banco': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'historico': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }