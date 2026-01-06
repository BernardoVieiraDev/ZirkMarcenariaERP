from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse
from apps.funcionarios.models import Funcionario
from django.http import JsonResponse
from decimal import Decimal, ROUND_HALF_UP
from .forms import FeriasForm, RecibosContabilidadeForm, PagamentoFeriasForm, PeriodoAquisitivoForm
from .models import Ferias, RecibosContabilidade, PagamentoFerias, PeriodoAquisitivo
from .services import FeriasExcelService


def listar_funcionarios(request):
    funcionarios = (
        Funcionario.objects
        .select_related("banco_horas")
        .prefetch_related(
            "periodos_aquisitivos__ferias_registradas"
        )
        .order_by("nome")
    )

    # --- NOVO: Instanciar forms vazios para os Modais ---
    form_periodo = PeriodoAquisitivoForm()
    form_ferias = FeriasForm()

    return render(request, "core/ferias/listar_funcionarios.html", {
        "funcionarios": funcionarios,
        "form_periodo": form_periodo,
        "form_ferias": form_ferias
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
                return redirect('ferias:listar_funcionarios')
            except ValueError as e:
                form.add_error(None, str(e))
    else:
        form = FeriasForm(instance=registro)
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