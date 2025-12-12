from django import forms
from .models import LancamentoHoras

class LancamentoHorasForm(forms.ModelForm):
    class Meta:
        model = LancamentoHoras
        fields = ['funcionario', 'horas']

        widgets = {
        }
