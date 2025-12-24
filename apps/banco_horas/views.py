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
            # Alterado para voltar para a lista de banco de horas
            return redirect('banco_horas:banco_horas_list') 
            
    # Se der erro ou for GET direto (fallback), renderiza a página antiga ou redireciona
    return redirect('banco_horas:banco_horas_list')


def banco_horas_list(request):
    """
    Lista todos os saldos de Banco de Horas dos funcionários.
    """
    # Garante que um BancoHoras exista para cada funcionário, se for o caso
    # (Opcional: criar objetos BancoHoras se não existirem, mas o prefetch abaixo funciona)
    
    bancos = BancoHoras.objects.select_related('funcionario').order_by('funcionario__nome')

    # --- NOVO: Formulário para o Modal ---
    form = LancamentoHorasForm()

    context = {
        'bancos': bancos,
        'form': form, # Enviando o formulário
        'title': 'Saldos de Banco de Horas'
    }
    return render(request, 'core/banco_horas/banco_horas_list.html', context)

# ... (Mantenha o resto do arquivo: BancoHorasEditForm e banco_horas_edit) ...
class BancoHorasEditForm(forms.ModelForm):
    class Meta:
        model = BancoHoras
        fields = ['saldo']
        widgets = {
            'saldo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Mantenha os imports existentes

def banco_horas_edit(request, pk):
    banco = get_object_or_404(BancoHoras, pk=pk)
    
    if request.method == 'POST':
        form = BancoHorasEditForm(request.POST, instance=banco)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saldo de {banco.funcionario.nome} ajustado com sucesso!")
            return redirect('banco_horas:banco_horas_list')
    else:
        form = BancoHorasEditForm(instance=banco)
        
    context = {
        'form': form,
        'banco': banco,
        'title': f'Ajustar Saldo'
    }

    # SE FOR AJAX, RETORNA O MODAL
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/banco_horas/form_modal.html', context)

    # Fallback normal
    return render(request, 'core/banco_horas/banco_horas_edit.html', context)

# ADICIONE ESTA NOVA VIEW
def banco_horas_delete(request, pk):
    banco = get_object_or_404(BancoHoras, pk=pk)
    
    if request.method == 'POST':
        banco.delete()
        messages.success(request, f"Banco de horas de {banco.funcionario.nome} removido.")
        return redirect('banco_horas:banco_horas_list')

    # SE FOR AJAX, RETORNA O MODAL
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/banco_horas/delete_modal.html', {'object': banco})
        
    # Fallback (caso precise de uma página dedicada, crie o template delete.html depois)
    return redirect('banco_horas:banco_horas_list')