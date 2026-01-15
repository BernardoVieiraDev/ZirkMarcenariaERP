import datetime
from decimal import Decimal
from django.db.models import Sum, Value, F, DecimalField
from django.db.models.functions import TruncMonth, Coalesce

# Importação dos modelos
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
        zero = Value(Decimal('0'), output_field=DecimalField())
        date_field = 'data_vencimento'
        
        if model == FolhaPagamento: 
            date_field = 'data_referencia'
        elif model == ComissaoArquiteto: 
            date_field = 'data_pagamento'
        elif hasattr(model, 'data_gasto'): 
            date_field = 'data_gasto'
        elif hasattr(model, 'data_emissao'): 
            date_field = 'data_emissao'

        if model == FolhaPagamento:
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
            value_expr = Coalesce(F('valor_pago'), zero, output_field=DecimalField())
        else:
            value_expr = Coalesce(F('valor'), zero, output_field=DecimalField())

        return date_field, value_expr

    def get_monthly_cash_flow(self, year):
        data = {
            'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
            'receitas': [0.0] * 12,
            'despesas': [0.0] * 12,
            'resultado': [0.0] * 12
        }

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

        for model, _ in self.expense_models:
            date_field, value_expr = self._get_model_fields(model)
            filtro = {f"{date_field}__year": year}
            
            if hasattr(model, 'status'):
                if model == Cheque:
                    filtro['status__in'] = ['COM', 'Compensado']
                else:
                    filtro['status__in'] = ['Pago', 'PAGO', 'pago', 'Confirmado']

            qs = model.objects.filter(**filtro).annotate(
                month=TruncMonth(date_field)
            ).values('month').annotate(total=Sum(value_expr))

            for entry in qs:
                if entry['month']:
                    idx = entry['month'].month - 1
                    val = float(entry['total'] or 0)
                    data['despesas'][idx] += val

        for i in range(12):
            data['resultado'][i] = data['receitas'][i] - data['despesas'][i]

        return data

    def get_expense_breakdown(self, year):
        labels = []
        values = []
        zero = Value(Decimal('0'), output_field=DecimalField())

        for model, label_name in self.expense_models:
            date_field, value_expr = self._get_model_fields(model)
            filtro = {f"{date_field}__year": year}
            
            if hasattr(model, 'status'):
                if model == Cheque:
                    filtro['status__in'] = ['COM', 'Compensado']
                else:
                    filtro['status__in'] = ['Pago', 'PAGO', 'pago']

            result = model.objects.filter(**filtro).aggregate(
                total=Coalesce(Sum(value_expr), zero, output_field=DecimalField())
            )
            total = result['total']
            
            if total and total > 0:
                labels.append(label_name)
                values.append(float(total))

        return {'labels': labels, 'data': values}

    def get_managerial_costs_breakdown(self, year):
        """
        Agrupa despesas em Centros de Custo Gerenciais.
        """
        zero = Value(Decimal('0'), output_field=DecimalField())
        
        # 1. PRODUÇÃO / FÁBRICA
        itens_fabrica = ['CESAN_MARCENARIA', 'ESC_MARCENARIA', 'INT_MARCENARIA']
        custo_fabrica = GastoUtilidade.objects.filter(
            data_vencimento__year=year,
            tipo_cliente__in=itens_fabrica,
            status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor'), zero))['total']

        # 2. ADMINISTRATIVO
        itens_admin = ['CESAN_ALPHA', 'ESC_ALPHA', 'INT_ALPHA', 'CEL']
        util_admin = GastoUtilidade.objects.filter(
            data_vencimento__year=year, 
            tipo_cliente__in=itens_admin,
            status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor'), zero))['total']
        
        contab = GastoContabilidade.objects.filter(
            data_vencimento__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor'), zero))['total']
        
        imovel = GastoImovel.objects.filter(
            data_vencimento__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor'), zero))['total']
        
        custo_admin = util_admin + contab + imovel

        # 3. LOGÍSTICA
        gasolina = GastoGasolina.objects.filter(
            data_gasto__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor_total'), zero))['total']
        
        veiculos = GastoVeiculoConsorcio.objects.filter(
            data_vencimento__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(
            total=Coalesce(Sum(Coalesce(F('valor_pago'), F('valor'))), zero)
        )['total']
        
        custo_logistica = gasolina + veiculos

        # 4. PESSOAL (RH)
        _, expr_folha = self._get_model_fields(FolhaPagamento)
        custo_rh = FolhaPagamento.objects.filter(
            data_referencia__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum(expr_folha), zero))['total']

        # 5. COMERCIAL
        custo_comercial = ComissaoArquiteto.objects.filter(
            data_pagamento__year=year, status__in=['Pago', 'PAGO', 'pago']
        ).aggregate(total=Coalesce(Sum('valor_comissao'), zero))['total']

        # 6. OPERACIONAL VARIÁVEL
        modelos_var = [Boleto, Cheque, FaturaCartao, PrestacaoEmprestimo, GastoGeral]
        custo_var = Decimal('0')
        
        for model in modelos_var:
            date_field, val_expr = self._get_model_fields(model)
            filtro = {f"{date_field}__year": year}
            
            if model == Cheque:
                filtro['status__in'] = ['COM', 'Compensado']
            else:
                filtro['status__in'] = ['Pago', 'PAGO', 'pago']
                
            val = model.objects.filter(**filtro).aggregate(
                total=Coalesce(Sum(val_expr), zero)
            )['total']
            custo_var += val

        return {
            'labels': ['Produção/Fábrica', 'Administrativo', 'Logística/Frota', 'Pessoal/RH', 'Comercial', 'Operacional/Variável'],
            'data': [float(custo_fabrica), float(custo_admin), float(custo_logistica), float(custo_rh), float(custo_comercial), float(custo_var)]
        }