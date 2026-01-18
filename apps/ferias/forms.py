from django import forms
from django.core.exceptions import ValidationError
from django.db import models  # <--- Importação adicionada aqui

from apps.funcionarios.models import Funcionario

from .models import (Ferias, PagamentoFerias, PeriodoAquisitivo,
                     RecibosContabilidade)


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
                consumo_anterior = max(0, self.instance.dias_tirados + (self.instance.faltas_justificadas_descontadas or 0))
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
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'dias_direito': forms.NumberInput(attrs={'class': 'form-control', 'max': 30}),
        }

    def clean(self):
        cleaned_data = super().clean()
        funcionario = cleaned_data.get('funcionario')
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        dias_direito = cleaned_data.get('dias_direito')

        # 1. Valida se a data fim é maior que a data início
        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError("A data de fim deve ser posterior à data de início.")

        # 2. Valida limite de dias de direito (padrão CLT é 30)
        if dias_direito and dias_direito > 30:
             self.add_error('dias_direito', "O máximo de dias de direito permitido por período é 30.")

        # 3. Valida sobreposição de períodos para o mesmo funcionário
        if funcionario and data_inicio and data_fim:
            # Busca períodos existentes que colidam com as datas informadas
            conflitos = PeriodoAquisitivo.objects.filter(
                funcionario=funcionario,
                is_deleted=False  # Ignora deletados se usar SoftDelete
            ).filter(
                # Lógica de sobreposição: (InicioA <= FimB) e (FimA >= InicioB)
                models.Q(data_inicio__lte=data_fim) & models.Q(data_fim__gte=data_inicio)
            )

            # Se for edição (instance.pk existe), exclui o próprio registro da busca
            if self.instance.pk:
                conflitos = conflitos.exclude(pk=self.instance.pk)

            if conflitos.exists():
                raise ValidationError(
                    f"O funcionário {funcionario.nome} já possui um período aquisitivo registrado que conflita com essas datas."
                )

        return cleaned_data


class PagamentoFeriasForm(forms.ModelForm):
    class Meta:
        model = PagamentoFerias
        fields = [
            'funcionario',
            'vencimento',
            'valor_a_pagar',
            'data_pagamento',
            'status',
            'observacoes',
        ]
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'),
            'data_pagamento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d'),
            'valor_a_pagar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
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
            'recibo_de_ferias_contabilidade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            # ALTERADO: rows de 2 para 4 para facilitar a edição
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'recibo_de_ferias_contabilidade': 'Data do Recibo (Contábil)',
            'observacoes': 'Observações'
        }


class FeriasColetivasForm(forms.Form):
    funcionarios = forms.ModelMultipleChoiceField(
        queryset=Funcionario.objects.filter(is_deleted=False).order_by('nome'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Selecione os Funcionários"
    )
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Data Início"
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Data Fim"
    )
    
    # Campos de Recesso e Carnaval
    ferias_no_recesso_final_ano = forms.IntegerField(
        required=False, 
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        label="Dias de Recesso (Final de Ano)"
    )
    ferias_no_carnaval = forms.IntegerField(
        required=False, 
        initial=0,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        label="Dias de Carnaval"
    )

    observacao_geral = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False,
        label="Observação (será adicionada a todos)"
    )

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('data_inicio')
        fim = cleaned_data.get('data_fim')
        recesso = cleaned_data.get('ferias_no_recesso_final_ano') or 0
        carnaval = cleaned_data.get('ferias_no_carnaval') or 0

        if inicio and fim:
            if inicio > fim:
                raise forms.ValidationError("A data de início não pode ser maior que a data fim.")
            
            dias_totais = (fim - inicio).days + 1
            if (recesso + carnaval) > dias_totais:
                raise forms.ValidationError(
                    f"A soma de Recesso ({recesso}) e Carnaval ({carnaval}) não pode exceder "
                    f"a duração total das férias ({dias_totais} dias)."
                )
        
        return cleaned_data