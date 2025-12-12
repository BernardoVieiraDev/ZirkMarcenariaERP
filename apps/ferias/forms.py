from django import forms
from apps.funcionarios.models import Funcionario  

from .models import Ferias, PagamentoFerias, PeriodoAquisitivo


class PeriodoAquisitivoForm(forms.ModelForm):
    class Meta:
        model = PeriodoAquisitivo
        fields = ['funcionario', 'data_inicio', 'data_fim', 'dias_direito']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }

class FeriasForm(forms.ModelForm):
    class Meta:
        model = Ferias
        fields = ['periodo',  'dias_tirados',
                  'faltas_justificadas_descontadas', 'ferias_no_recesso_final_ano', 'ferias_no_carnaval', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }


class PagamentoFeriasForm(forms.ModelForm):
    class Meta:
        model = PagamentoFerias
        fields = [
            'funcionario',
            'vencimento',
            'valor_a_pagar',
            'data_pagamento',
            'observacoes',
            'data_recibo_contabilidade',
            'observacoes_recibo_contabilidade'
        ]
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            'data_recibo_contabilidade': forms.DateInput(attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'observacoes_recibo_contabilidade': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exibe salários no select
        self.fields['funcionario'].queryset = Funcionario.objects.all()
        self.fields['funcionario'].label_from_instance = lambda obj: (
    f"{obj.nome} — Salário: R$ {getattr(obj.dados_trabalhistas, 'salario', 0):.2f}"
)