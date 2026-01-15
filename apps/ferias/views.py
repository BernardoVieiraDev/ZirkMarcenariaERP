from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.funcionarios.models import Funcionario

# IMPORTANTE: Importe o form aqui, não defina a classe novamente
from .forms import \
    FeriasColetivasForm  # <--- Certifique-se que está importado aqui
from .forms import (FeriasForm, PagamentoFeriasForm, PeriodoAquisitivoForm,
                    RecibosContabilidadeForm)
from .models import (Ferias, Funcionario, PagamentoFerias,  # ...
                     PeriodoAquisitivo, RecibosContabilidade)
from .services import FeriasExcelService

# ... outros imports ...


def listar_funcionarios(request):
    funcionarios = (
        Funcionario.objects
        .select_related("banco_horas")
        .prefetch_related("periodos_aquisitivos__ferias_registradas")
        .order_by("nome")
    )

    # Instanciar forms vazios
    form_periodo = PeriodoAquisitivoForm()
    form_ferias = FeriasForm()
    
    # --- NOVO: Form para o Modal de Coletivas ---
    form_ferias_coletivas = FeriasColetivasForm()

    return render(request, "core/ferias/listar_funcionarios.html", {
        "funcionarios": funcionarios,
        "form_periodo": form_periodo,
        "form_ferias": form_ferias,
        "form_ferias_coletivas": form_ferias_coletivas, # Passando para o template
    })

def registrar_periodo(request):
    if request.method == 'POST':
        form = PeriodoAquisitivoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Período aquisitivo registrado com sucesso.")
            return redirect('ferias:listar_funcionarios')
    else:
        form = PeriodoAquisitivoForm()
    return render(request, 'core/ferias/registrar_periodo.html', {'form': form})

def editar_periodo(request, pk):
    periodo = get_object_or_404(PeriodoAquisitivo, pk=pk)
    if request.method == 'POST':
        form = PeriodoAquisitivoForm(request.POST, instance=periodo)
        if form.is_valid():
            form.save()
            messages.success(request, "Período atualizado.")
            return redirect('ferias:listar_funcionarios')
    else:
        form = PeriodoAquisitivoForm(instance=periodo)
    return render(request, 'core/ferias/registrar_periodo.html', {'form': form, 'editar': True})

@require_POST
def deletar_periodo(request, pk):
    periodo = get_object_or_404(PeriodoAquisitivo, pk=pk)
    periodo.delete()
    messages.success(request, "Período aquisitivo deletado.")
    return redirect('ferias:listar_funcionarios')


# Em zirk_rh_financeiro/apps/ferias/views.py

def registrar_ferias(request):
    if request.method == 'POST':
        form = FeriasForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Férias registradas com sucesso.")
                return redirect('ferias:listar_funcionarios')
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = FeriasForm()

    # --- CORREÇÃO: Se o formulário for inválido (ou for GET), recarrega o dashboard ---
    
    # Se houver erros, precisamos reconstruir o contexto da lista de funcionários
    if form.errors:
        funcionarios = (
            Funcionario.objects
            .select_related("banco_horas")
            .prefetch_related("periodos_aquisitivos__ferias_registradas")
            .order_by("nome")
        )
        # Cria o form de período vazio para não quebrar o outro modal
        form_periodo = PeriodoAquisitivoForm()
        
        return render(request, "core/ferias/listar_funcionarios.html", {
            "funcionarios": funcionarios,
            "form_periodo": form_periodo,
            "form_ferias": form,  # Passa o form COM ERROS
            "abrir_modal": "modalFerias" # Sinalizador para o template abrir o modal
        })

    # Caso seja um GET direto para essa URL (opcional, ou mantem o comportamento antigo)
    return render(request, 'core/ferias/registrar_ferias.html', {'form': form})

def editar_ferias(request, pk):
    registro = get_object_or_404(Ferias, pk=pk)
    
    if request.method == 'POST':
        form = FeriasForm(request.POST, instance=registro)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Registro de férias atualizado.")
                # Se for AJAX, o ideal seria retornar um JSON ou script para fechar o modal
                # Mas mantendo o padrão simples, o redirect funciona se o front lidar com isso
                return redirect('ferias:listar_funcionarios')
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = FeriasForm(instance=registro)
    
    # CORREÇÃO: Verifica se é uma requisição AJAX (comum em modais)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Retorna apenas o template do modal ou form parcial se houver erro
        # Certifique-se de ter um template parcial ou use o registrar_ferias.html sem o base se necessário
        # Assumindo que você tem um template base de modal ou reutiliza o registrar_ferias de forma parcial:
        return render(request, 'core/ferias/registrar_ferias.html', {
            'form': form, 
            'editar': True,
            'is_modal': True # Você pode usar essa flag no template para não carregar cabeçalho/rodapé
        })

    return render(request, 'core/ferias/registrar_ferias.html', {'form': form, 'editar': True})

@require_POST
def deletar_ferias(request, pk):
    registro = get_object_or_404(Ferias, pk=pk)
    registro.delete()
    messages.success(request, "Registro de férias deletado.")
    return redirect('ferias:listar_funcionarios')

def listar_pagamentos(request):
    pagamentos = (
        PagamentoFerias.objects
        .select_related("funcionario")
        .order_by("-vencimento")
    )
    
    # --- NOVO: Formulário vazio para o Modal ---
    form_pagamento = PagamentoFeriasForm()

    return render(request, "core/ferias/listar_pagamentos.html", {
        "pagamentos": pagamentos,
        "form_pagamento": form_pagamento
    })
def registrar_pagamento(request):
    if request.method == 'POST':
        form = PagamentoFeriasForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pagamento de 1/3 de férias registrado com sucesso!")
            return redirect('ferias:listar_pagamentos')
    else:
        form = PagamentoFeriasForm()
    return render(request, 'core/ferias/registrar_pagamento.html', {'form': form})


def calcular_saldo_total(funcionario):
    saldo_total = 0
    for periodo in funcionario.periodos_aquisitivos.all():
        saldo_total += periodo.saldo_restante  # ou outra lógica que você use para saldo
    return saldo_total

def editar_pagamento(request, pk):
    pagamento = get_object_or_404(PagamentoFerias, pk=pk)
    form = PagamentoFeriasForm(request.POST or None, instance=pagamento)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('ferias:listar_pagamentos')
    
    # Se a requisição for AJAX (vinda do modal), renderiza apenas o partial
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/ferias/form_modal.html', {
            'form': form,
            'object': pagamento
        })

    # Fallback caso alguém acesse a URL diretamente pelo navegador (opcional)
    return render(request, 'core/ferias/form_modal.html', {'form': form})

def deletar_pagamento(request, pk):
    pagamento = get_object_or_404(PagamentoFerias, pk=pk)

    if request.method == 'POST':
        pagamento.delete()
        return redirect('ferias:listar_pagamentos')

    # Se a requisição for AJAX, retorna o modal de confirmação
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/ferias/delete_modal.html', {
            'object': pagamento
        })
        
    return redirect('ferias:listar_pagamentos')


def exportar_planilha_geral(request):
    """
    Gera o relatório GERAL com todas as seções (Férias, Pgto, Recibos, Banco Horas).
    """
    ano_atual = date.today().year
    # Se quiser permitir o usuário escolher o ano via URL ?ano=2024
    ano_param = request.GET.get('ano')
    ano = int(ano_param) if ano_param else ano_atual
    
    excel_file = FeriasExcelService.gerar_relatorio_geral(ano)
    
    filename = f"Relatorio_Geral_RH_{ano}.xlsx"
    response = HttpResponse(
        excel_file.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response



def listar_recibos(request):
    recibos = (
        RecibosContabilidade.objects
        .select_related("funcionario")
        .order_by("-recibo_de_ferias_contabilidade")
    )
    
    # Formulário vazio para o Modal de criação
    form_recibo = RecibosContabilidadeForm()

    return render(request, "core/ferias/listar_recibos.html", {
        "recibos": recibos,
        "form_recibo": form_recibo
    })

def registrar_recibo(request):
    if request.method == 'POST':
        form = RecibosContabilidadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Recibo contábil registrado com sucesso!")
            return redirect('ferias:listar_recibos')
    else:
        form = RecibosContabilidadeForm()
    return render(request, 'core/ferias/registrar_recibo.html', {'form': form}) # Fallback se não usar modal


def editar_recibo(request, pk):
    recibo = get_object_or_404(RecibosContabilidade, pk=pk)
    
    # ADICIONADO: auto_id="id_edit_%s" para evitar conflito de IDs com o modal de criação
    form = RecibosContabilidadeForm(
        request.POST or None, 
        instance=recibo, 
        auto_id="id_edit_%s"
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Recibo atualizado.")
            return redirect('ferias:listar_recibos')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/ferias/form_modal_recibo.html', {
            'form': form,
            'object': recibo,
            'action_url': request.path 
        })
    
    return redirect('ferias:listar_recibos')

def deletar_recibo(request, pk):
    recibo = get_object_or_404(RecibosContabilidade, pk=pk)

    # Se for POST, executa a exclusão
    if request.method == 'POST':
        recibo.delete()
        messages.success(request, "Recibo deletado.")
        return redirect('ferias:listar_recibos')

    # Se for GET (AJAX), retorna o modal de confirmação
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/ferias/delete_modal.html', {
            'object': recibo,
            # O template delete_modal usa request.path no action, o que funcionará corretamente
        })
    
    # Fallback
    return redirect('ferias:listar_recibos')
# View auxiliar para o modal de exclusão (opcional, igual ao padrão que você já usa)
def confirmar_delete_recibo(request, pk):
    recibo = get_object_or_404(RecibosContabilidade, pk=pk)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/ferias/delete_modal.html', {
            'object': recibo,
            'delete_url': reverse('ferias:deletar_recibo', kwargs={'pk': pk})
        })
    return redirect('ferias:listar_recibos')

def calcular_valor_ferias_api(request):
    """
    API para calcular automaticamente 1/3 de férias com base no salário.
    Recebe: funcionario_id (GET)
    Retorna: JSON {'valor': '1234.56'}
    """
    funcionario_id = request.GET.get('funcionario_id')
    
    if not funcionario_id:
        return JsonResponse({'valor': None})

    try:
        funcionario = Funcionario.objects.get(pk=funcionario_id)
        # Tenta pegar salário da Marcenaria ou Contabilidade
        if hasattr(funcionario, 'dados_trabalhistas'):
            salario = funcionario.dados_trabalhistas.salario
            if salario:
                # Cálculo de 1/3
                valor = salario / Decimal("3.0")
                valor_formatado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                return JsonResponse({'valor': str(valor_formatado)})
    
    except Funcionario.DoesNotExist:
        pass
    
    return JsonResponse({'valor': 0})



def registrar_ferias_coletivas(request):
    if request.method == 'POST':
        form = FeriasColetivasForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            funcionarios = data['funcionarios']
            data_inicio = data['data_inicio']
            data_fim = data['data_fim']
            observacao = data['observacao_geral']
            
            # 1. Capturar os valores do formulário
            dias_recesso = data['ferias_no_recesso_final_ano']
            dias_carnaval = data['ferias_no_carnaval']
            
            # Calcula total de dias
            dias_totais = (data_fim - data_inicio).days + 1

            for func in funcionarios:
                # CORREÇÃO AQUI:
                # 1. Buscamos todos os períodos do funcionário ordenados pelo mais antigo
                periodos = PeriodoAquisitivo.objects.filter(funcionario=func).order_by('data_inicio')
                
                periodo_encontrado = None
                
                # 2. Iteramos no Python para achar o primeiro com saldo positivo
                # Como 'saldo_restante' é calculado no Python, precisamos fazer assim:
                for p in periodos:
                    if p.saldo_restante() > 0:
                        periodo_encontrado = p
                        break
                
                if periodo_encontrado:
                    Ferias.objects.create(
                        periodo=periodo_encontrado,
                        dias_tirados=dias_totais,
                        observacoes=observacao,
                        ferias_no_recesso_final_ano=dias_recesso,
                        ferias_no_carnaval=dias_carnaval
                    )
                else:
                    # Opcional: Adicionar aviso se algum funcionário não tiver período com saldo
                    # messages.warning(request, f"Funcionário {func.nome} não possui saldo suficiente.")
                    pass
            
            messages.success(request, "Férias coletivas registradas com sucesso!")
            return redirect('ferias:listar_funcionarios')
    else:
        form = FeriasColetivasForm()

    # Se der erro no form, reabre o modal na listagem
    return listar_funcionarios_com_erro_coletivas(request, form)

# Helper necessário para reabrir o modal com erro
def listar_funcionarios_com_erro_coletivas(request, form_coletivas_com_erro):
    funcionarios = Funcionario.objects.select_related("banco_horas").prefetch_related("periodos_aquisitivos__ferias_registradas").order_by("nome")
    return render(request, "core/ferias/listar_funcionarios.html", {
        "funcionarios": funcionarios,
        "form_periodo": PeriodoAquisitivoForm(),
        "form_ferias": FeriasForm(),
        "form_ferias_coletivas": form_coletivas_com_erro,
        "abrir_modal": "modalColetivas"
    })