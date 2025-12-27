from django import forms
from django.core.exceptions import ValidationError
from .models import Ferias, PeriodoAquisitivo, PagamentoFerias, RecibosContabilidade

class FeriasForm(forms.ModelForm):
    class Meta:
        model = Ferias
        # Campos atualizados conforme seu models.py
        fields = [
            'periodo', 
            'dias_tirados', 
            'ferias_no_recesso_final_ano', 
            'ferias_no_carnaval',
            'faltas_justificadas_descontadas', 
            'observacoes'
        ]
        
        widgets = {
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'dias_tirados': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'ferias_no_recesso_final_ano': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
            'ferias_no_carnaval': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 30}),
            'faltas_justificadas_descontadas': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
        labels = {
            'periodo': 'Período Aquisitivo',
            'dias_tirados': 'Dias Tirados (Total)',
            'ferias_no_recesso_final_ano': 'Dias no Recesso (Final de Ano)',
            'ferias_no_carnaval': 'Dias no Carnaval',
            'faltas_justificadas_descontadas': 'Faltas Justificadas (a descontar)',
            'observacoes': 'Observações',
        }

    def clean(self):
        cleaned_data = super().clean()
        dias_tirados = cleaned_data.get('dias_tirados') or 0
        recesso = cleaned_data.get('ferias_no_recesso_final_ano') or 0
        carnaval = cleaned_data.get('ferias_no_carnaval') or 0
        faltas = cleaned_data.get('faltas_justificadas_descontadas') or 0
        periodo = cleaned_data.get('periodo')

        # 1. Validação de Soma (> 30 dias)
        if dias_tirados > 30:
            raise ValidationError("O total de dias tirados não pode ultrapassar 30 dias.")

        # 2. Validação Lógica (Total >= Parciais)
        # Se você quiser garantir que o total 'dias_tirados' seja coerente com recesso+carnaval
        # (Depende da sua regra de negócio se eles somam ou se 'dias_tirados' já é o total geral)
        # Assumindo que 'dias_tirados' é o guarda-chuva total:
        if (recesso + carnaval) > dias_tirados:
             raise ValidationError("A soma dos dias de Recesso e Carnaval não pode ser maior que o Total de Dias Tirados.")

        # 3. Validação de Saldo (Não permitir estourar o saldo do período)
        if periodo:
            # Pega o saldo atual do período
            saldo_atual = periodo.saldo_restante()
            
            # Se for edição, precisamos adicionar de volta os dias deste registro para recalcular o saldo disponível
            if self.instance.pk:
                consumo_anterior = max(0, self.instance.dias_tirados - (self.instance.faltas_justificadas_descontadas or 0))
                saldo_atual += consumo_anterior

            consumo_novo = max(0, dias_tirados - faltas)

            if consumo_novo > saldo_atual:
                raise ValidationError(f"Saldo insuficiente no período. Saldo disponível: {saldo_atual} dias. Tentativa de consumo: {consumo_novo} dias.")

        return cleaned_data


class PeriodoAquisitivoForm(forms.ModelForm):
    class Meta:
        model = PeriodoAquisitivo
        fields = ['funcionario', 'data_inicio', 'data_fim', 'dias_direito']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'dias_direito': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PagamentoFeriasForm(forms.ModelForm):
    class Meta:
        model = PagamentoFerias
        fields = ['funcionario', 'vencimento', 'valor_a_pagar', 'data_pagamento', 'observacoes']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_a_pagar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        help_texts = {
            'valor_a_pagar': 'Deixe em branco para calcular automaticamente 1/3 do salário atual.'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_a_pagar'].required = False


class RecibosContabilidadeForm(forms.ModelForm):
    class Meta:
        model = RecibosContabilidade
        fields = ['funcionario', 'recibo_de_ferias_contabilidade', 'observacoes']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'recibo_de_ferias_contabilidade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'recibo_de_ferias_contabilidade': 'Data do Recibo (Contábil)',
            'observacoes': 'Observações'
        }