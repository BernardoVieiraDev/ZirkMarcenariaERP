from django import forms
from .models import Empreitada, PagamentoEmpreitada

class EmpreitadaForm(forms.ModelForm):
    class Meta:
        model = Empreitada
        fields = ['funcionario', 'cliente', 'ambiente', 'valor_total', 'data_inicio', 'status', 'descricao']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'ambiente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Cozinha Planejada'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PagamentoEmpreitadaForm(forms.ModelForm):
    class Meta:
        model = PagamentoEmpreitada
        fields = ['data', 'valor', 'observacao']
        widgets = {
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacao': forms.TextInput(attrs={'class': 'form-control'}),
        }