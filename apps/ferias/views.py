from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.funcionarios.models import Funcionario

from .forms import FeriasForm, PagamentoFeriasForm, PeriodoAquisitivoForm
from .models import Ferias, PagamentoFerias, PeriodoAquisitivo
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