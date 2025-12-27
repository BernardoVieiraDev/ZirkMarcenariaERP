from django import forms
from .models import Rescisao

class RescisaoForm(forms.ModelForm):
    class Meta:
        model = Rescisao
        fields = '__all__'
        widgets = {
            'data_demissao': forms.DateInput(attrs={'type': 'date'},  format='%Y-%m-%d'),
            'outro_tipo': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Placeholder para ajudar no preenchimento
        self.fields['desc_faltas'].widget.attrs['placeholder'] = 'Ex: 04, 23, 25/09'
        self.fields['outro_nome'].widget.attrs['placeholder'] = 'Ex: Bônus Meta ou Quebra de Caixa'