import datetime
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings
from django.db.models import DecimalField, F, Sum, Value, Q
from django.db.models.functions import Coalesce, TruncMonth

# Imports dos Models
from apps.financeiro.pagar.models import (Boleto, Cheque, ComissaoArquiteto,
                                          FaturaCartao, FolhaPagamento,
                                          GastoContabilidade, GastoGasolina,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import Receber

class FinancialDashboardService:
    CACHE_TIMEOUT = 60 * 60 * 24 

    def __init__(self):
        self.today = datetime.date.today()
        # Lista padronizada de status considerados "Pagos"
        self.paid_status_list = ['Pago', 'PAGO', 'pago', 'Confirmado', 'Compensado', 'COM', 'Baixado', 'Recebido']
        
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
        Retorna (campo_de_data, expressao_de_valor) para cada model.
        Prioriza data de pagamento efetivo para regime de caixa.
        """
        zero = Value(Decimal('0'), output_field=DecimalField())
        
        # --- 1. DEFINIÇÃO DA DATA (Regime de Caixa preferencial) ---
        date_field = 'data_vencimento' # Default
        
        if model == FolhaPagamento:
            date_field = 'data_referencia'
        elif model == ComissaoArquiteto:
            # Se tiver data_pagamento preenchida, usa ela. Senão (fallback), usa vencimento.
            # Nota: Como isso é definido no nível da classe para o annotate, 
            # assumimos data_pagamento para análises de realizado.
            date_field = 'data_pagamento'
        elif hasattr(model, 'data_gasto'): 
            date_field = 'data_gasto'
        elif hasattr(model, 'data_emissao'): 
            date_field = 'data_emissao'
        elif hasattr(model, 'data_pagamento'):
             # Boletos e Consórcios têm data_pagamento
             date_field = 'data_pagamento'

        # --- 2. DEFINIÇÃO DO VALOR (Custo/Saída Real) ---
        if model == FolhaPagamento:
            # [CORREÇÃO] Custo total da empresa (Competência/DRE). 
            # Não subtraímos o adiantamento aqui para ver o CUSTO TOTAL.
            # Se for Fluxo de Caixa, o adiantamento deveria ser uma saída separada, 
            # mas para Analytics de Custo, soma-se tudo.
            value_expr = (
                Coalesce(F('salario_real'), zero, output_field=DecimalField()) + 
                Coalesce(F('ferias_terco'), zero, output_field=DecimalField()) + 
                Coalesce(F('empreitada'), zero, output_field=DecimalField()) + 
                Coalesce(F('decimo_terceiro'), zero, output_field=DecimalField()) + 
                Coalesce(F('horas_extras_valor'), zero, output_field=DecimalField())
                # Removido: - Coalesce(F('adiantamento')... 
            )
        elif model == ComissaoArquiteto:
            value_expr = Coalesce(F('valor_pago'), F('valor_comissao'), zero, output_field=DecimalField())
        elif hasattr(model, 'valor_total'):
            value_expr = Coalesce(F('valor_total'), zero, output_field=DecimalField())
        elif hasattr(model, 'valor_pago'):
            # Prioriza o valor efetivamente pago (com juros/multa)
            value_expr = Coalesce(F('valor_pago'), F('valor'), zero, output_field=DecimalField())
        else:
            value_expr = Coalesce(F('valor'), zero, output_field=DecimalField())

        return date_field, value_expr

    def get_monthly_cash_flow(self, year):
        cache_key = f"analytics_cash_flow_{year}_v2"
        data = cache.get(cache_key)
        
        if not data:
            data = {
                'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                'receitas': [0.0] * 12,
                'despesas': [0.0] * 12,
                'resultado': [0.0] * 12
            }

            # Receitas (Regime de Caixa)
            receitas_qs = Receber.objects.filter(
                data_recebimento__year=year,
                status__iexact='Recebido'
            ).annotate(month=TruncMonth('data_recebimento')).values('month').annotate(
                total=Sum('valor_recebido')
            )

            for entry in receitas_qs:
                if entry['month']:
                    idx = entry['month'].month - 1
                    data['receitas'][idx] = float(entry['total'] or 0)

            # Despesas
            for model, _ in self.expense_models:
                date_field, value_expr = self._get_model_fields(model)
                
                # Filtra pelo ano no campo definido (idealmente data_pagamento se houver)
                filtro = {f"{date_field}__year": year}
                
                # Aplica filtro de status seguro
                if hasattr(model, 'status'):
                    filtro['status__in'] = self.paid_status_list

                # Caso o date_field seja 'data_pagamento' mas o registro esteja pago sem data preenchida (erro de cadastro),
                # usamos Coalesce no banco é difícil no filtro direto. 
                # Assumimos aqui que se está PAGO, tem data_pagamento.
                
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

            cache.set(cache_key, data, self.CACHE_TIMEOUT)

        return data

    def get_expense_breakdown(self, year):
        cache_key = f"analytics_expense_breakdown_{year}_v2"
        data = cache.get(cache_key)

        if not data:
            labels = []
            values = []
            zero = Value(Decimal('0'), output_field=DecimalField())

            for model, label_name in self.expense_models:
                date_field, value_expr = self._get_model_fields(model)
                filtro = {f"{date_field}__year": year}
                
                if hasattr(model, 'status'):
                    filtro['status__in'] = self.paid_status_list

                result = model.objects.filter(**filtro).aggregate(
                    total=Coalesce(Sum(value_expr), zero, output_field=DecimalField())
                )
                total = result['total']
                
                if total and total > 0:
                    labels.append(label_name)
                    values.append(float(total))
            
            data = {'labels': labels, 'data': values}
            cache.set(cache_key, data, self.CACHE_TIMEOUT)

        return data

    def get_managerial_costs_breakdown(self, year):
        """
        Retorna a quebra de custos gerenciais (DRE simplificado).
        """
        cache_key = f"analytics_managerial_costs_{year}_v2"
        data = cache.get(cache_key)

        if not data:
            zero = Value(Decimal('0'), output_field=DecimalField())
            
            # Helper para somar queries
            def sum_model(model, **kwargs):
                return model.objects.filter(
                    status__in=self.paid_status_list, **kwargs
                ).aggregate(total=Coalesce(Sum('valor'), zero))['total']

            # 1. PRODUÇÃO
            itens_fabrica = ['CESAN_MARCENARIA', 'ESC_MARCENARIA', 'INT_MARCENARIA']
            custo_fabrica = GastoUtilidade.objects.filter(
                data_vencimento__year=year,
                tipo_cliente__in=itens_fabrica,
                status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum('valor'), zero))['total']

            # 2. ADMINISTRATIVO
            itens_admin = ['CESAN_ALPHA', 'ESC_ALPHA', 'INT_ALPHA', 'CEL']
            util_admin = GastoUtilidade.objects.filter(
                data_vencimento__year=year, 
                tipo_cliente__in=itens_admin,
                status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum('valor'), zero))['total']
            
            contab = sum_model(GastoContabilidade, data_vencimento__year=year)
            imovel = sum_model(GastoImovel, data_vencimento__year=year)
            
            custo_admin = util_admin + contab + imovel

            # 3. LOGÍSTICA
            gasolina = GastoGasolina.objects.filter(
                data_gasto__year=year, status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum('valor_total'), zero))['total']
            
            veiculos = GastoVeiculoConsorcio.objects.filter(
                data_vencimento__year=year, status__in=self.paid_status_list
            ).aggregate(
                total=Coalesce(Sum(Coalesce(F('valor_pago'), F('valor'))), zero)
            )['total']
            
            custo_logistica = gasolina + veiculos

            # 4. PESSOAL (RH)
            # Usa a expressão corrigida (sem subtrair adiantamento)
            _, expr_folha = self._get_model_fields(FolhaPagamento)
            custo_rh = FolhaPagamento.objects.filter(
                data_referencia__year=year, status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum(expr_folha), zero))['total']

            # 5. COMERCIAL
            custo_comercial = ComissaoArquiteto.objects.filter(
                data_pagamento__year=year, status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum('valor_pago'), Sum('valor_comissao'), zero))['total']

            # 6. OPERACIONAL / VARIÁVEL
            custo_var = Decimal('0')
            
            # Boleto
            custo_var += Boleto.objects.filter(
                data_pagamento__year=year, status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum(Coalesce(F('valor_pago'), F('valor'))), zero))['total']

            # Cheque
            custo_var += Cheque.objects.filter(
                 data_emissao__year=year, status__in=['COM', 'Compensado', 'Pago']
            ).aggregate(total=Coalesce(Sum('valor'), zero))['total']

            # Fatura Cartão
            custo_var += sum_model(FaturaCartao, data_vencimento__year=year)
            
            # Prestação Empréstimo
            custo_var += sum_model(PrestacaoEmprestimo, data_vencimento__year=year)

            # Gasto Geral
            custo_var += GastoGeral.objects.filter(
                data_gasto__year=year, status__in=self.paid_status_list
            ).aggregate(total=Coalesce(Sum('valor_total'), zero))['total']

            data = {
                'labels': ['Produção/Fábrica', 'Administrativo', 'Logística/Frota', 'Pessoal/RH', 'Comercial', 'Operacional/Variável'],
                'data': [float(custo_fabrica), float(custo_admin), float(custo_logistica), float(custo_rh), float(custo_comercial), float(custo_var)]
            }
            
            cache.set(cache_key, data, self.CACHE_TIMEOUT)

        return data