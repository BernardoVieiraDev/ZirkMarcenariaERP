from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse  # Adicionar nos imports
from django.shortcuts import redirect, render

from .forms import LancamentoSocioForm, SocioForm  # <--- Importe o novo form
from .models import CategoriaSocio, LancamentoSocio, Socio
from .services import SocioExcelService 


def registrar_despesa(request):
    if request.method == 'POST':
        form = LancamentoSocioForm(request.POST)
        if form.is_valid():
            form.save()
            # MUDAR O REDIRECT PARA O EXTRATO
            return redirect('socios:listar_lancamentos') 
    else:
        form = LancamentoSocioForm()
    
    return render(request, 'core/socios/registrar_despesa.html', {'form': form})
def relatorio_anual(request):
    # 1. Filtros
    ano_selecionado = request.GET.get('ano', datetime.now().year)
    socio_id_param = request.GET.get('socio') # Pega o ID da URL (?socio=1)
    
    try:
        ano = int(ano_selecionado)
    except ValueError:
        ano = datetime.now().year

    # Converter socio_id para int se existir
    socio_id = None
    if socio_id_param and socio_id_param != '':
        try:
            socio_id = int(socio_id_param)
        except ValueError:
            pass

    # 2. Dados para o Template
    socios = Socio.objects.all() # Lista para o Dropdown
    categorias = CategoriaSocio.objects.all()
    relatorio = {}
    
    # 3. Construção da Matriz
    for cat in categorias:
        grupo_label = cat.get_grupo_display()
        if grupo_label not in relatorio:
            relatorio[grupo_label] = []
        
        valores_meses = []
        total_cat = 0
        
        for mes in range(1, 13):
            # Query base
            qs = LancamentoSocio.objects.filter(
                categoria=cat, 
                data__year=ano, 
                data__month=mes
            )
            
            # FILTRO DE SÓCIO AQUI NA TELA
            if socio_id:
                qs = qs.filter(socio_id=socio_id)
            
            soma = qs.aggregate(Sum('valor'))['valor__sum'] or 0
            
            valores_meses.append(soma)
            total_cat += soma
            
        relatorio[grupo_label].append({
            'nome': cat.nome,
            'valores': valores_meses,
            'total': total_cat
        })

    context = {
        'relatorio': relatorio,
        'ano': ano,
        'meses': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
        'socios': socios,       # Lista completa
        'socio_atual': socio_id # ID selecionado para manter o select marcado
    }
    return render(request, 'core/socios/relatorio_anual.html', context)

def exportar_relatorio(request):
    """
    Gera o download da planilha Excel considerando Ano e Sócio.
    """
    # 1. Pega Ano
    ano_param = request.GET.get('ano')
    try:
        ano = int(ano_param) if ano_param else datetime.now().year
    except ValueError:
        ano = datetime.now().year
        
    # 2. Pega Sócio
    socio_param = request.GET.get('socio')
    socio_id = None
    nome_arquivo_extra = "Geral"
    
    if socio_param:
        try:
            socio_id = int(socio_param)
            socio_obj = Socio.objects.get(id=socio_id)
            nome_arquivo_extra = socio_obj.nome.replace(" ", "_")
        except (ValueError, Socio.DoesNotExist):
            pass
    
    # 3. Gera planilha passando o ID
    buffer = SocioExcelService.gerar_planilha_anual(ano, socio_id)
    
    # 4. Download
    filename = f"Relatorio_Socios_{nome_arquivo_extra}_{ano}.xlsx"
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response

def cadastrar_socio(request):
    if request.method == 'POST':
        form = SocioForm(request.POST)
        if form.is_valid():
            form.save()
            # Após criar o sócio, manda o usuário direto para registrar uma despesa
            return redirect('socios:registrar_despesa')
    else:
        form = SocioForm()
    
    return render(request, 'core/socios/cadastrar_socio.html', {'form': form})

def listar_lancamentos(request):
    """
    Lista detalhada de todas as despesas/receitas lançadas, ordenadas pela mais recente.
    """
    lancamentos = LancamentoSocio.objects.select_related('categoria', 'socio').order_by('-data')
    context = {
        'lancamentos': lancamentos
    }
    return render(request, 'core/socios/lista_lancamentos.html', context)


def editar_lancamento(request, pk):
    lancamento = get_object_or_404(LancamentoSocio, pk=pk)
    
    if request.method == 'POST':
        form = LancamentoSocioForm(request.POST, instance=lancamento)
        if form.is_valid():
            form.save()
            # Volta para o extrato após editar
            return redirect('socios:listar_lancamentos')
    else:
        # Abre o formulário preenchido com os dados atuais
        form = LancamentoSocioForm(instance=lancamento)
    
    return render(request, 'core/socios/registrar_despesa.html', {
        'form': form, 
        'titulo': 'Editar Lançamento' # Passamos um título para saber que é edição
    })

def excluir_lancamento(request, pk):
    lancamento = get_object_or_404(LancamentoSocio, pk=pk)
    
    if request.method == 'POST':
        lancamento.delete()
        return redirect('socios:listar_lancamentos')
    
    # Renderiza uma telinha simples de confirmação
    return render(request, 'core/socios/confirmar_exclusao.html', {'item': lancamento})