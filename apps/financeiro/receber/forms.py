from django import forms
from .models import Receber


class ReceberForm(forms.ModelForm):
    class Meta:
        model = Receber
        fields = ['forma_de_recebimento','data_vencimento','cliente','categoria','valor',
                  'valor_estoque','observacoes','data_pagamento']

        widgets = {'data_vencimento': forms.DateInput(attrs={'type':'date'}),
                   'data_pagamento': forms.DateInput(attrs={'type': 'date'})}

