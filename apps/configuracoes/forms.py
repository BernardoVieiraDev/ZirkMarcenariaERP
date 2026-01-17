from django import forms
from .models import ConfiguracaoGlobal

class ConfiguracaoGlobalForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoGlobal
        fields = [
            'lixeira_ativa', 
            'dias_retencao_lixeira', 
            'limpeza_automatica_ativa', 
            'meses_retencao_historico',
        ]
        widgets = {
            'lixeira_ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'limpeza_automatica_ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dias_retencao_lixeira': forms.NumberInput(attrs={'class': 'form-control'}),
            'meses_retencao_historico': forms.NumberInput(attrs={'class': 'form-control',  'min': '1'}),
        }


class AdminCreationForm(forms.Form):
    username = forms.CharField(
        label="Nome de Usuário",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: BernardoVieira'})
    )
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apenas números ou com pontuação'})
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )