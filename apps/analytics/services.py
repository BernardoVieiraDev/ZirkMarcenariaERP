import datetime
from decimal import Decimal
from django.db.models import Sum, Value, F, DecimalField, Q
from django.db.models.functions import TruncMonth, Coalesce

# Importação dos modelos financeiros existentes
from apps.financeiro.receber.models import Receber
from apps.financeiro.pagar.models import (
    Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio, 
    GastoContabilidade, GastoImovel, GastoUtilidade, GastoGeral, 
    GastoGasolina, FolhaPagamento, ComissaoArquiteto, Cheque
)

class FinancialDashboardService:
    def __init__(self):
        self.today = datetime.date.today()
        self.expense_models = [
            (Boleto, 'Boletos'),
            (FaturaCartao, 'Cartão de Crédito'),
            (PrestacaoEmprestimo, 'Empréstimos'),
            (GastoVeiculoConsorcio, 'Veículos'),
            (GastoContabilidade, 'Contabilidade/Impostos'),
            (GastoImovel, 'Infraestrutura'),
            (GastoUtilidade, 'Utilidades'),
            (GastoGeral, 'Despesas Gerais'),
            (GastoGasolina, 'Combustível'),
            (FolhaPagamento, 'Folha de Pagamento'),
            (ComissaoArquiteto, 'Comissões'),
            (Cheque, 'Cheques')
        ]

    def _get_model_fields(self, model):
        """
        Define dinamicamente os campos de Data e Valor para cada modelo,
        protegendo valores nulos com Coalesce e definindo output_field explicitamente.
        """
        # Constante para zero decimal para evitar erro de Mixed Types
        zero = Value(Decimal('0'), output_field=DecimalField())

        # 1. Campo de Data
        date_field = 'data_vencimento'
        if model == FolhaPagamento: 
            date_field = 'data_referencia'
        elif model == ComissaoArquiteto: 
            date_field = 'data_pagamento'
        elif hasattr(model, 'data_gasto'): 
            date_field = 'data_gasto'
        elif hasattr(model, 'data_emissao'): 
            date_field = 'data_emissao'

        # 2. Campo/Expressão de Valor
        # Coalesce precisa de output_field=DecimalField() quando mistura campos Decimal com Value(0)
        
        if model == FolhaPagamento:
            # Soma de colunas que podem ser NULL
            # Campos: salario_real, ferias_terco, empreitada, decimo_terceiro, horas_extras_valor
            value_expr = (
                Coalesce(F('salario_real'), zero, output_field=DecimalField()) + 
                Coalesce(F('ferias_terco'), zero, output_field=DecimalField()) + 
                Coalesce(F('empreitada'), zero, output_field=DecimalField()) + 
                Coalesce(F('decimo_terceiro'), zero, output_field=DecimalField()) + 
                Coalesce(F('horas_extras_valor'), zero, output_field=DecimalField())
            )
        elif model == ComissaoArquiteto:
            value_expr = Coalesce(F('valor_comissao'), zero, output_field=DecimalField())
        elif hasattr(model, 'valor_total'):
            value_expr = Coalesce(F('valor_total'), zero, output_field=DecimalField())
        elif hasattr(model, 'valor_pago'):
            # Usa valor_pago se existir, senão 0
            value_expr = Coalesce(F('valor_pago'), zero, output_field=DecimalField())
        else:
            # Fallback padrão
            value_expr = Coalesce(F('valor'), zero, output_field=DecimalField())

        return date_field, value_expr

    def get_monthly_cash_flow(self, year):
        data = {
            'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            'receitas': [0.0] * 12,
            'despesas': [0.0] * 12,
            'resultado': [0.0] * 12
        }

        # 1. Receitas
        receitas_qs = Receber.objects.filter(
            data_vencimento__year=year,
            status__iexact='Recebido'
        ).annotate(month=TruncMonth('data_vencimento')).values('month').annotate(
            total=Sum('valor_recebido')
        )

        for entry in receitas_qs:
            if entry['month']:
                idx = entry['month'].month - 1
                data['receitas'][idx] = float(entry['total'] or 0)

        # 2. Despesas
        for model, _ in self.expense_models:
            date_field, value_expr = self._get_model_fields(model)
            
            filtro = {f"{date_field}__year": year}
            
            # Filtros de Status
            if hasattr(model, 'status'):
                if model == Cheque:
                    filtro['status__in'] = ['COM', 'Compensado']
                else:
                    # Verifica status comuns de pagamento
                    filtro['status__in'] = ['Pago', 'PAGO', 'pago', 'Confirmado']

            # Nota: value_expr já é uma expressão tratada (Coalesce) ou F()
            qs = model.objects.filter(**filtro).annotate(
                month=TruncMonth(date_field)
            ).values('month').annotate(total=Sum(value_expr))

            for entry in qs:
                if entry['month']:
                    idx = entry['month'].month - 1
                    val = float(entry['total'] or 0)
                    data['despesas'][idx] += val

        # 3. Resultado
        for i in range(12):
            data['resultado'][i] = data['receitas'][i] - data['despesas'][i]

        return data

    def get_expense_breakdown(self, year):
        labels = []
        values = []
        
        # Zero decimal constante
        zero = Value(Decimal('0'), output_field=DecimalField())

        for model, label_name in self.expense_models:
            date_field, value_expr = self._get_model_fields(model)
            filtro = {f"{date_field}__year": year}
            
            if hasattr(model, 'status'):
                if model == Cheque:
                    filtro['status__in'] = ['COM', 'Compensado']
                else:
                    filtro['status__in'] = ['Pago', 'PAGO', 'pago']

            # Aggregate retorna dict {'total': Decimal(...)}
            # Precisamos envolver o Sum em Coalesce também aqui para evitar None se não houver registros
            result = model.objects.filter(**filtro).aggregate(
                total=Coalesce(Sum(value_expr), zero, output_field=DecimalField())
            )
            
            total = result['total']
            
            if total and total > 0:
                labels.append(label_name)
                values.append(float(total))

        return {'labels': labels, 'data': values}