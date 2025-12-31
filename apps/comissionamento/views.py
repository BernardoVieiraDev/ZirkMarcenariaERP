from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
from .models import Arquiteta, ContratoRT
from .forms import ArquitetaForm, ContratoRTForm
from decimal import Decimal

# --- VIEWS DE CONTRATOS (Agora Unificadas) ---

# Em apps/comissionamento/views.py

def rt_contratos_list(request):
    # ... código existente da query de contratos ...
    contratos = ContratoRT.objects.select_related('arquiteta').order_by('-data_contrato')
    
    # ADICIONE ISSO:
    todas_arquitetas = Arquiteta.objects.all().order_by('nome')

    # ... cálculos de totais existentes ...
    total_rt = contratos.aggregate(sum_rt=Sum('valor_rt'))['sum_rt'] or Decimal('0.00')
    total_pago = contratos.aggregate(sum_pago=Sum('valor_pago'))['sum_pago'] or Decimal('0.00')

    context = {
        'contratos': contratos,
        'arquitetas': todas_arquitetas, # Passando para o template
        'total_rt': total_rt,
        'total_pago': total_pago,
        'title': 'Gestão de Contratos de RT',
    }
    return render(request, 'core/comissionamento/contratos_list.html', context)

def rt_contrato_create(request):
    if request.method == 'POST':
        form = ContratoRTForm(request.POST)
        if form.is_valid():
            contrato = form.save()
            messages.success(request, f"Contrato RT para {contrato.cliente} salvo com sucesso!")
            return redirect('comissionamento:contratos_list') 
    else:
        form = ContratoRTForm()
        
    context = {'form': form, 'title': 'Novo Contrato de RT'}
    return render(request, 'core/comissionamento/contrato_form.html', context)

def rt_contrato_edit(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    if request.method == 'POST':
        form = ContratoRTForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            messages.success(request, f"Contrato de {contrato.cliente} atualizado com sucesso!")
            return redirect('comissionamento:contratos_list')
    else:
        form = ContratoRTForm(instance=contrato)
        
    context = {
        'form': form,
        'title': f'Editar Contrato RT: {contrato.cliente}',
        'edit_mode': True
    }
    return render(request, 'core/comissionamento/contrato_form.html', context)

def rt_contrato_delete(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    if request.method == 'POST':
        nome = contrato.cliente
        contrato.delete()
        messages.success(request, f"Registro de {nome} excluído com sucesso.")
        return redirect('comissionamento:contratos_list')
        
    context = {
        'contrato': contrato,
        'title': f'Excluir Registro: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_delete.html', context)

# --- VIEWS DE ARQUITETA (Sem alterações lógicas) ---
def arquiteta_list(request):
    arquitetas = Arquiteta.objects.all().order_by('nome')
    context = {'arquitetas': arquitetas, 'title': 'Cadastro de Arquitetas'}
    return render(request, 'core/comissionamento/arquiteta_list.html', context)

def arquiteta_create(request):
    if request.method == 'POST':
        form = ArquitetaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Arquiteta cadastrada com sucesso.")
            return redirect('comissionamento:arquiteta_list') 
    else:
        form = ArquitetaForm()
    context = {'form': form, 'title': 'Nova Arquiteta'}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)

def arquiteta_edit(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    if request.method == 'POST':
        form = ArquitetaForm(request.POST, instance=arquiteta)
        if form.is_valid():
            form.save()
            messages.success(request, "Arquiteta atualizada com sucesso.")
            return redirect('comissionamento:arquiteta_list')
    else:
        form = ArquitetaForm(instance=arquiteta)
    context = {'form': form, 'title': f'Editar: {arquiteta.nome}', 'edit_mode': True}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)

def arquiteta_delete(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    # Verifica dependência com o novo modelo ContratoRT
    if arquiteta.contratort_set.exists():
        messages.error(request, "Não é possível excluir: existem registros vinculados a esta arquiteta.")
        return redirect('comissionamento:arquiteta_list')
        
    if request.method == 'POST':
        arquiteta.delete()
        messages.success(request, "Arquiteta excluída com sucesso.")
        return redirect('comissionamento:arquiteta_list')
    context = {'arquiteta': arquiteta, 'title': f'Excluir Arquiteta: {arquiteta.nome}'}
    return render(request, 'core/comissionamento/arquiteta_delete.html', context)