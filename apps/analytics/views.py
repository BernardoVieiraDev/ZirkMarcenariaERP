from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import FinancialDashboardService
import datetime
import json
import locale

# Tenta configurar locale para PT-BR para formatação correta
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass # Fallback para formatação manual se não tiver locale instalado

def format_currency(value):
    """Formata float para moeda BRL manualmente para garantir compatibilidade"""
    try:
        val = float(value)
        # Formata com 2 casas decimais, troca ponto por vírgula e adiciona separador de milhar
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

@login_required
def financial_dashboard_view(request):
    current_year = datetime.date.today().year
    
    try:
        selected_year = int(request.GET.get('year', current_year))
    except ValueError:
        selected_year = current_year
    
    service = FinancialDashboardService()
    
    # --- GRÁFICOS ---
    cash_flow_data = service.get_monthly_cash_flow(selected_year)
    expense_data = service.get_expense_breakdown(selected_year)
    
    # --- CÁLCULO DE TOTAIS ---
    total_rec = sum(cash_flow_data['receitas'])
    total_desp = sum(cash_flow_data['despesas'])
    total_saldo = sum(cash_flow_data['resultado'])

    context = {
        'selected_year': selected_year,
        'year_range': range(current_year - 2, current_year + 2),
        
        # Dados serializados para os Gráficos JS
        'chart_cash_flow_labels': json.dumps(cash_flow_data['labels']),
        'chart_cash_flow_receitas': json.dumps(cash_flow_data['receitas']),
        'chart_cash_flow_despesas': json.dumps(cash_flow_data['despesas']),
        'chart_cash_flow_resultado': json.dumps(cash_flow_data['resultado']),
        
        'chart_expense_labels': json.dumps(expense_data['labels']),
        'chart_expense_data': json.dumps(expense_data['data']),
        
        # Totais Formatados (Strings prontas para exibir)
        'total_receitas_fmt': format_currency(total_rec),
        'total_despesas_fmt': format_currency(total_desp),
        'saldo_anual_fmt': format_currency(total_saldo),
        'saldo_positivo': total_saldo >= 0, # Booleano simples para cor
    }
    
    return render(request, 'core/analytics/financial_dashboard.html', context)