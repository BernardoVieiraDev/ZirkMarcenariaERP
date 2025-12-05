from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.funcionarios.models import Funcionario

from .forms import FeriasForm, PagamentoFeriasForm, PeriodoAquisitivoForm
from .models import Ferias, PagamentoFerias, PeriodoAquisitivo

def listar_funcionarios(request):
    funcionarios = (
        Funcionario.objects
        .select_related("banco_horas")  # pega o banco de horas
        .prefetch_related(
            "periodos_aquisitivos__ferias_registradas"  # pega férias
        )
        .order_by("nome")
    )

    return render(request, "core/ferias/listar_funcionarios.html", {
        "funcionarios": funcionarios
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
    return redirect('core/ferias:listar_funcionarios')

def listar_pagamentos(request):
    pagamentos = PagamentoFerias.objects.select_related('funcionario').order_by('-vencimento')
    return render(request, 'core/ferias/listar_pagamentos.html', {'pagamentos': pagamentos})

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

def deletar_pagamento(request, pk):
    pagamento = get_object_or_404(PagamentoFerias, pk=pk)
    pagamento.delete()
    messages.success(request, "Pagamento excluído com sucesso!")
    return redirect('ferias:listar_pagamentos')

def calcular_saldo_total(funcionario):
    saldo_total = 0
    for periodo in funcionario.periodos_aquisitivos.all():
        saldo_total += periodo.saldo_restante  # ou outra lógica que você use para saldo
    return saldo_total




def teste(request):
    funcionarios = Funcionario.objects.all().order_by('nome')

    # Inicializa os formulários vazios
    form_uso = FeriasForm()
    form_periodo = PeriodoAquisitivoForm()

    if request.method == 'POST':
        # Formulário de Férias
        if 'submit_uso' in request.POST:
            form_uso = FeriasForm(request.POST)
            if form_uso.is_valid():
                try:
                    form_uso.save()
                    messages.success(request, "Férias registradas com sucesso.")
                    return redirect('ferias:listar_funcionarios')
                except ValueError as e:
                    form_uso.add_error(None, str(e))

        # Formulário de Período Aquisitivo
        elif 'submit_periodo' in request.POST:
            form_periodo = PeriodoAquisitivoForm(request.POST)
            if form_periodo.is_valid():
                form_periodo.save()
                messages.success(request, "Período aquisitivo registrado com sucesso.")
                return redirect('ferias:listar_funcionarios')

    return render(request, 'core/ferias/teste.html', {
        'funcionarios': funcionarios,
        'form_uso': form_uso,
        'form_periodo': form_periodo,
    })
