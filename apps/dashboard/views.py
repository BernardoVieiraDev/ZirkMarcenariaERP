from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import F, Q, Sum
from django.shortcuts import render

# ... (imports de modelos mantidos) ...
from apps.comissionamento.models import ContratoRT
from apps.ferias.models import PeriodoAquisitivo
from apps.financeiro.pagar.models import (Boleto, ComissaoArquiteto, FaturaCartao, FolhaPagamento,
                                          GastoContabilidade, GastoGeral,
                                          GastoImovel, GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo, GastoAlmoco)
from apps.financeiro.receber.models import Receber
from apps.funcionarios.models import Funcionario

@login_required
def dashboard(request):
    now = datetime.now()
    today = now.date()
    seven_days_later = today + timedelta(days=7)
    
    # === CACHE 1: TOTAIS DO TOPO (Cache curto de 10 min ou invalidado por sinal) ===
    cache_key_totals = "dashboard_header_totals"
    cached_totals = cache.get(cache_key_totals)
    
    if cached_totals:
        cont_funcionarios = cached_totals['funcionarios']
        total_pagar_pendente = cached_totals['pagar']
        receber_total = cached_totals['receber']
        # Precisamos recalcular apenas as listas dinâmicas abaixo
    else:
        # Lógica original de cálculo dos totais
        cont_funcionarios = Funcionario.objects.count()
        total_pagar_pendente = Decimal('0.00')
        
        # Recalcula o total a pagar iterando os modelos
        MODELOS_COM_VENCIMENTO_SUM = [
            Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio, 
            GastoContabilidade, GastoImovel, GastoUtilidade
        ]
        for ModelClass in MODELOS_COM_VENCIMENTO_SUM:
            total_qs = ModelClass.objects.exclude(status='Pago').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
            total_pagar_pendente += total_qs
        
        # Adiciona GastoGeral
        total_geral = GastoGeral.objects.exclude(status='Pago').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        
        total_almoco = GastoAlmoco.objects.exclude(status='Pago').aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
        
        total_pagar_pendente += total_geral

        total_comissoes = ComissaoArquiteto.objects.exclude(status='Pago').aggregate(
        total=Sum('valor_comissao')
        )['total'] or Decimal('0.00')
        total_pagar_pendente += total_comissoes


        total_folha = FolhaPagamento.objects.exclude(status='Pago').aggregate(
            total=Sum('salario_real')
        )['total'] or Decimal('0.00')
        
        total_pagar_pendente += total_folha

        total_pagar_pendente += total_almoco


        # Total Receber
        receber_total = Receber.objects.exclude(status='Recebido').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # Salva no cache
        cache.set(cache_key_totals, {
            'funcionarios': cont_funcionarios,
            'pagar': total_pagar_pendente,
            'receber': receber_total
        }, 600) # 10 minutos

    # === AS LISTAS (Atrasados, Vencendo, etc) geralmente não compensa cachear muito tempo
    # pois dependem da data exata (today) que muda meia-noite, e o usuário quer ver updates rápidos.
    # Mantemos a query direta para garantir realtime nestas listas críticas. ===
    
    atrasados_list = []
    vencendo_list = []
    ultimos_gastos_list = []

    MODELOS_COM_VENCIMENTO = [
        Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio, 
        GastoContabilidade, GastoImovel, GastoUtilidade
    ]

    for ModelClass in MODELOS_COM_VENCIMENTO:
        # Lista: Gastos Atrasados
        atrasados = ModelClass.objects.filter(~Q(status='Pago'), data_vencimento__lt=today)
        atrasados_list.extend(list(atrasados))

        # Lista: Vencendo em 7 dias
        vencendo = ModelClass.objects.filter(
            ~Q(status='Pago'),
            data_vencimento__gte=today,
            data_vencimento__lte=seven_days_later
        )
        vencendo_list.extend(list(vencendo))

        # Coletar para "Últimos Gastos"
        recentes = ModelClass.objects.all().order_by('-data_vencimento')[:5]
        ultimos_gastos_list.extend(list(recentes))

    # Adicionar GastoGeral às listas
    recentes_geral = GastoGeral.objects.all().order_by('-data_gasto')[:5]
    ultimos_gastos_list.extend(list(recentes_geral))

    # --- CACHE 2: ALERTAS DE FÉRIAS (Processamento Pesado em Python) ---
    # Como férias não mudam a todo minuto, podemos cachear por 12 horas
    cache_key_ferias = "dashboard_ferias_alerts"
    ferias_alerta_list = cache.get(cache_key_ferias)

    if ferias_alerta_list is None:
        ferias_alerta_list = []
        periodos = PeriodoAquisitivo.objects.select_related('funcionario').prefetch_related('ferias_registradas').all()
        
        for p in periodos:
            saldo = p.saldo_restante()
            if saldo > 0:
                try:
                    prazo_concessivo = p.data_fim.replace(year=p.data_fim.year + 1)
                except ValueError:
                    prazo_concessivo = p.data_fim + timedelta(days=365)
                
                dias_para_vencer = (prazo_concessivo - today).days
                
                if 0 <= dias_para_vencer <= 45:
                    ferias_alerta_list.append({
                        'funcionario': p.funcionario.nome,
                        'data_limite': prazo_concessivo,
                        'dias_restantes_prazo': dias_para_vencer,
                        'saldo_dias': saldo,
                        'critico': dias_para_vencer < 30 
                    })
        
        ferias_alerta_list.sort(key=lambda x: x['dias_restantes_prazo'])
        cache.set(cache_key_ferias, ferias_alerta_list, 60 * 60 * 12)

    # Ordenação e cortes das listas (rápido em memória)
    atrasados_list.sort(key=lambda x: x.data_vencimento)
    atrasados_list = atrasados_list[:5]

    vencendo_list.sort(key=lambda x: x.data_vencimento)
    vencendo_list = vencendo_list[:5]

    def get_sort_date(obj):
        if hasattr(obj, 'data_vencimento'): return obj.data_vencimento
        if hasattr(obj, 'data_gasto'): return obj.data_gasto
        return datetime.min.date()

    ultimos_gastos_list.sort(key=get_sort_date, reverse=True)
    ultimos_gastos_list = ultimos_gastos_list[:5]

    contratos_list = ContratoRT.objects.annotate(
        saldo_devedor=F('valor_rt')
    ).order_by('-data_contrato')[:5]
    
    context = { 
        'cont_funcionarios': cont_funcionarios,
        'pagar_total': total_pagar_pendente, # Valor pode vir do cache ou recalculado
        'receber_total': receber_total,      # Valor pode vir do cache ou recalculado
        'atrasados_list': atrasados_list,
        'vencendo_list': vencendo_list,
        'contratos_list': contratos_list,
        'ultimos_gastos': ultimos_gastos_list,
        'ferias_alerta_list': ferias_alerta_list, # Lista do cache
        'atrasados_count': len(atrasados_list),
    }
    
    return render(request, 'core/dashboard.html', context)