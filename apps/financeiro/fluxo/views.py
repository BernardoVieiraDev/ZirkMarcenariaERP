from datetime import date, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from .services import FluxoCaixaService
from apps.relatorios.services.fluxo_caixa_export import RelatorioFluxoCaixaExport
from django.contrib.auth.decorators import login_required

def _calcular_data_inicio(request, tipo):
    """
    Função auxiliar para determinar a data de início baseada no 'toggle' da tela.
    """
    hoje = date.today()
    visualizar_inicio = request.GET.get('visualizar_inicio') == 'on'

    if visualizar_inicio:
        if tipo == 'semanal':
            # Volta para a última segunda-feira
            return hoje - timedelta(days=hoje.weekday())
        elif tipo == 'mensal':
            # Volta para o dia 1 do mês atual
            return hoje.replace(day=1)
    return hoje

@login_required
def fluxo_semanal(request):
    data_inicio = _calcular_data_inicio(request, 'semanal')
    # Gera 7 dias
    dias, timeline = FluxoCaixaService.gerar_fluxo_detalhado(data_inicio, 7)
    
    context = {
        'titulo': 'Fluxo de Caixa Semanal',
        'dias': dias,
        'timeline': timeline,
        'tipo_view': 'semanal',
        'visualizar_inicio': request.GET.get('visualizar_inicio') == 'on'
    }
    return render(request, 'core/fluxo/fluxo_list.html', context)

@login_required
def fluxo_mensal(request):
    data_inicio = _calcular_data_inicio(request, 'mensal')
    # Gera 30 dias (ou ajuste conforme necessidade)
    dias, timeline = FluxoCaixaService.gerar_fluxo_detalhado(data_inicio, 30)
    
    context = {
        'titulo': 'Fluxo de Caixa Mensal',
        'dias': dias,
        'timeline': timeline,
        'tipo_view': 'mensal',
        'visualizar_inicio': request.GET.get('visualizar_inicio') == 'on'
    }
    return render(request, 'core/fluxo/fluxo_list.html', context)

@login_required
def exportar_fluxo(request, tipo):
    """
    Gera o download do arquivo Excel.
    """
    dias = 30 if tipo == 'mensal' else 7
    data_inicio = _calcular_data_inicio(request, tipo)
    
    # Chama o serviço de exportação que atualizamos para o formato detalhado
    excel_file = RelatorioFluxoCaixaExport.gerar_excel(data_inicio, dias, tipo)
    
    response = HttpResponse(
        excel_file,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    # Formata o nome do arquivo para incluir data e tipo
    filename = f"fluxo_caixa_{tipo}_{data_inicio.strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response