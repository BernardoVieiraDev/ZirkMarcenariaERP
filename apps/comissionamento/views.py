from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.db.models import Sum
from .models import Arquiteta, ContratoRT, PagamentoRT
from decimal import Decimal
from .forms import ArquitetaForm, ContratoRTForm, PagamentoRTForm
from django.contrib import messages

def rt_contratos_list(request):
    """
    Lista unificada de todos os Contratos RT ativos.
    """
    contratos = ContratoRT.objects.select_related('arquiteta').order_by('arquiteta__nome', '-data_contrato')
    total_rt_devida = contratos.aggregate(sum_rt=Sum('saldo_devedor'))['sum_rt'] or Decimal('0.00')
    
    # Formulário vazio para o Modal de Novo Contrato
    form = ContratoRTForm()
    
    context = {
        'contratos': contratos,
        'total_rt_devida': total_rt_devida,
        'title': 'Gestão de Contratos de Remuneração Técnica (RT)',
        'form': form,
    }
    return render(request, 'core/comissionamento/contratos_list.html', context)

def rt_contrato_create(request):
    if request.method == 'POST':
        form = ContratoRTForm(request.POST)
        if form.is_valid():
            contrato = form.save()
            messages.success(request, f"Contrato RT para {contrato.cliente} cadastrado com sucesso!")
            return redirect('comissionamento:contratos_list') 
    else:
        form = ContratoRTForm()
        
    context = {'form': form, 'title': 'Cadastrar Novo Contrato de RT'}
    return render(request, 'core/comissionamento/contrato_form.html', context)

def rt_contrato_edit(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    if request.method == 'POST':
        form = ContratoRTForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contrato RT de {contrato.cliente} atualizado com sucesso!")
            # Redireciona de volta para quem chamou (lista ou detalhe)
            return redirect(request.META.get('HTTP_REFERER', 'comissionamento:contratos_list'))
    else:
        form = ContratoRTForm(instance=contrato)
        
    context = {
        'form': form,
        'title': f'Editar Contrato RT: {contrato.cliente}',
        'contrato': contrato,
        'edit_mode': True
    }
    return render(request, 'core/comissionamento/contrato_form.html', context)

def rt_contrato_delete(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    tem_pagamentos = contrato.pagamentort_set.exists()

    if request.method == 'POST':
        cliente_nome = contrato.cliente
        contrato.delete()
        messages.success(request, f"Contrato RT de {cliente_nome} excluído com sucesso.")
        return redirect('comissionamento:contratos_list')
        
    context = {
        'contrato': contrato,
        'tem_pagamentos': tem_pagamentos,
        'title': f'Confirmar Exclusão do Contrato RT: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_delete.html', context)

def rt_contrato_detail(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    pagamentos = PagamentoRT.objects.filter(contrato=contrato).order_by('-data_pagamento')
    total_pago = pagamentos.aggregate(sum_pgto=Sum('valor_pago'))['sum_pgto'] or Decimal('0.00')
    
    context = {
        'contrato': contrato,
        'pagamentos': pagamentos,
        'total_pago': total_pago,
        'title': f'Detalhe RT: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_detail.html', context)

# --- VIEWS DE PAGAMENTO ---

def rt_pagamento_create(request, contrato_pk):
    contrato = get_object_or_404(ContratoRT, pk=contrato_pk)
            
    if request.method == 'POST':
        form = PagamentoRTForm(request.POST)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.contrato = contrato
            pagamento.save()
            messages.success(request, "Pagamento registrado com sucesso.")
            return redirect('comissionamento:contrato_detail', pk=contrato.pk)
    else:
        form = PagamentoRTForm()
        
    context = {
        'form': form,
        'contrato': contrato,
        'title': f'Registrar Pagamento para {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/pagamento_form.html', context)

def rt_pagamento_edit(request, pk):
    pagamento = get_object_or_404(PagamentoRT, pk=pk)
    
    if request.method == 'POST':
        form = PagamentoRTForm(request.POST, instance=pagamento)
        if form.is_valid():
            form.save()
            messages.success(request, "Pagamento atualizado com sucesso.")
            return redirect('comissionamento:contrato_detail', pk=pagamento.contrato.pk)
    else:
        form = PagamentoRTForm(instance=pagamento)
    
    context = {
        'form': form,
        'contrato': pagamento.contrato,
        'title': 'Editar Pagamento'
    }
    # Reutiliza o form de pagamento
    return render(request, 'core/comissionamento/pagamento_form.html', context)

def rt_pagamento_delete(request, pk):
    pagamento = get_object_or_404(PagamentoRT, pk=pk)
    contrato_pk = pagamento.contrato.pk
    
    if request.method == 'POST':
        pagamento.delete()
        messages.success(request, "Pagamento excluído com sucesso.")
        return redirect('comissionamento:contrato_detail', pk=contrato_pk)
    
    # Renderiza um template simples de confirmação para ser carregado no modal
    # Podemos usar um template genérico ou reutilizar o contrato_delete com adaptações
    context = {
        'object': pagamento,
        'title': 'Excluir Pagamento'
    }
    # Vamos criar um template inline simples para o delete do pagamento se preferir,
    # mas para manter padrão, usarei um HTML simples retornado ou um template específico.
    # Vou usar um template específico bem simples.
    return render(request, 'core/comissionamento/pagamento_delete.html', context)

# --- VIEWS DE ARQUITETA (Mantidas iguais, omitidas por brevidade se não houve alteração) ---
def arquiteta_create(request):
    if request.method == 'POST':
        form = ArquitetaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('comissionamento:contratos_list') 
    else:
        form = ArquitetaForm()
    context = {'form': form, 'title': 'Cadastrar Nova Arquiteta'}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)

def arquiteta_list(request):
    arquitetas = Arquiteta.objects.all().order_by('nome')
    form = ArquitetaForm()
    context = {'arquitetas': arquitetas, 'title': 'Cadastro de Arquitetas', 'form': form}
    return render(request, 'core/comissionamento/arquiteta_list.html', context)

def arquiteta_edit(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    if request.method == 'POST':
        form = ArquitetaForm(request.POST, instance=arquiteta)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cadastro de {arquiteta.nome} atualizado com sucesso!")
            return redirect('comissionamento:arquiteta_list')
    else:
        form = ArquitetaForm(instance=arquiteta)
    context = {'form': form, 'title': f'Editar Arquiteta: {arquiteta.nome}', 'arquiteta': arquiteta, 'edit_mode': True}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)

def arquiteta_delete(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    if arquiteta.contratort_set.exists():
        messages.error(request, f"Não é possível excluir {arquiteta.nome}. Existem contratos RT vinculados a ela.")
        return redirect('comissionamento:arquiteta_list')
    if request.method == 'POST':
        nome = arquiteta.nome
        arquiteta.delete()
        messages.success(request, f"Arquiteta {nome} excluída com sucesso.")
        return redirect('comissionamento:arquiteta_list')
    context = {'arquiteta': arquiteta, 'title': f'Confirmar Exclusão de Arquiteta: {arquiteta.nome}'}
    return render(request, 'core/comissionamento/arquiteta_delete.html', context)