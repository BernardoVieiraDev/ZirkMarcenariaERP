from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (BoletoForm, ChequeForm, FaturaCartaoForm,
                    GastoContabilidadeForm, GastoGasolinaForm, GastoGeralForm,
                    GastoImovelForm, GastoUtilidadeForm,
                    GastoVeiculoConsorcioForm, PrestacaoEmprestimoForm,
                    TipoGastoForm, FolhaPagamentoForm, ComissaoArquitetoForm)
from .models import (Boleto, Cheque, FaturaCartao, GastoBase,
                     GastoContabilidade, GastoGasolina, GastoGeral,
                     GastoImovel, GastoUtilidade, GastoVeiculoConsorcio,
                     PrestacaoEmprestimo, FolhaPagamento, ComissaoArquiteto)

# ----------------------------------------------------
# MAPA DE MODELOS
# ----------------------------------------------------

MODEL_FORM_MAP = {
    'Boleto': {'model': Boleto, 'form': BoletoForm, 'title': 'Novo Boleto'},
    'FaturaCartao': {'model': FaturaCartao, 'form': FaturaCartaoForm, 'title': 'Nova Fatura de Cartão'},
    'PrestacaoEmprestimo': {'model': PrestacaoEmprestimo, 'form': PrestacaoEmprestimoForm, 'title': 'Nova Prestação de Empréstimo'},
    'GastoVeiculoConsorcio': {'model': GastoVeiculoConsorcio, 'form': GastoVeiculoConsorcioForm, 'title': 'Novo Gasto Veicular'},
    'GastoContabilidade': {'model': GastoContabilidade, 'form': GastoContabilidadeForm, 'title': 'Novo Encargo Contábil'},
    'GastoImovel': {'model': GastoImovel, 'form': GastoImovelForm, 'title': 'Novo Gasto Imobiliário (IPTU/Condomínio)'},
    'GastoUtilidade': {'model': GastoUtilidade, 'form': GastoUtilidadeForm, 'title': 'Nova Conta de Utilidade'},
    'GastoGeral': {'model': GastoGeral, 'form': GastoGeralForm, 'title': 'Novo Gasto Geral'},
    'GastoGasolina': {'model': GastoGasolina, 'form': GastoGasolinaForm, 'title': 'Novo Gasto com Gasolina'},
    'Cheque': {'model': Cheque, 'form': ChequeForm, 'title': 'Novo Gasto com Cheque'},
    'FolhaPagamento': {'model': FolhaPagamento, 'form': FolhaPagamentoForm, 'title': 'Folha pagamento'},
    'ComissaoArquiteto': {'model': ComissaoArquiteto, 'form': ComissaoArquitetoForm, 'title': 'Comissão Arquitetos'}
}

# ----------------------------------------------------
# AUXILIARES
# ----------------------------------------------------

def _get_gasto_object_info(pk):
    """Retorna (ModelClass, obj, FormClass, title)"""
    for data in MODEL_FORM_MAP.values():
        ModelClass = data['model']
        try:
            obj = ModelClass.objects.get(pk=pk)
            return ModelClass, obj, data['form'], data['title']
        except ModelClass.DoesNotExist:
            continue
    return None

def sort_key(obj):
    """Garantir ordenação compatível entre todos os modelos."""
    campos_data = ['data_vencimento', 'data_gasto', 'data_emissao', 'data_referencia', 'data_pagamento']
    
    for campo in campos_data:
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor:
                return valor
    return date(1900, 1, 1)

# ----------------------------------------------------
# VIEW - LISTAGEM (DASHBOARDS SEPARADOS)
# ----------------------------------------------------

def pagar_list(request):
    # Definição das Categorias
    cat_operacional = ['GastoGeral', 'GastoGasolina']
    cat_folha = ['FolhaPagamento']
    cat_comissao = ['ComissaoArquiteto']
    # Obs: Todo o resto vai para 'Contas a Pagar'
    
    # Inicializa as listas
    list_contas = []
    list_operacional = []
    list_folha = []
    list_comissao = []
    
    combined_all = [] # Apenas para cálculo dos totais globais

    for key, data in MODEL_FORM_MAP.items():
        ModelClass = data['model']
        qs = ModelClass.objects.all()
        
        # Distribui nas listas corretas
        if key in cat_operacional:
            list_operacional.extend(qs)
        elif key in cat_folha:
            list_folha.extend(qs)
        elif key in cat_comissao:
            list_comissao.extend(qs)
        else:
            list_contas.extend(qs)
            
        combined_all.extend(qs)

    # Ordenação das listas
    list_contas.sort(key=sort_key, reverse=True)
    list_operacional.sort(key=sort_key, reverse=True)
    list_folha.sort(key=sort_key, reverse=True)
    list_comissao.sort(key=sort_key, reverse=True)
    combined_all.sort(key=sort_key, reverse=True)

    # Totais Globais
    total_pendente = sum(
        item.get_valor_consolidado() for item in combined_all 
        if getattr(item, 'status', '') not in ['Pago', 'PG']
    )
    
    total_pago = sum(
        item.get_valor_consolidado() for item in combined_all 
        if getattr(item, 'status', '') in ['Pago', 'PG']
    )
    
    form_selecao = TipoGastoForm()

    return render(request, 'core/financeiro/pagar/list.html', {
        'list_contas': list_contas,
        'list_operacional': list_operacional,
        'list_folha': list_folha,
        'list_comissao': list_comissao,
        
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'total_registros': len(combined_all),
        
        'tipos_disponiveis': MODEL_FORM_MAP.keys(),
        'form_selecao': form_selecao,
    })

# ----------------------------------------------------
# VIEW - CRIAÇÃO
# ----------------------------------------------------

def pagar_create(request):
    is_modal = request.GET.get('modal') == 'true' or request.POST.get('modal') == 'true'
    template_name = 'core/financeiro/pagar/form_content.html' if is_modal else 'core/financeiro/pagar/form_detalhe.html'
    title = 'Nova Conta a Pagar'

    if request.method == 'POST':
        tipo = request.POST.get('categoria')

        if tipo and tipo in MODEL_FORM_MAP:
            FormClass = MODEL_FORM_MAP[tipo]['form']
            title = MODEL_FORM_MAP[tipo]['title']
            form = FormClass(request.POST)

            if form.is_valid():
                form.save()
                return redirect('pagar:pagar_list')

            return render(request, template_name, {
                'form': form, 'title': title, 'tipo': tipo,
            })

        tipo_form = TipoGastoForm(request.POST)
        if tipo_form.is_valid():
            tipo = tipo_form.cleaned_data['categoria']
            return redirect(f"{request.path}?tipo={tipo}")

        return render(request, 'core/financeiro/pagar/form_selecao.html', {
            'tipo_form': tipo_form, 'title': title,
        })

    tipo = request.GET.get('tipo')
    if tipo and tipo in MODEL_FORM_MAP:
        FormClass = MODEL_FORM_MAP[tipo]['form']
        form = FormClass()
        return render(request, template_name, {
            'form': form, 'title': MODEL_FORM_MAP[tipo]['title'], 'tipo': tipo, 
        })

    return render(request, 'core/financeiro/pagar/form_selecao.html', {
        'tipo_form': TipoGastoForm(), 'title': 'Nova Conta a Pagar - Seleção',
    })

# ----------------------------------------------------
# EDITAR / DELETAR
# ----------------------------------------------------

def pagar_edit(request, pk):
    found = _get_gasto_object_info(pk)
    if not found: raise Http404("Gasto não encontrado.")
    ModelClass, obj, FormClass, title = found

    if request.method == 'POST':
        form = FormClass(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('pagar:pagar_list')
    else:
        form = FormClass(instance=obj)

    return render(request, 'core/financeiro/pagar/form_detalhe.html', {
        'form': form, 'title': f'Editar {title}', 'object': obj,
    })

def pagar_delete(request, pk):
    found = _get_gasto_object_info(pk)
    if not found: raise Http404("Gasto não encontrado.")
    ModelClass, obj, _, title = found

    if request.method == 'POST':
        obj.delete()
        return redirect('pagar:pagar_list')

    return render(request, 'core/financeiro/pagar/delete.html', {
        'object': obj, 'title': f'Excluir {title}',
    })