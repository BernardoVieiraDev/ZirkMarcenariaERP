from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from apps.funcionarios.models import Funcionario
from .models import BancoHoras, LancamentoHoras
from .forms import LancamentoHorasForm
from django import forms

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


def banco_horas_list(request):
    """
    Lista todos os saldos de Banco de Horas dos funcionários.
    """
    # Garante que um BancoHoras exista para cada funcionário, se for o caso
    funcionarios = Funcionario.objects.all().prefetch_related('banco_horas')
    
    # Busca os saldos existentes (usando select_related para performance)
    bancos = BancoHoras.objects.select_related('funcionario').order_by('funcionario__nome')

    context = {
        'bancos': bancos,
        'title': 'Saldos de Banco de Horas'
    }
    return render(request, 'core/banco_horas/banco_horas_list.html', context)

# Criando um ModelForm simples para editar apenas o saldo
class BancoHorasEditForm(forms.ModelForm):
    class Meta:
        model = BancoHoras
        fields = ['saldo']
        widgets = {
            'saldo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

def banco_horas_edit(request, pk):
    """
    Permite editar o saldo do Banco de Horas manualmente (Ajuste).
    """
    banco = get_object_or_404(BancoHoras, pk=pk)
    
    if request.method == 'POST':
        form = BancoHorasEditForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saldo de Banco de Horas de {banco.funcionario.nome} ajustado com sucesso!")
            return redirect('banco_horas:banco_horas_list')
    else:
        form = BancoHorasEditForm(instance=banco)
        
    context = {
        'form': form,
        'banco': banco,
        'title': f'Ajustar Saldo de {banco.funcionario.nome}'
    }
    return render(request, 'core/banco_horas/banco_horas_edit.html', context)