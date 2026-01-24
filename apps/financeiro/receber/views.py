import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from apps.financeiro.utils import gerar_parcelas

from .forms import (BancoForm, CaixaDiarioForm, ConfirmarRecebimentoForm,
                    MovimentoBancoForm, ReceberForm)
from .models import Banco, CaixaDiario, MovimentoBanco, Receber


@login_required
def receber_list(request):
    # 1. Parâmetros de Filtro
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    data_inicio_get = request.GET.get('data_inicio')
    data_fim_get = request.GET.get('data_fim')
    
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    sort_order = request.GET.get('order', 'asc') # Default asc para ver vencimentos próximos

    start_date = None
    end_date = None
    usar_filtro_personalizado = False

    # 2. Lógica de Data (Prioridade: Intervalo > Mês/Ano)
    if data_inicio_get:
        try:
            start_date = datetime.strptime(data_inicio_get, '%Y-%m-%d').date()
            usar_filtro_personalizado = True
        except ValueError:
            pass
            
    if data_fim_get:
        try:
            end_date = datetime.strptime(data_fim_get, '%Y-%m-%d').date()
            usar_filtro_personalizado = True
        except ValueError:
            pass

    if usar_filtro_personalizado:
        mes = None
        ano = None
    elif mes and ano:
        try:
            mes = int(mes)
            ano = int(ano)
            start_date = date(ano, mes, 1)
            ultimo_dia = calendar.monthrange(ano, mes)[1]
            end_date = date(ano, mes, ultimo_dia)
        except ValueError:
            pass

    # 3. Querysets Iniciais
    # Filtrar Receber
    receber_qs = Receber.objects.select_related('cliente', 'banco_destino', 'contrato_rt').filter(is_deleted=False)
    
    # Filtrar Caixa Diário (Apenas Entradas e que NÃO sejam origem de um Receber para não duplicar)
    caixa_qs = CaixaDiario.objects.filter(is_deleted=False, tipo='E', recebimento_origem__isnull=True)

    # 4. Aplicação de Filtros Textuais e Status (Antes de tudo para reduzir o conjunto)
    if search_query:
        receber_qs = receber_qs.filter(
            Q(descricao__icontains=search_query) | 
            Q(cliente__nome__icontains=search_query) |
            Q(categoria__icontains=search_query)
        )
        caixa_qs = caixa_qs.filter(historico__icontains=search_query)

    if status_filter:
        if status_filter == 'Recebido':
            receber_qs = receber_qs.filter(status='Recebido')
            # Caixa é sempre recebido, mantém
        elif status_filter == 'Pendente':
            receber_qs = receber_qs.exclude(status='Recebido')
            caixa_qs = caixa_qs.none() # Caixa não tem pendente
        elif status_filter == 'Atrasado':
            # Considera atrasado se não recebido e vencimento < hoje
            receber_qs = receber_qs.filter(status='Pendente', data_vencimento__lt=date.today())
            caixa_qs = caixa_qs.none()

    # 5. Aplicação dos Filtros de Data e Flag de Limite
    aplicar_limite_seguranca = False

    if start_date and end_date:
        receber_qs = receber_qs.filter(data_vencimento__range=(start_date, end_date))
        caixa_qs = caixa_qs.filter(data__range=(start_date, end_date))
    elif start_date:
        receber_qs = receber_qs.filter(data_vencimento__gte=start_date)
        caixa_qs = caixa_qs.filter(data__gte=start_date)
    elif end_date:
        receber_qs = receber_qs.filter(data_vencimento__lte=end_date)
        caixa_qs = caixa_qs.filter(data__lte=end_date)
    else:
        # Se não tem filtro de data, marcamos para aplicar o limite APÓS a ordenação
        aplicar_limite_seguranca = True

    # 6. Ordenação (OBRIGATÓRIO vir ANTES do slice/limite)
    if sort_order == 'desc':
        receber_qs = receber_qs.order_by('-data_vencimento')
        caixa_qs = caixa_qs.order_by('-data')
    else:
        receber_qs = receber_qs.order_by('data_vencimento')
        caixa_qs = caixa_qs.order_by('data')

    # 7. Aplicação do Limite de Segurança (Slice)
    if aplicar_limite_seguranca:
        receber_qs = receber_qs[:2000]
        caixa_qs = caixa_qs[:2000]

    # 8. Cálculo de Totais (Iterando sobre a lista resultante para performance e precisão do que é exibido)
    total_pendente = Decimal('0.00')
    total_recebido = Decimal('0.00')
    
    # Converter para lista para iterar e passar ao template
    list_receber = list(receber_qs)
    list_caixa = list(caixa_qs)

    # Iterar Receber
    for r in list_receber:
        if r.status == 'Recebido':
            total_recebido += (r.valor_recebido or r.valor)
        else:
            total_pendente += r.valor
            
    # Iterar Caixa (Tudo é recebido)
    for c in list_caixa:
        total_recebido += c.valor

    total_geral = total_pendente + total_recebido
    total_registros = len(list_receber) + len(list_caixa)

    form = ReceberForm()

    return render(request, 'core/financeiro/receber/list.html', {
        'list_receber': list_receber,
        'list_caixa': list_caixa,
        'total_pendente': total_pendente,
        'total_recebido': total_recebido,
        'total_geral': total_geral,
        'total_registros': total_registros,
        'form': form,
        'today': date.today(),
        
        # Filtros para o template
        'filtros_ativos': {
            'mes': mes, 
            'ano': ano, 
            'q': search_query, 
            'status': status_filter, 
            'order': sort_order,
            'data_inicio': data_inicio_get,
            'data_fim': data_fim_get
        },
        'mes_atual': mes if mes else '',
        'ano_atual': ano if ano else '',
    })

@login_required
def receber_create(request):
    initial_data = {}
    if request.GET.get('contrato_id'):
        contrato_id = request.GET.get('contrato_id')
        initial_data['contrato_rt'] = contrato_id
        initial_data['valor'] = request.GET.get('valor')
        initial_data['descricao'] = request.GET.get('descricao')
    
    # Instancia o formulário com POST (se existir) ou None (para GET)
    form = ReceberForm(request.POST or None, initial=initial_data)
    
    if request.method == 'POST':
        if form.is_valid():
            # Não salva ainda (commit=False)
            recebimento = form.save(commit=False)
            
            # Pega a qtd de parcelas do form (limpo)
            qtd_parcelas = form.cleaned_data.get('parcelas', 1)
            
            if qtd_parcelas > 1:
                # Chama o gerador de parcelas
                gerar_parcelas(recebimento, qtd_parcelas, form.cleaned_data)
            else:
                # Salva normalmente
                recebimento.save()
    
            return redirect('receber:receber')

    # Esta linha agora é alcançada se for GET ou se o form for inválido no POST
    return render(request, 'core/financeiro/receber/form.html', {'form': form})

@login_required
def receber_edit(request, pk):
    receber = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        form = ReceberForm(request.POST, instance=receber)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm(instance=receber)
    return render(request, 'core/financeiro/receber/form.html', {'form': form})

@login_required
def receber_delete(request, pk):
    receber = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        receber.delete()
        return redirect('receber:receber')
    return render(request, 'core/financeiro/receber/delete.html', {'receber': receber})

@login_required
def caixa_diario_view(request):
    # 1. Definição do Período (Mês/Ano)
    hoje = date.today()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        ano = hoje.year
        mes = hoje.month

    # Datas limites do mês selecionado
    data_inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_fim = date(ano, mes, ultimo_dia)

    # 2. Processar Formulário de Adição (Quick Add na mesma página)
    if request.method == 'POST':
        form = CaixaDiarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(f'{request.path}?ano={ano}&mes={mes}')
    else:
        # Traz a data de hoje pré-preenchida se estiver dentro do mês visualizado
        initial_date = hoje if (hoje.year == ano and hoje.month == mes) else data_inicio
        form = CaixaDiarioForm(initial={'data': initial_date, 'tipo': 'S'})

    # 3. Cálculo do SALDO ANTERIOR (Tudo antes do dia 01 do mês atual)
    # Soma entradas anteriores
    entradas_ant = CaixaDiario.objects.filter(data__lt=data_inicio, tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    # Soma saídas anteriores
    saidas_ant = CaixaDiario.objects.filter(data__lt=data_inicio, tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    saldo_anterior = entradas_ant - saidas_ant

    # 4. Movimentações do Mês Atual
    movimentacoes = CaixaDiario.objects.filter(
        data__year=ano, 
        data__month=mes
    ).order_by('-data', '-id')

    # Totais do mês
    total_entradas_mes = movimentacoes.filter(tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    total_saidas_mes = movimentacoes.filter(tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']

    # 5. Saldo Atual (Final do Mês)
    saldo_atual = saldo_anterior + total_entradas_mes - total_saidas_mes

    # 6. Navegação de Meses
    data_nav = date(ano, mes, 1)
    prox_mes_data = data_nav + timedelta(days=32)
    prox_mes_data = prox_mes_data.replace(day=1)
    
    ant_mes_data = data_nav - timedelta(days=1)
    ant_mes_data = ant_mes_data.replace(day=1)

    context = {
        'movimentacoes': movimentacoes,
        'saldo_anterior': saldo_anterior,
        'total_entradas': total_entradas_mes,
        'total_saidas': total_saidas_mes,
        'saldo_atual': saldo_atual,
        'form': form,
        'mes_atual': mes,
        'ano_atual': ano,
        'data_ref': data_nav, # Para exibir "Janeiro de 2025"
        'prox_mes': prox_mes_data.month,
        'prox_ano': prox_mes_data.year,
        'ant_mes': ant_mes_data.month,
        'ant_ano': ant_mes_data.year,
    }

    return render(request, 'core/financeiro/receber/caixa_diario.html', context)

@login_required
def caixa_diario_delete(request, pk):
    item = get_object_or_404(CaixaDiario, pk=pk)
    # Redireciona de volta para o mês do item deletado
    ano = item.data.year
    mes = item.data.month
    
    if request.method == 'POST':
        item.delete()
        return redirect(f'/receber/caixa-diario/?ano={ano}&mes={mes}')
    
    return render(request, 'core/financeiro/receber/delete.html', {'receber': item}) 

@login_required
def movimento_banco_view(request):
    # 1. Identificar qual Banco estamos visualizando
    todos_bancos = Banco.objects.all()
    
    if not todos_bancos.exists():
        return redirect('receber:bancos_list') # Redireciona para criar um banco se não houver nenhum

    banco_id = request.GET.get('banco_id')
    
    if banco_id:
        banco_selecionado = get_object_or_404(Banco, pk=banco_id)
    else:
        banco_selecionado = todos_bancos.first() # Pega o primeiro se não for passado nada

    # 2. Definição do Período (Mês/Ano)
    hoje = date.today()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except ValueError:
        ano = hoje.year
        mes = hoje.month

    data_inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    
    # 3. Processar Formulário de Lançamento
    if request.method == 'POST':
        form = MovimentoBancoForm(request.POST)
        if form.is_valid():
            movimento = form.save(commit=False)
            movimento.banco = banco_selecionado # Associa ao banco atual da tela
            movimento.save()
            return redirect(f'{request.path}?banco_id={banco_selecionado.id}&ano={ano}&mes={mes}')
    else:
        initial_date = hoje if (hoje.year == ano and hoje.month == mes) else data_inicio
        form = MovimentoBancoForm(initial={'data': initial_date, 'tipo': 'S'})

    # 4. Cálculos de Saldo (Filtrando pelo Banco Selecionado)
    
    # Saldo Inicial fixo do cadastro do banco
    saldo_inicial_cadastro = banco_selecionado.saldo_inicial

    # Movimentações anteriores ao mês atual (acumulado histórico)
    entradas_ant = MovimentoBanco.objects.filter(
        banco=banco_selecionado, 
        data__lt=data_inicio, 
        tipo='E'
    ).aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    saidas_ant = MovimentoBanco.objects.filter(
        banco=banco_selecionado, 
        data__lt=data_inicio, 
        tipo='S'
    ).aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    saldo_anterior = saldo_inicial_cadastro + entradas_ant - saidas_ant

    # 5. Movimentações do Mês Atual
    movimentacoes = MovimentoBanco.objects.filter(
        banco=banco_selecionado,
        data__year=ano, 
        data__month=mes
    ).order_by('-data', '-id')

    total_entradas_mes = movimentacoes.filter(tipo='E').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    total_saidas_mes = movimentacoes.filter(tipo='S').aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']

    saldo_atual = saldo_anterior + total_entradas_mes - total_saidas_mes

    # 6. Navegação
    data_nav = date(ano, mes, 1)
    prox_mes_data = (data_nav + timedelta(days=32)).replace(day=1)
    ant_mes_data = (data_nav - timedelta(days=1)).replace(day=1)

    context = {
        'todos_bancos': todos_bancos,
        'banco_selecionado': banco_selecionado,
        'movimentacoes': movimentacoes,
        'saldo_anterior': saldo_anterior,
        'total_entradas': total_entradas_mes,
        'total_saidas': total_saidas_mes,
        'saldo_atual': saldo_atual,
        'form': form,
        'mes_atual': mes,
        'ano_atual': ano,
        'data_ref': data_nav,
        'prox_mes': prox_mes_data.month,
        'prox_ano': prox_mes_data.year,
        'ant_mes': ant_mes_data.month,
        'ant_ano': ant_mes_data.year,
    }

    return render(request, 'core/financeiro/receber/movimento_banco.html', context)

@login_required
def movimento_banco_delete(request, pk):
    item = get_object_or_404(MovimentoBanco, pk=pk)
    ano = item.data.year
    mes = item.data.month
    banco_id = item.banco.id
    
    if request.method == 'POST':
        item.delete()
        return redirect(f'/receber/movimento-banco/?banco_id={banco_id}&ano={ano}&mes={mes}')
    
    return render(request, 'core/financeiro/receber/delete.html', {'receber': item})

@login_required
def bancos_list(request):
    bancos = Banco.objects.all()
    if request.method == 'POST':
        form = BancoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('receber:bancos_list')
    else:
        form = BancoForm()
    
    return render(request, 'core/financeiro/receber/banco_list.html', {'bancos': bancos, 'form': form})

@login_required
def banco_edit(request, pk):
    banco = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        form = BancoForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            return redirect('receber:bancos_list')
    else:
        form = BancoForm(instance=banco)
    
    return render(request, 'core/financeiro/receber/banco_form.html', {'form': form, 'banco': banco})

@login_required
def banco_delete(request, pk):
    banco = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        banco.delete()
        return redirect('receber:bancos_list')
    return render(request, 'core/financeiro/receber/delete.html', {'receber': banco, 'titulo': f'Excluir Banco {banco.nome}'})


# --- MOVIMENTAÇÃO BANCÁRIA ---

@login_required
def movimento_banco_edit(request, pk):
    movimento = get_object_or_404(MovimentoBanco, pk=pk)
    banco_id = movimento.banco.id
    ano = movimento.data.year
    mes = movimento.data.month
    
    if request.method == 'POST':
        form = MovimentoBancoForm(request.POST, instance=movimento)
        if form.is_valid():
            form.save()
            # Redireciona mantendo o filtro do banco e data
            return redirect(f'/receber/movimento-banco/?banco_id={banco_id}&ano={ano}&mes={mes}')
    else:
        form = MovimentoBancoForm(instance=movimento)
        
    return render(request, 'core/financeiro/receber/movimento_banco_form.html', {
        'form': form, 
        'movimento': movimento
    })


@login_required
def receber_confirmar_recebimento(request, pk):
    receber = get_object_or_404(Receber, pk=pk)
    
    # Se já estiver pago, avisa e volta
    if receber.status == 'Recebido':
        messages.warning(request, f"Esta parcela já consta como recebida.")
        if receber.contrato_rt:
            return redirect('comissionamento:contrato_detail', pk=receber.contrato_rt.pk)
        return redirect('receber:receber')

    if request.method == 'POST':
        form = ConfirmarRecebimentoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Atualiza o objeto Receber
            receber.status = 'Recebido'
            receber.data_recebimento = data['data_recebimento']
            receber.valor_recebido = data['valor_recebido']
            receber.forma_recebimento = data['forma_recebimento']
            receber.banco_destino = data['banco_destino'] # Será None se for CAIXA
            
            # Adiciona observação se houver
            if data['observacoes']:
                obs_atual = receber.observacoes or ""
                receber.observacoes = f"{obs_atual} | Baixa: {data['observacoes']}".strip(' | ')

            # O signal (se existir) ou a lógica de save deve criar o movimento financeiro
            # Se você não tiver signals automáticos, precisaria criar o MovimentoBanco/CaixaDiario aqui manualmente.
            # Assumindo que seu sistema já tem signals para 'Receber' igual tem para 'Pagar':
            receber.save()
            
            messages.success(request, f"Recebimento de {receber.descricao} confirmado!")
            
            # Redirecionamento Inteligente
            if receber.contrato_rt:
                return redirect('comissionamento:contrato_detail', pk=receber.contrato_rt.pk)
            return redirect('receber:receber')
    else:
        # Preenche com valores padrão
        initial_data = {
            'data_recebimento': date.today(),
            'valor_recebido': receber.valor, # Sugere o valor total
            'destino_recebimento': 'BANCO' if receber.banco_destino else 'CAIXA',
            'banco_destino': receber.banco_destino,
            'forma_recebimento': receber.forma_recebimento
        }
        form = ConfirmarRecebimentoForm(initial=initial_data)

    return render(request, 'core/financeiro/receber/form_modal_recebimento.html', {
        'form': form,
        'object': receber,
        'title': f'Confirmar Recebimento'
    })