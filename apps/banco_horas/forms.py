# zirk_rh_financeiro/apps/banco_horas/forms.py

from django import forms
from .models import LancamentoHoras, BancoHoras

class LancamentoHorasForm(forms.ModelForm):
    class Meta:
        model = LancamentoHoras
        fields = ['funcionario', 'horas', 'valor_hora', 'data', 'descricao'] # 'data' incluído
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # Widget de data crucial para o usuário escolher o dia
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }