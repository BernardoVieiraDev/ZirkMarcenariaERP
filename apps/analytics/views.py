from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services import FinancialDashboardService
import datetime
import json
import locale

# Tenta configurar locale para formatar dinheiro (opcional, mas recomendado)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

def format_currency(value):
    try:
        val = float(value)
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

@login_required
def financial_dashboard_view(request):
    current_year = datetime.date.today().year
    
    # Pega o ano da URL ou usa o atual
    try:
        selected_year = int(request.GET.get('year', current_year))
    except ValueError:
        selected_year = current_year
    
    # Instancia o serviço
    service = FinancialDashboardService()
    
    # 1. Busca os dados usando os métodos do service
    cash_flow_data = service.get_monthly_cash_flow(selected_year)
    expense_data = service.get_expense_breakdown(selected_year)
    managerial_data = service.get_managerial_costs_breakdown(selected_year) # O novo método
    
    # 2. Calcula totais para os cards do topo
    total_rec = sum(cash_flow_data['receitas'])
    total_desp = sum(cash_flow_data['despesas'])
    total_saldo = sum(cash_flow_data['resultado'])

    # 3. Prepara o contexto para o HTML
    context = {
        'selected_year': selected_year,
        'year_range': range(current_year - 2, current_year + 2),
        
        # Gráfico Fluxo de Caixa
        'chart_cash_flow_labels': json.dumps(cash_flow_data['labels']),
        'chart_cash_flow_receitas': json.dumps(cash_flow_data['receitas']),
        'chart_cash_flow_despesas': json.dumps(cash_flow_data['despesas']),
        'chart_cash_flow_resultado': json.dumps(cash_flow_data['resultado']),
        
        # Gráfico Despesas (Pizza)
        'chart_expense_labels': json.dumps(expense_data['labels']),
        'chart_expense_data': json.dumps(expense_data['data']),

        # Gráfico Gerencial (Novo)
        'chart_managerial_labels': json.dumps(managerial_data['labels']),
        'chart_managerial_data': json.dumps(managerial_data['data']),
        
        # Totais formatados
        'total_receitas_fmt': format_currency(total_rec),
        'total_despesas_fmt': format_currency(total_desp),
        'saldo_anual_fmt': format_currency(total_saldo),
        'saldo_positivo': total_saldo >= 0,
    }
    
    return render(request, 'core/analytics/financial_dashboard.html', context)