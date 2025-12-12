from django.shortcuts import render
from django.db.models import Sum, Q
from decimal import Decimal
from datetime import datetime

# 1. IMPORTS CORRIGIDOS: Importe todos os seus modelos de gastos
from apps.financeiro.pagar.models import  (
    StatusPagamento, Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio,
    GastoContabilidade, GastoImovel, GastoUtilidade, GastoGeral,
    # Você provavelmente tem Receber e Funcionario em outras apps
) 
# Assumindo que Receber e Funcionario vêm de onde estavam antes:
from apps.financeiro.receber.models import Receber
from apps.funcionarios.models import Funcionario

# Mapeamento para buscar todos os modelos de Gasto
MODELOS_GASTO_A_PAGAR = [
    Boleto, FaturaCartao, PrestacaoEmprestimo, GastoVeiculoConsorcio, 
    GastoContabilidade, GastoImovel, GastoUtilidade, 
    # GastoGeral não herda GastoBase, mas tem 'valor_total'
]

def dashboard(request):
    # Obter a data e hora atuais
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    cont_funcionarios = Funcionario.objects.count()

    # --- LÓGICA DE AGREGAÇÃO DE CONTAS A PAGAR (CRÍTICO) ---
    
    total_pagar_pendente = Decimal('0.00')
    pagar_preview_list = []

    for ModelClass in MODELOS_GASTO_A_PAGAR:
        # 1. Consulta para o TOTAL PENDENTE: Exclui status 'PAGO'
        # Assumindo que todos os modelos herdam GastoBase, eles têm 'status' e 'valor'.
        total_qs = ModelClass.objects.filter(
            ~Q(status=StatusPagamento.PAGO) # Exclui os que já foram pagos
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        
        total_pagar_pendente += total_qs

        # 2. Consulta para o PREVIEW (Mês Atual):
        # Filtra pelo mês/ano e pega os 5 primeiros
        preview_qs = ModelClass.objects.filter(
            data_vencimento__month=current_month, 
            data_vencimento__year=current_year
        ).order_by('data_vencimento')[:5]
        
        # Estendemos a lista de preview
        pagar_preview_list.extend(list(preview_qs))

    # Adiciona GastoGeral (modelo independente com campo 'valor_total')
    # O GastoGeral não tem 'status' e 'data_vencimento' como GastoBase, então precisa de lógica adaptada:
    gasto_geral_qs = GastoGeral.objects.all().aggregate(total=Sum('valor_total'))['total'] or Decimal('0.00')
    total_pagar_pendente += gasto_geral_qs
    
    # Ordena a lista de preview final (pode ter mais de 5 itens agora, limite no template)
    pagar_preview_list.sort(key=lambda x: x.data_vencimento if hasattr(x, 'data_vencimento') else datetime(9999,1,1))
    
    # --- FIM DA LÓGICA DE AGREGAÇÃO ---
    
    # Lógica Receber (mantida)
    # Recomenda-se corrigir o filtro do Receber para usar apenas o status, pois excluir isnull=False é estranho.
    receber_total = Receber.objects.exclude(status='Pago').aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    
    context = { 
        'cont_funcionarios': cont_funcionarios,
        'pagar_total': total_pagar_pendente, # Novo Total Agregado
        'receber_total': receber_total,
        'pagar_preview': pagar_preview_list, # Lista unificada
        'receber_preview': Receber.objects.all()[:5],
    }
    
    return render(request, 'core/dashboard.html', context)