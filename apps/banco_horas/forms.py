from django import forms
from .models import LancamentoHoras

class LancamentoHorasForm(forms.ModelForm):
    class Meta:
        model = LancamentoHoras
        fields = ['funcionario', 'horas', 'motivo']

        widgets = {
            'motivo': forms.TextInput(attrs={'placeholder': 'Ex: horas extras, desconto, etc.'})
        }
