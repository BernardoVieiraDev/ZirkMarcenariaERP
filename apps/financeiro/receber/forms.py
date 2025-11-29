from django import forms
from .models import Receber


class ReceberForm(forms.ModelForm):
    class Meta:
        model = Receber
        fields = ['cliente','desc','value','when','status']
        widgets = {'when': forms.DateInput(attrs={'type':'date'})}

