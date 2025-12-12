from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.db.models import Sum
from .models import Arquiteta, ContratoRT, PagamentoRT
from decimal import Decimal
from .forms import ArquitetaForm, ContratoRTForm

# Certifique-se de que o Django tem uma URL para o 'arquiteta_detail' (ex: name='arquiteta_detail')

def rt_contratos_list(request):
    """
    Lista unificada de todos os Contratos RT ativos.
    (Substitui a aba 'RTs POR CLIENTE')
    """
    # Exemplo: Lista contratos ordenados por arquiteta
    contratos = ContratoRT.objects.select_related('arquiteta').order_by('arquiteta__nome', '-data_contrato')
    
    # Agregação global (Exemplo: Total Geral da Dívida RT)
    total_rt_devida = contratos.aggregate(sum_rt=Sum('saldo_devedor'))['sum_rt'] or Decimal('0.00')
    
    context = {
        'contratos': contratos,
        'total_rt_devida': total_rt_devida,
        'title': 'Gestão de Contratos de Remuneração Técnica (RT)'
    }
    return render(request, 'core/comissionamento/contratos_list.html', context)

def rt_contrato_detail(request, pk):
    """
    Detalhe de um Contrato RT específico e lista de todos os pagamentos realizados.
    (Substitui a aba 'RT (2)')
    """
    contrato = get_object_or_404(ContratoRT, pk=pk)
    pagamentos = PagamentoRT.objects.filter(contrato=contrato).order_by('-data_pagamento')
    
    # Calcula o total pago e o saldo devedor (redundante, mas útil para confirmar)
    total_pago = pagamentos.aggregate(sum_pgto=Sum('valor_pago'))['sum_pgto'] or Decimal('0.00')
    
    context = {
        'contrato': contrato,
        'pagamentos': pagamentos,
        'total_pago': total_pago,
        'title': f'Detalhe RT: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_detail.html', context)

def rt_pagamento_create(request, contrato_pk):
    """
    View para registrar um novo pagamento de RT.
    """
    contrato = get_object_or_404(ContratoRT, pk=contrato_pk)
    
    # Criamos um formulário simples para o PagamentoRT
    from django import forms
    class PagamentoRTForm(forms.ModelForm):
        class Meta:
            model = PagamentoRT
            fields = ['data_pagamento', 'valor_pago', 'observacoes']
            widgets = {
                'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            }
            
    if request.method == 'POST':
        form = PagamentoRTForm(request.POST)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.contrato = contrato
            pagamento.save()
            # O signal recalcula o saldo automaticamente aqui
            return redirect('comissionamento:contrato_detail', pk=contrato.pk)
    else:
        form = PagamentoRTForm()
        
    context = {
        'form': form,
        'contrato': contrato,
        'title': f'Registrar Pagamento para {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/pagamento_form.html', context)

def arquiteta_create(request):
    """
    View para adicionar um novo registro de Arquiteta.
    """
    if request.method == 'POST':
        form = ArquitetaForm(request.POST)
        if form.is_valid():
            form.save()
            # Redireciona para a lista de contratos após o sucesso
            return redirect('comissionamento:contratos_list') 
    else:
        form = ArquitetaForm()
        
    context = {
        'form': form,
        'title': 'Cadastrar Nova Arquiteta',
    }
    return render(request, 'core/comissionamento/arquiteta_form.html', context)


def rt_contrato_create(request):
    """
    View para criar um novo Contrato RT, associando-o a uma Arquiteta existente.
    """
    if request.method == 'POST':
        form = ContratoRTForm(request.POST)
        if form.is_valid():
            contrato = form.save()
            # Salva o contrato e redireciona para a lista geral
            return redirect('comissionamento:contratos_list') 
    else:
        form = ContratoRTForm()
        
    context = {
        'form': form,
        'title': 'Cadastrar Novo Contrato de RT',
    }
    return render(request, 'core/comissionamento/contrato_form.html', context)