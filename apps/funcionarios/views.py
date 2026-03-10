import logging
import os

from django.contrib import messages

logger = logging.getLogger(__name__)
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum  # <--- Importante: Adicionar este import
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (DadosTrabalhistasForm, DocumentosFuncionarioForm,
                    EnderecoFuncionarioForm, FuncionarioForm, BeneficioFormSet)
from .models import (DadosTrabalhistas, DocumentosFuncionario,
                     EnderecoFuncionario, Funcionario)
from .services import CadastroFuncionarioExcelService


def _get_dashboard_context():
    """Retorna o contexto padrão da lista de funcionários"""
    qs = Funcionario.objects.all().select_related('dados_trabalhistas', 'endereco')
    total_funcionarios = qs.count()
    total_folha = DadosTrabalhistas.objects.aggregate(soma=Sum('salario'))['soma'] or 0
    return {
        'funcionarios': qs,
        'total_funcionarios': total_funcionarios,
        'total_folha': total_folha,
    }

@login_required
def criar_funcionario(request):
    # GET: Redireciona para a lista (onde o modal de criação vive)
    if request.method != 'POST':
        return redirect('funcionarios:funcionarios')

    # POST: Processa o formulário
    funcionario_form = FuncionarioForm(request.POST)
    endereco_form = EnderecoFuncionarioForm(request.POST)
    documentos_form = DocumentosFuncionarioForm(request.POST)
    dados_trabalhistas_form = DadosTrabalhistasForm(request.POST)
    beneficios_formset = BeneficioFormSet(request.POST)

    # Adicionado a validação do beneficios_formset
    if (funcionario_form.is_valid() and endereco_form.is_valid() and 
        documentos_form.is_valid() and dados_trabalhistas_form.is_valid() and 
        beneficios_formset.is_valid()):
        
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

        # Salva os benefícios atrelando ao funcionário recém-criado
        beneficios_formset.instance = funcionario
        beneficios_formset.save()

        return redirect('funcionarios:funcionarios')
    
    else:
        def adicionar_erros(form, nome_aba):
            for field, errors in form.errors.items():
                for error in errors:
                    # Exibe: "Dados Trabalhistas (insalubridade): Certifique-se de que..."
                    messages.error(request, f"Erro em {nome_aba} ({field}): {error}")

        # Verifica cada form e adiciona os erros específicos
        if not funcionario_form.is_valid():
            adicionar_erros(funcionario_form, "Dados Pessoais")
            
        if not endereco_form.is_valid():
            adicionar_erros(endereco_form, "Endereço")
            
        if not documentos_form.is_valid():
            adicionar_erros(documentos_form, "Documentos")
            
        if not dados_trabalhistas_form.is_valid():
            adicionar_erros(dados_trabalhistas_form, "Dados Trabalhistas")
            
        if not beneficios_formset.is_valid():
            messages.error(request, "Erro em Benefícios: Verifique os dados inseridos nas linhas de benefícios.")
        
        print("\n\n❌ ERRO DE VALIDAÇÃO AO CRIAR FUNCIONÁRIO:")
        if not funcionario_form.is_valid():
            print(f"Erro Dados Pessoais: {funcionario_form.errors.as_json()}")
        if not endereco_form.is_valid():
            print(f"Erro Endereço: {endereco_form.errors.as_json()}")
        if not documentos_form.is_valid():
            print(f"Erro Documentos: {documentos_form.errors.as_json()}")
        if not dados_trabalhistas_form.is_valid():
            print(f"Erro Trabalhistas: {dados_trabalhistas_form.errors.as_json()}")
        if not beneficios_formset.is_valid():
            print(f"Erro Beneficios: {beneficios_formset.errors}")
        print("=================================================================\n")

    # ERRO: Renderiza a lista novamente, mas com os forms preenchidos e flag para abrir modal
    context = _get_dashboard_context()
    context.update({
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        'beneficios_formset': beneficios_formset, # Passa o formset para o context de erro
        'abrir_modal': 'modalFuncionario' # Flag para seu template abrir o modal via JS se necessário
    })
    return render(request, 'core/funcionarios/list.html', context)

@login_required
def lista_funcionarios(request):
    context = _get_dashboard_context()
    # Adiciona forms vazios para o modal de criação
    context.update({
        'funcionario_form': FuncionarioForm(),
        'endereco_form': EnderecoFuncionarioForm(),
        'documentos_form': DocumentosFuncionarioForm(),
        'dados_trabalhistas_form': DadosTrabalhistasForm(),
        'beneficios_formset': BeneficioFormSet(), # Formset vazio para criação
    })
    return render(request, 'core/funcionarios/list.html', context)

@login_required
def editar_funcionario(request, pk):
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    # Recupera instâncias (mesma lógica anterior)
    try: endereco = funcionario.endereco
    except EnderecoFuncionario.DoesNotExist: endereco = EnderecoFuncionario(funcionario=funcionario)

    try: documentos = funcionario.documentos
    except DocumentosFuncionario.DoesNotExist: documentos = DocumentosFuncionario(funcionario=funcionario)

    try: dados_trabalhistas = funcionario.dados_trabalhistas
    except DadosTrabalhistas.DoesNotExist: dados_trabalhistas = DadosTrabalhistas(funcionario=funcionario)

    if request.method == 'POST':
        funcionario_form = FuncionarioForm(request.POST, instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(request.POST, instance=endereco)
        documentos_form = DocumentosFuncionarioForm(request.POST, instance=documentos)
        dados_trabalhistas_form = DadosTrabalhistasForm(request.POST, instance=dados_trabalhistas)
        beneficios_formset = BeneficioFormSet(request.POST, instance=funcionario) # Passa request.POST e a instância

        if (funcionario_form.is_valid() and endereco_form.is_valid() and 
            documentos_form.is_valid() and dados_trabalhistas_form.is_valid() and 
            beneficios_formset.is_valid()):
            
            funcionario_form.save()
            endereco_form.save()
            documentos_form.save()
            dados_trabalhistas_form.save()
            beneficios_formset.save() # Salva as edições, adições ou deleções do formset
            
            return redirect('funcionarios:funcionarios')
    else:
        funcionario_form = FuncionarioForm(instance=funcionario)
        endereco_form = EnderecoFuncionarioForm(instance=endereco)
        documentos_form = DocumentosFuncionarioForm(instance=documentos)
        dados_trabalhistas_form = DadosTrabalhistasForm(instance=dados_trabalhistas)
        beneficios_formset = BeneficioFormSet(instance=funcionario) # Carrega os benefícios do funcionário

    context = {
        'funcionario_form': funcionario_form,
        'endereco_form': endereco_form,
        'documentos_form': documentos_form,
        'dados_trabalhistas_form': dados_trabalhistas_form,
        'beneficios_formset': beneficios_formset, # Passando para o form_modal.html
        'title': 'Editar Funcionário'
    }

    # SÓ RETORNA SE FOR AJAX (Modal)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/funcionarios/form_modal.html', context)

    # Fallback: Redireciona para lista se tentar acessar direto via URL
    return redirect('funcionarios:funcionarios')

@login_required
def deletar_funcionario(request, pk):
    obj = get_object_or_404(Funcionario, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('funcionarios:funcionarios')
    
    # SÓ RETORNA SE FOR AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/funcionarios/delete_modal.html', {'object': obj})

    # Fallback
    return redirect('funcionarios:funcionarios')

@login_required
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

@login_required
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