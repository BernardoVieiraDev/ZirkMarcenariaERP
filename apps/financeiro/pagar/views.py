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
    'ComissaoArquiteto': {'model': ComissaoArquiteto, 'form': ComissaoArquitetoForm, 'title': 'Comissão ARquitetos'}
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
    for campo in ['data_vencimento', 'data_gasto', 'data_emissao']:
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor:
                return valor
    return date(1900, 1, 1)

# ----------------------------------------------------
# VIEW - LISTAGEM
# ----------------------------------------------------

# No arquivo apps/financeiro/pagar/views.py

def pagar_list(request):
    combined = []
    for data in MODEL_FORM_MAP.values():
        ModelClass = data['model']
        qs = ModelClass.objects.all()
        combined.extend(qs)

    combined.sort(key=sort_key, reverse=True)

    total_pendente = sum(
        item.get_valor_consolidado() for item in combined 
        if item.status != 'Pago' and item.status != 'PG'
    )
    
    total_pago = sum(
        item.get_valor_consolidado() for item in combined 
        if item.status == 'Pago' or item.status == 'PG'
    )
    
    # --- NOVO: Form para o Modal de Seleção ---
    form_selecao = TipoGastoForm()

    return render(request, 'core/financeiro/pagar/list.html', {
        'list': combined,
        'total': total_pendente, # Usado no resumo
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'tipos_disponiveis': MODEL_FORM_MAP.keys(),
        'form_selecao': form_selecao, # Adicionado ao contexto
    })

# ----------------------------------------------------
# VIEW - CRIAÇÃO
# ----------------------------------------------------

def pagar_create(request):
    # Verifica se a requisição veio do Modal (parametro GET ou POST)
    is_modal = request.GET.get('modal') == 'true' or request.POST.get('modal') == 'true'
    
    # Define qual template renderizar
    template_name = 'core/financeiro/pagar/form_content.html' if is_modal else 'core/financeiro/pagar/form_detalhe.html'
    
    title = 'Nova Conta a Pagar'

    # 1) POST — tentativa de salvar gasto
    if request.method == 'POST':
        tipo = request.POST.get('categoria')

        if tipo and tipo in MODEL_FORM_MAP:
            FormClass = MODEL_FORM_MAP[tipo]['form']
            title = MODEL_FORM_MAP[tipo]['title']

            form = FormClass(request.POST)

            if form.is_valid():
                form.save()
                return redirect('pagar:pagar_list')

            # Se der erro, retorna o template (parcial se for modal, completo se não)
            return render(request, template_name, {
                'form': form,
                'title': title,
                'tipo': tipo,
            })

        # 2) POST sem tipo (Seleção inicial via POST convencional - fallback)
        tipo_form = TipoGastoForm(request.POST)
        if tipo_form.is_valid():
            tipo = tipo_form.cleaned_data['categoria']
            return redirect(f"{request.path}?tipo={tipo}")

        return render(request, 'core/financeiro/pagar/form_selecao.html', {
            'tipo_form': tipo_form,
            'title': title,
        })

    # 3) GET → usuário escolheu tipo por ?tipo=XYZ (Chamada AJAX do Modal cai aqui)
    tipo = request.GET.get('tipo')

    if tipo and tipo in MODEL_FORM_MAP:
        FormClass = MODEL_FORM_MAP[tipo]['form']
        form = FormClass()
        return render(request, template_name, {
            'form': form,
            'title': MODEL_FORM_MAP[tipo]['title'],
            'tipo': tipo, 
        })

    # 4) GET → Tela de seleção (Fallback)
    return render(request, 'core/financeiro/pagar/form_selecao.html', {
        'tipo_form': TipoGastoForm(),
        'title': 'Nova Conta a Pagar - Seleção',
    })

# ----------------------------------------------------
# EDITAR
# ----------------------------------------------------

def pagar_edit(request, pk):
    found = _get_gasto_object_info(pk)
    if not found:
        raise Http404("Gasto não encontrado.")

    ModelClass, obj, FormClass, title = found

    if request.method == 'POST':
        form = FormClass(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('pagar:pagar_list')
    else:
        form = FormClass(instance=obj)

    return render(request, 'core/financeiro/pagar/form_detalhe.html', {
        'form': form,
        'title': f'Editar {title}',
        'object': obj,
    })

# ----------------------------------------------------
# DELETAR
# ----------------------------------------------------

def pagar_delete(request, pk):
    found = _get_gasto_object_info(pk)
    if not found:
        raise Http404("Gasto não encontrado.")

    ModelClass, obj, _, title = found

    if request.method == 'POST':
        obj.delete()
        return redirect('pagar:pagar_list')

    return render(request, 'core/financeiro/pagar/delete.html', {
        'object': obj,
        'title': f'Excluir {title}',
    })


# ... seus outros imports ...