import os

import requests
from django.conf import settings
from django.forms import modelformset_factory
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (DadosTrabalhistasForm, DocumentosFuncionarioForm,
                    EnderecoFuncionarioForm, FuncionarioForm)
from .models import (DadosTrabalhistas, DocumentosFuncionario,
                     EnderecoFuncionario, Funcionario)
from .services import \
    CadastroFuncionarioExcelService  # importe o service que criamos


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
    qs = Funcionario.objects.all()
    return render(request, 'core/funcionarios/list.html', {'funcionarios': qs})

def editar_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    try:
        endereco = funcionario.endereco #type: ignore
    except EnderecoFuncionario.DoesNotExist:
        endereco = EnderecoFuncionario(funcionario=funcionario)

    try:
        documentos = funcionario.documentos #type: ignore
    except DocumentosFuncionario.DoesNotExist:
        documentos = DocumentosFuncionario(funcionario=funcionario)

    try:
        dados_trabalhistas = funcionario.dados_trabalhistas #type: ignore
    except DadosTrabalhistas.DoesNotExist:
        dados_trabalhistas = DadosTrabalhistas(funcionario=funcionario)

    if request.method == 'POST':
        # Criando forms apenas para campos editáveis
        funcionario_form = FuncionarioForm(request.POST, instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(request.POST, instance=endereco)
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST, instance=dados_trabalhistas)
        # Se quiser permitir edição de documentos sensíveis, descomente:
        # documentos_form = DocumentosFuncionarioForm(request.POST, instance=documentos)

        if funcionario_form.is_valid() and endereco_form.is_valid() and dados_trabalhistas_form.is_valid():
            funcionario_form.save()
            endereco_form.save()
            dados_trabalhistas_form.save()
            # documentos_form.save()  # só se estiver editando documentos

            return redirect('funcionarios:funcionarios')
    else:
        funcionario_form = FuncionarioForm(instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(instance=endereco)
        dados_trabalhistas_form = DadosTrabalhistasForm(instance=dados_trabalhistas)
        # documentos_form = DocumentosFuncionarioForm(instance=documentos)

    return render(request, 'core/funcionarios/form.html', {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        # 'documentos_form': documentos_form,  # incluir se for editável
        'title': 'Editar Funcionário'
    })
def deletar_funcionario(request, pk):
    obj = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('funcionarios:funcionarios')
    return render(request, 'core/funcionarios/delete.html', {'object': obj})
"""
def editar_banco_dehoras(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    return render(request, '', {
        'banco_de_horas_form': ""
    })
"""
def gerar_excel_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)

    # Caminho temporário para salvar o arquivo
    caminho_temp = os.path.join(settings.MEDIA_ROOT, f'Funcionario_{funcionario.nome}.xlsx')

    # Gera o Excel
    CadastroFuncionarioExcelService.gerar_modelo(funcionario, caminho_arquivo=caminho_temp)

    # Retorna o arquivo para download
    if os.path.exists(caminho_temp):
        response = FileResponse(open(caminho_temp, 'rb'), as_attachment=True, filename=f'{funcionario.nome}.xlsx')
        return response
    return HttpResponse("Erro ao gerar o arquivo.", status=500)

def buscar_endereco_por_cep(request):
    cep = request.GET.get('cep', '').replace('-', '')
    if len(cep) != 8:
        return JsonResponse({'error': 'CEP inválido'}, status=400)

    url = f'https://viacep.com.br/ws/{cep}/json/'

    try:
        response = requests.get(url)
        data = response.json()
        if 'erro' in data:
            return JsonResponse({'error': 'CEP não encontrado'}, status=404)
        return JsonResponse({
            'endereco': data.get('logradouro', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'uf': data.get('uf', ''),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

