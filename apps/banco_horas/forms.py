from django import forms
from .models import LancamentoHoras

class LancamentoHorasForm(forms.ModelForm):
    class Meta:
        model = LancamentoHoras
        fields = ['funcionario', 'horas', 'valor_hora']

        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'Ex: 2.5 ou -1.0'}),
            'valor_hora': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'R$ 0,00'}),
        }
