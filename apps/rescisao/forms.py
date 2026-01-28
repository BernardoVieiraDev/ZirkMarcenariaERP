from django import forms
from django.forms import inlineformset_factory
from .models import Rescisao, ItemRescisao

class RescisaoForm(forms.ModelForm):
    class Meta:
        model = Rescisao
        fields = '__all__' # Os campos "outro_*" não existem mais, então não darão erro, mas certifique-se de rodar makemigrations
        widgets = {
            'data_demissao': forms.DateInput(attrs={'type': 'date'},  format='%Y-%m-%d'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['desc_faltas'].widget.attrs['placeholder'] = 'Ex: 04, 23, 25/09'

# Configuração do Formset
ItemRescisaoFormSet = inlineformset_factory(
    Rescisao, 
    ItemRescisao,
    fields=['descricao', 'valor', 'tipo'],
    extra=1, # Começa com 1 linha vazia extra
    can_delete=True,
    widgets={
        'descricao': forms.TextInput(attrs={'placeholder': 'Ex: Bônus Meta', 'class': 'form-control'}),
        'valor': forms.NumberInput(attrs={'placeholder': '0.00', 'class': 'form-control'}),
        'tipo': forms.Select(attrs={'class': 'form-select'}),
    }
)