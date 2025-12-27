import os

import requests
from django.conf import settings
from django.db.models import Sum  # <--- Importante: Adicionar este import
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (DadosTrabalhistasForm, DocumentosFuncionarioForm,
                    EnderecoFuncionarioForm, FuncionarioForm)
from .models import (DadosTrabalhistas, DocumentosFuncionario,
                     EnderecoFuncionario, Funcionario)
from .services import CadastroFuncionarioExcelService

def criar_funcionario(request):
    if request.method == 'POST':
        funcionario_form = FuncionarioForm(request.POST)
        endereco_form = EnderecoFuncionarioForm(request.POST)
        documentos_form = DocumentosFuncionarioForm(request.POST)
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST)

        if funcionario_form.is_valid() and endereco_form.is_valid() and documentos_form.is_valid() and dados_trabalhistas_form.is_valid():
            funcionario = funcionario_form.save()
            
            endereco = endereco_form.save(commit=False)
            endereco.funcionario = funcionario
            endereco.save()

            documentos = documentos_form.save(commit=False)
            documentos.funcionario = funcionario
            documentos.save()

            dados_trabalhistas = dados_trabalhistas_form.save(commit=False)
            dados_trabalhistas.funcionario = funcionario
            dados_trabalhistas.save()

            return redirect('funcionarios:funcionarios')
    else:
        funcionario_form = FuncionarioForm()
        endereco_form = EnderecoFuncionarioForm()
        documentos_form = DocumentosFuncionarioForm()
        dados_trabalhistas_form = DadosTrabalhistasForm()

    return render(request, 'core/funcionarios/form.html', {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        'title': 'Criar Novo Funcionário'
    })

def lista_funcionarios(request):
    qs = Funcionario.objects.all().select_related('dados_trabalhistas', 'endereco')
    
    # Cálculos para os Cards
    total_funcionarios = qs.count()
    
    # Soma dos salários (trata caso não tenha ninguém ou salário nulo)
    total_folha = DadosTrabalhistas.objects.aggregate(
        soma=Sum('salario')
    )['soma'] or 0

    funcionario_form = FuncionarioForm()
    endereco_form = EnderecoFuncionarioForm()
    documentos_form = DocumentosFuncionarioForm()
    dados_trabalhistas_form = DadosTrabalhistasForm()

    return render(request, 'core/funcionarios/list.html', {
        'funcionarios': qs,
        'total_funcionarios': total_funcionarios,
        'total_folha': total_folha,
        # Passamos os forms para o template
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
    })

def editar_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    # Recupera ou cria instâncias relacionadas (igual ao seu código)
    try:
        endereco = funcionario.endereco
    except EnderecoFuncionario.DoesNotExist:
        endereco = EnderecoFuncionario(funcionario=funcionario)

    try:
        documentos = funcionario.documentos
    except DocumentosFuncionario.DoesNotExist:
        documentos = DocumentosFuncionario(funcionario=funcionario)

    try:
        dados_trabalhistas = funcionario.dados_trabalhistas
    except DadosTrabalhistas.DoesNotExist:
        dados_trabalhistas = DadosTrabalhistas(funcionario=funcionario)

    if request.method == 'POST':
        # Instancia forms com dados do POST
        funcionario_form = FuncionarioForm(request.POST, instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(request.POST, instance=endereco)
        documentos_form = DocumentosFuncionarioForm(request.POST, instance=documentos) # Adicionado
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST, instance=dados_trabalhistas)

        if funcionario_form.is_valid() and endereco_form.is_valid() and documentos_form.is_valid() and dados_trabalhistas_form.is_valid():
            funcionario_form.save()
            endereco_form.save()
            documentos_form.save() # Adicionado
            dados_trabalhistas_form.save()
            return redirect('funcionarios:funcionarios')
    else:
        # Instancia forms com dados do banco
        funcionario_form = FuncionarioForm(instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(instance=endereco)
        documentos_form = DocumentosFuncionarioForm(instance=documentos) # Adicionado
        dados_trabalhistas_form = DadosTrabalhistasForm(instance=dados_trabalhistas)

    context = {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form, # Adicionado
        'dados_trabalhistas_form': dados_trabalhistas_form,
        'title': 'Editar Funcionário'
    }

    # LÓGICA DO MODAL: Se for requisição AJAX, retorna apenas o modal parcial
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/funcionarios/form_modal.html', context)

    # Fallback para acesso direto via URL (opcional, ou pode manter form.html)
    return render(request, 'core/funcionarios/form.html', context)

def deletar_funcionario(request, pk):
    obj = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('funcionarios:funcionarios')
    
    # LÓGICA DO MODAL
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/funcionarios/delete_modal.html', {'object': obj})

    return render(request, 'core/funcionarios/delete.html', {'object': obj})


def gerar_excel_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    # Chama o serviço que agora retorna um buffer (BytesIO)
    arquivo_excel = CadastroFuncionarioExcelService.gerar_modelo(funcionario)
    
    if arquivo_excel:
        return FileResponse(
            arquivo_excel, 
            as_attachment=True, 
            filename=f'Funcionario_{funcionario.nome}.xlsx'
        )
    
    return HttpResponse("Erro ao gerar o arquivo Excel.", status=500)
def buscar_endereco_por_cep(request):
    cep = request.GET.get('cep', '').replace('-', '')
    
    if len(cep) != 8:
        return JsonResponse({'error': 'CEP inválido.'}, status=400)

    # 1. TENTATIVA PRINCIPAL: ViaCEP
    try:
        url_viacep = f'https://viacep.com.br/ws/{cep}/json/'
        # Headers ajudam a evitar bloqueios (erro 502/403)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        response = requests.get(url_viacep, headers=headers, timeout=3) # Timeout curto para não demorar a tentar o próximo
        
        if response.ok:
            data = response.json()
            if 'erro' not in data:
                return JsonResponse({
                    'endereco': data.get('logradouro', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('localidade', ''),
                    'uf': data.get('uf', ''),
                    'api_source': 'viacep' # Opcional: para debug
                })
                
    except (requests.RequestException, ValueError):
        # Falha silenciosa no ViaCEP para tentar o próximo
        pass

    # 2. TENTATIVA SECUNDÁRIA (Fallback): AwesomeAPI
    try:
        url_awesome = f'https://cep.awesomeapi.com.br/json/{cep}'
        response = requests.get(url_awesome, timeout=5)
        print("Awesome cep ativado")
        if response.ok:
            data = response.json()
            if 'code' not in data and 'address' in data:
                return JsonResponse({
                    # Mapeamento dos campos da AwesomeAPI para o seu padrão
                    'endereco': data.get('address', ''),
                    'bairro': data.get('district', ''),
                    'cidade': data.get('city', ''),
                    'uf': data.get('state', ''),
                    'api_source': 'awesomeapi'
                })

    except (requests.RequestException, ValueError):
        pass

    # 3. FALHA TOTAL: Mensagem para preenchimento manual
    return JsonResponse({
        'error': 'Não foi possível buscar o CEP automaticamente no momento. Por favor, preencha o endereço manualmente.'
    }, status=503)