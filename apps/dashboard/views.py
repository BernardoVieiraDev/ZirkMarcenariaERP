from django.shortcuts import render
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime, timedelta

# Importe os modelos
from apps.financeiro.pagar.models import (
    Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio,
    GastoContabilidade, GastoImovel, GastoUtilidade, GastoGeral, Cheque, 
    GastoGasolina, PagamentoFuncionario
)
from apps.financeiro.receber.models import Receber
from apps.funcionarios.models import Funcionario
from apps.comissionamento.models import ContratoRT

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

    # Contratos RT Ativos (Lista)
    contratos_list = ContratoRT.objects.filter(saldo_devedor__gt=0).order_by('arquiteta__nome')[:5]

    # Total Receber
    receber_total = Receber.objects.exclude(status='Pago').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
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
        
        'atrasados_count': len(atrasados_list), # Opcional se quiser mostrar o número no título
    }
    
    return render(request, 'core/dashboard.html', context)