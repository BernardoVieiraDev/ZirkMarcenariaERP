from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.cache import cache # <--- Importante
from .services import FinancialDashboardService
import datetime
import json
import locale

# Tenta configurar locale para formatar dinheiro
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

    # Verifica se o usuário pediu para forçar atualização (ex: clicou num botão "Atualizar")
    force_refresh = request.GET.get('refresh') == 'true'

    # Cria uma chave única para o cache baseada no ano selecionado
    # Exemplo: 'dashboard_data_2026'
    cache_key = f"financial_dashboard_data_{selected_year}"
    
    # Tenta pegar os dados do cache
    cached_context = cache.get(cache_key)

    # LÓGICA DE CACHE:
    # Se temos dados no cache E o usuário NÃO pediu refresh, usamos o cache.
    if cached_context and not force_refresh:
        # Adicionamos apenas flag para saber que veio do cache (opcional, para debug)
        cached_context['from_cache'] = True
        return render(request, 'core/analytics/financial_dashboard.html', cached_context)

    # --- SE CHEGOU AQUI, PRECISA CALCULAR TUDO DO ZERO ---
    
    # Instancia o serviço
    service = FinancialDashboardService()
    
    # 1. Busca os dados usando os métodos do service (A PARTE PESADA)
    cash_flow_data = service.get_monthly_cash_flow(selected_year)
    expense_data = service.get_expense_breakdown(selected_year)
    managerial_data = service.get_managerial_costs_breakdown(selected_year)
    
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
        'from_cache': False, # Flag para indicar que foi processado agora
    }

    # SALVA NO CACHE
    # timeout=60*60 (1 hora) ou o tempo que achar necessário
    cache.set(cache_key, context, timeout=60 * 60) 
    
    return render(request, 'core/analytics/financial_dashboard.html', context)