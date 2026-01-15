from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q, Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.shortcuts import render

from apps.comissionamento.models import ContratoRT
from apps.ferias.models import PeriodoAquisitivo
# Importe os modelos
from apps.financeiro.pagar.models import (Boleto, Cheque, FaturaCartao,
                                          GastoContabilidade, GastoGasolina,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PagamentoFuncionario,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import Receber
from apps.funcionarios.models import Funcionario


def dashboard(request):
    now = datetime.now()
    today = now.date()
    seven_days_later = today + timedelta(days=7)
    
    # --- QUADROS SUPERIORES (Mantidos) ---
    cont_funcionarios = Funcionario.objects.count()
    total_pagar_pendente = Decimal('0.00')
    
    # --- LISTAS PARA OS QUADROS INFERIORES ---
    atrasados_list = []
    vencendo_list = []
    ultimos_gastos_list = []

    # Modelos que possuem 'data_vencimento'
    MODELOS_COM_VENCIMENTO = [
        Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio, 
        GastoContabilidade, GastoImovel, GastoUtilidade
    ]

    for ModelClass in MODELOS_COM_VENCIMENTO:
        # 1. Total Pagar (Pendente Geral)
        total_qs = ModelClass.objects.exclude(status='Pago').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        total_pagar_pendente += total_qs

        # 2. Lista: Gastos Atrasados (Vencidos e não pagos)
        atrasados = ModelClass.objects.filter(
            ~Q(status='Pago'), 
            data_vencimento__lt=today
        )
        atrasados_list.extend(list(atrasados))

        # 3. Lista: Vencendo em 7 dias
        vencendo = ModelClass.objects.filter(
            ~Q(status='Pago'),
            data_vencimento__gte=today,
            data_vencimento__lte=seven_days_later
        )
        vencendo_list.extend(list(vencendo))

        # 4. Coletar para "Últimos Gastos"
        recentes = ModelClass.objects.all().order_by('-data_vencimento')[:5]
        ultimos_gastos_list.extend(list(recentes))


    # --- NOVA LÓGICA: ALERTAS DE FÉRIAS ---
    ferias_alerta_list = []
    
    # Buscamos períodos aquisitivos e trazemos as férias registradas para evitar N+1 queries no loop
    periodos = PeriodoAquisitivo.objects.select_related('funcionario').prefetch_related('ferias_registradas').all()
    
    for p in periodos:
        saldo = p.saldo_restante() # Usa o método do model que calcula dias - tirados
        
        if saldo > 0:
            # O prazo legal para conceder férias é geralmente 1 ano após o fim do período aquisitivo
            try:
                prazo_concessivo = p.data_fim.replace(year=p.data_fim.year + 1)
            except ValueError: # Tratamento para 29 de fev
                prazo_concessivo = p.data_fim + timedelta(days=365)
            
            dias_para_vencer = (prazo_concessivo - today).days
            
            # ALERTA: Se faltam menos de 45 dias para estourar o prazo e ainda tem saldo
            if 0 <= dias_para_vencer <= 45:
                ferias_alerta_list.append({
                    'funcionario': p.funcionario.nome,
                    'data_limite': prazo_concessivo,
                    'dias_restantes_prazo': dias_para_vencer,
                    'saldo_dias': saldo,
                    # Flag para urgência crítica (menos de 15 dias é perigoso por causa do aviso prévio de férias)
                    'critico': dias_para_vencer < 30 
                })

    # Adicionar GastoGeral ao total e últimos gastos
    total_geral = GastoGeral.objects.exclude(status='Pago').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    total_pagar_pendente += total_geral
    
    recentes_geral = GastoGeral.objects.all().order_by('-data_gasto')[:5]
    ultimos_gastos_list.extend(list(recentes_geral))

    # --- ORDENAÇÃO E CORTE DAS LISTAS ---
    
    # Atrasados: Ordenar pelos mais antigos primeiro (urgência)
    atrasados_list.sort(key=lambda x: x.data_vencimento)
    atrasados_list = atrasados_list[:5] # Top 5

    # Vencendo: Ordenar pelo vencimento mais próximo
    vencendo_list.sort(key=lambda x: x.data_vencimento)
    vencendo_list = vencendo_list[:5] # Top 5

    # Últimos Gastos: Ordenar pelo mais recente
    def get_sort_date(obj):
        if hasattr(obj, 'data_vencimento'): return obj.data_vencimento
        if hasattr(obj, 'data_gasto'): return obj.data_gasto
        return datetime.min.date()

    ultimos_gastos_list.sort(key=get_sort_date, reverse=True)
    ultimos_gastos_list = ultimos_gastos_list[:5]

    # --- CORREÇÃO AQUI: Contratos RT Ativos ---
    # Como não existe mais 'saldo_devedor' no banco, calculamos via annotate.
    # Coalesce garante que se valor_pago for None, seja tratado como 0.
    contratos_list = ContratoRT.objects.annotate(
        saldo_devedor=F('valor_rt')
    ).order_by('-data_contrato')[:5]
    ferias_alerta_list.sort(key=lambda x: x['dias_restantes_prazo'])

    # Total Receber
    receber_total = Receber.objects.exclude(status='Recebido').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    context = { 
        # Quadros Superiores
        'cont_funcionarios': cont_funcionarios,
        'pagar_total': total_pagar_pendente,
        'receber_total': receber_total,
        
        # Listas para os Quadros Inferiores
        'atrasados_list': atrasados_list,
        'vencendo_list': vencendo_list,
        'contratos_list': contratos_list,
        'ultimos_gastos': ultimos_gastos_list,
        'ferias_alerta_list': ferias_alerta_list,
        'atrasados_count': len(atrasados_list),
    }
    
    return render(request, 'core/dashboard.html', context)