# zirk_rh_financeiro/apps/clientes/views.py

import requests
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

# Imports locais corretos
from apps.comissionamento.models import ContratoRT
from apps.financeiro.receber.models import Receber
from .forms import ClienteForm, EnderecoClienteForm
from .models import Cliente, EnderecoCliente


def buscar_endereco_por_cep(request):
    cep = request.GET.get('cep', '').replace('-', '').replace('.', '').strip()
    
    if len(cep) != 8:
        return JsonResponse({'error': 'CEP inválido.'}, status=400)

    # 1. ViaCEP
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(f'https://viacep.com.br/ws/{cep}/json/', headers=headers, timeout=3)
        if response.ok:
            data = response.json()
            if 'erro' not in data:
                return JsonResponse({
                    'endereco': data.get('logradouro', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('localidade', ''),
                    'uf': data.get('uf', '')
                })
    except (requests.RequestException, ValueError):
        pass

    # 2. AwesomeAPI (Fallback)
    try:
        response = requests.get(f'https://cep.awesomeapi.com.br/json/{cep}', timeout=5)
        if response.ok:
            data = response.json()
            if 'code' not in data and 'address' in data:
                return JsonResponse({
                    'endereco': data.get('address', ''),
                    'bairro': data.get('district', ''),
                    'cidade': data.get('city', ''),
                    'uf': data.get('state', '')
                })
    except (requests.RequestException, ValueError):
        pass

    return JsonResponse({'error': 'CEP não encontrado.'}, status=404)


def lista_clientes(request):
    qs = Cliente.objects.all()
    
    term = request.GET.get('q')
    if term:
        qs = qs.filter(Q(nome_completo__icontains=term) | Q(cpf__icontains=term))

    context = {
        'clientes': qs,
        'total_clientes': qs.count(),
    }
    return render(request, 'core/clientes/list.html', context)


def criar_cliente(request):
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST)
        end_residencial_form = EnderecoClienteForm(request.POST, prefix='residencial')
        end_obra_form = EnderecoClienteForm(request.POST, prefix='obra')

        # Verifica se tem dados de obra preenchidos
        tem_dados_obra = any(v for k, v in request.POST.items() if k.startswith('obra-') and v.strip())

        is_valid = cliente_form.is_valid() and end_residencial_form.is_valid()
        
        if tem_dados_obra:
            if not end_obra_form.is_valid():
                is_valid = False

        if is_valid:
            cliente = cliente_form.save()

            # Salva Residencial
            res = end_residencial_form.save(commit=False)
            res.cliente = cliente
            res.tipo = 'RESIDENCIAL'
            res.save()

            # Salva Obra se houver dados
            if tem_dados_obra:
                obra = end_obra_form.save(commit=False)
                obra.cliente = cliente
                obra.tipo = 'OBRA'
                obra.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
            return redirect('clientes:list')
            
    else:
        cliente_form = ClienteForm()
        end_residencial_form = EnderecoClienteForm(prefix='residencial')
        end_obra_form = EnderecoClienteForm(prefix='obra')

    context = {
        'cliente_form': cliente_form,
        'end_residencial_form': end_residencial_form,
        'end_obra_form': end_obra_form,
        'is_editing': False
    }

    return render(request, 'core/clientes/form_modal.html', context)


def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    
    end_residencial = cliente.enderecos.filter(tipo='RESIDENCIAL').first()
    end_obra = cliente.enderecos.filter(tipo='OBRA').first()

    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST, instance=cliente)
        end_residencial_form = EnderecoClienteForm(request.POST, instance=end_residencial, prefix='residencial')
        end_obra_form = EnderecoClienteForm(request.POST, instance=end_obra, prefix='obra')

        tem_dados_obra = any(v for k, v in request.POST.items() if k.startswith('obra-') and v.strip())

        is_valid = cliente_form.is_valid() and end_residencial_form.is_valid()

        if tem_dados_obra:
            if not end_obra_form.is_valid():
                is_valid = False

        if is_valid:
            cliente_form.save()

            res = end_residencial_form.save(commit=False)
            res.cliente = cliente
            res.tipo = 'RESIDENCIAL'
            res.save()

            if tem_dados_obra:
                obra = end_obra_form.save(commit=False)
                obra.cliente = cliente
                obra.tipo = 'OBRA'
                obra.save()
            elif end_obra:
                end_obra.delete()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            return redirect('clientes:list')
    else:
        cliente_form = ClienteForm(instance=cliente)
        end_residencial_form = EnderecoClienteForm(instance=end_residencial, prefix='residencial')
        end_obra_form = EnderecoClienteForm(instance=end_obra, prefix='obra')

    context = {
        'cliente_form': cliente_form,
        'end_residencial_form': end_residencial_form,
        'end_obra_form': end_obra_form,
        'is_editing': True,
        'object': cliente
    }

    return render(request, 'core/clientes/form_modal.html', context)

from django.http import JsonResponse

def deletar_cliente(request, pk):
    obj = get_object_or_404(Cliente, pk=pk)

    # POST → exclusão
    if request.method == 'POST':
        obj.delete()

        # Se for AJAX, retorna JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        # Fallback para POST normal
        return redirect('clientes:list')

    # GET → carrega o modal
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(
            request,
            'core/clientes/delete_modal.html',
            {'object': obj}
        )

    return redirect('clientes:list')


def detalhe_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    contratos = ContratoRT.objects.filter(cliente=cliente).select_related('arquiteta').order_by('-data_contrato')
    financeiro = Receber.objects.filter(contrato_rt__cliente=cliente).order_by('data_vencimento')
    
    context = {
        'cliente': cliente,
        'contratos': contratos,
        'financeiro': financeiro,
    }
    return render(request, 'core/clientes/detail.html', context)