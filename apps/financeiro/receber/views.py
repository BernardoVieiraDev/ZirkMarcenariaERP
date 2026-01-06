import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from itertools import chain

from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

# Importando todos os modelos de Pagamentos (Compras)
from apps.financeiro.pagar.models import (Boleto, Cheque, ComissaoArquiteto,
                                          FaturaCartao, FolhaPagamento,
                                          GastoContabilidade, GastoGasolina,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)

from .forms import (BancoForm, CaixaDiarioForm,
                    MovimentoBancoForm, ReceberForm)
from .models import (Banco, CaixaDiario,
                     MovimentoBanco, Receber)


# --- VIEWS DE CRUD PADRÃO (Lista, Criar, Editar, Excluir) ---

def receber_list(request):
    receber = Receber.objects.all().order_by('data_vencimento')
    
    # === CORREÇÃO: Cálculo do Total Acumulado ===
    total = receber.aggregate(s=Coalesce(Sum('valor'), Decimal(0)))['s']
    
    form = ReceberForm() 
    
    return render(request, 'core/financeiro/receber/list.html', {
        'receber': receber,
        'form': form,
        'total': total  # Passando o total para o template
    })

def receber_create(request):
    if request.method == 'POST':
        form = ReceberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm()
    return render(request, 'core/financeiro/receber/form.html', {'form': form})

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

def receber_delete(request, pk):
    receber = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        receber.delete()
        return redirect('receber:receber')
    return render(request, 'core/financeiro/receber/delete.html', {'receber': receber})


# --- LÓGICA DO RELATÓRIO GERENCIAL (VENDAS E COMPRAS) ---

def _obter_classificacao(item):
    """
    Define se o item é 'VISTA' ou 'PRAZO' baseado no Modelo ou Campo Específico.
    """
    # 1. Se for Venda (Receber), usa o campo explícito
    if hasattr(item, 'tipo_recebimento'):
        return item.tipo_recebimento

    # 2. Se for GastoGeral, usa o campo explícito dele
    if hasattr(item, 'tipo_pagamento'):
        return item.tipo_pagamento

    # 3. Lógica Automática para os outros (Compras/Despesas)
    nome_classe = type(item).__name__

    # Lista de Models que são SEMPRE "A Prazo"
    models_a_prazo = [
        'Boleto', 
        'FaturaCartao', 
        'FolhaPagamento', 
        'ComissaoArquiteto', 
        'PrestacaoEmprestimo',
        'Cheque',
        'GastoVeiculoConsorcio',
        'GastoImovel',
        'GastoContabilidade',
        'GastoUtilidade'
    ]

    if nome_classe in models_a_prazo:
        return 'PRAZO'

    # Se sobrar algum não mapeado, assume PRAZO por segurança
    return 'PRAZO'

def _processar_dados_financeiros(lista_objetos, ano_filtro):
    """
    Recebe uma lista de contas e agrupa por mês, FILTRANDO PELO ANO.
    """
    agrupado = {} # Chave: (ano, mes)
    
    for item in lista_objetos:
        # --- A. Descobrir a Data ---
        data_ref = getattr(item, 'data_vencimento', None)
        if not data_ref: data_ref = getattr(item, 'data_gasto', None)
        if not data_ref: data_ref = getattr(item, 'data_pagamento', None)
            
        if not data_ref: continue 
        
        # === FILTRO DE ANO ===
        if data_ref.year != ano_filtro:
            continue
        # =====================

        chave = (data_ref.year, data_ref.month)
        
        if chave not in agrupado:
            agrupado[chave] = {
                'data': date(data_ref.year, data_ref.month, 1),
                'vista_val': Decimal(0), 
                'prazo_val': Decimal(0), 
                'total': Decimal(0)
            }
            
        # --- B. Descobrir o Valor ---
        valor = getattr(item, 'valor', None)
        if valor is None: valor = getattr(item, 'valor_total', None)
        if valor is None: valor = getattr(item, 'valor_comissao', None)
        valor = valor if valor else Decimal(0)
        
        # --- C. Classificar ---
        classificacao = _obter_classificacao(item)
        
        if classificacao == 'VISTA':
            agrupado[chave]['vista_val'] += valor
        else:
            agrupado[chave]['prazo_val'] += valor
            
        agrupado[chave]['total'] += valor

    # --- D. Finalização (Cálculo de %) ---
    resultado = []
    soma_vista, soma_prazo, soma_total = Decimal(0), Decimal(0), Decimal(0)
    qtd_meses = 0
    
    for chave in sorted(agrupado.keys(), reverse=True):
        dados = agrupado[chave]
        total = dados['total']
        
        dados['vista_perc'] = (dados['vista_val'] / total * 100) if total > 0 else Decimal(0)
        dados['prazo_perc'] = (dados['prazo_val'] / total * 100) if total > 0 else Decimal(0)
        
        resultado.append(dados)
        
        soma_vista += dados['vista_val']
        soma_prazo += dados['prazo_val']
        soma_total += total
        qtd_meses += 1
        
    media = {}
    if qtd_meses > 0:
        media['vista_val'] = soma_vista / qtd_meses
        media['prazo_val'] = soma_prazo / qtd_meses
        media['total'] = soma_total / qtd_meses
        mt = media['total']
        media['vista_perc'] = (media['vista_val'] / mt * 100) if mt > 0 else 0
        media['prazo_perc'] = (media['prazo_val'] / mt * 100) if mt > 0 else 0
        
    return resultado, media

def relatorio_vendas(request):
    """
    Exibe o Relatório Gerencial de Vendas e Compras filtrado por ANO.
    """
    # 1. Determinar o Ano (Padrão: Atual, ou o que vier na URL)
    ano_atual = datetime.now().year
    ano_selecionado = request.GET.get('ano', ano_atual)
    
    try:
        ano_selecionado = int(ano_selecionado)
    except ValueError:
        ano_selecionado = ano_atual

    # 2. Dados de VENDAS
    qs_vendas = Receber.objects.all()
    dados_vendas, media_vendas = _processar_dados_financeiros(qs_vendas, ano_selecionado)

    # 3. Dados de COMPRAS
    # Buscar todos os models
    qs_boletos = Boleto.objects.all()
    qs_gerais = GastoGeral.objects.all()
    qs_cartao = FaturaCartao.objects.all()
    qs_util = GastoUtilidade.objects.all()
    qs_cheque = Cheque.objects.all()
    qs_emp = PrestacaoEmprestimo.objects.all()
    qs_veic = GastoVeiculoConsorcio.objects.all()
    qs_cont = GastoContabilidade.objects.all()
    qs_imov = GastoImovel.objects.all()
    qs_gas = GastoGasolina.objects.all()
    qs_folha = FolhaPagamento.objects.all()
    qs_comissao = ComissaoArquiteto.objects.all()
    
    todos_pagar = list(chain(
        qs_boletos, qs_gerais, qs_cartao, qs_util, qs_cheque, 
        qs_emp, qs_veic, qs_cont, qs_imov, qs_gas, qs_folha, qs_comissao
    ))
    
    dados_compras, media_compras = _processar_dados_financeiros(todos_pagar, ano_selecionado)

    return render(request, 'core/financeiro/receber/relatorios_vendas.html', {
        'dados_vendas': dados_vendas,
        'media_vendas': media_vendas,
        'dados_compras': dados_compras,
        'media_compras': media_compras,
        'ano_selecionado': ano_selecionado, 
        'proximo_ano': ano_selecionado + 1,
        'ano_anterior': ano_selecionado - 1,
    })


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

def caixa_diario_delete(request, pk):
    item = get_object_or_404(CaixaDiario, pk=pk)
    # Redireciona de volta para o mês do item deletado
    ano = item.data.year
    mes = item.data.month
    
    if request.method == 'POST':
        item.delete()
        return redirect(f'/receber/caixa-diario/?ano={ano}&mes={mes}')
    
    return render(request, 'core/financeiro/receber/delete.html', {'receber': item}) 


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

def movimento_banco_delete(request, pk):
    item = get_object_or_404(MovimentoBanco, pk=pk)
    ano = item.data.year
    mes = item.data.month
    banco_id = item.banco.id
    
    if request.method == 'POST':
        item.delete()
        return redirect(f'/receber/movimento-banco/?banco_id={banco_id}&ano={ano}&mes={mes}')
    
    return render(request, 'core/financeiro/receber/delete.html', {'receber': item})


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

def banco_delete(request, pk):
    banco = get_object_or_404(Banco, pk=pk)
    if request.method == 'POST':
        banco.delete()
        return redirect('receber:bancos_list')
    return render(request, 'core/financeiro/receber/delete.html', {'receber': banco, 'titulo': f'Excluir Banco {banco.nome}'})


# --- MOVIMENTAÇÃO BANCÁRIA ---

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