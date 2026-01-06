from django import forms

from .models import (CategoriaSocio,  # <--- Adicione Socio aqui
                     LancamentoSocio, Socio)


class LancamentoSocioForm(forms.ModelForm):
    class Meta:
        model = LancamentoSocio
        fields = ['socio', 'data', 'categoria', 'valor', 'observacao']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacao': forms.TextInput(attrs={'class': 'form-control'}),
            'socio': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select select2'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordena para aparecer agrupado (Ex: Tudo de Habitação junto)
        self.fields['categoria'].queryset = CategoriaSocio.objects.order_by('grupo', 'nome')
        
        # Opcional: Modificar o label do dropdown para mostrar o grupo
        self.fields['categoria'].label_from_instance = lambda obj: f"{obj.get_grupo_display()} > {obj.nome}"


class SocioForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = ['nome'] # Se você adicionou CPF no model, coloque 'cpf' aqui também
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: João da Silva'}),
            # 'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
        }