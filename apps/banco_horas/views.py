from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.funcionarios.models import Funcionario
from .models import BancoHoras, LancamentoHoras
from .forms import LancamentoHorasForm


def registrar_horas(request):
    if request.method == 'POST':
        form = LancamentoHorasForm(request.POST)
        if form.is_valid():
            lancamento = form.save()

            # Atualiza o banco de horas
            banco, created = BancoHoras.objects.get_or_create(funcionario=lancamento.funcionario)
            banco.saldo += lancamento.horas
            banco.save()

            messages.success(request, "Horas registradas com sucesso!")
            return redirect('ferias:listar_funcionarios')
    else:
        form = LancamentoHorasForm()

    return render(request, 'core/banco_horas/registrar_horas.html', {'form': form})
