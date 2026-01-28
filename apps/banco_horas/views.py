from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render

from apps.funcionarios.models import Funcionario

from .forms import LancamentoHorasForm
from .models import BancoHoras, LancamentoHoras


@login_required
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


@login_required
def banco_horas_list(request):
    """
    Lista todos os saldos de Banco de Horas e pré-calcula o acumulado mensal.
    """
    # Buscamos todos os bancos com os dados do funcionário
    bancos = BancoHoras.objects.select_related('funcionario').order_by('funcionario__nome')
    
    dados_consolidados = []

    for banco in bancos:
        # Aqui está a mágica: Agrupamos os lançamentos deste funcionário por Mês
        # e somamos as horas de cada mês.
        resumo_mensal = (
            LancamentoHoras.objects
            .filter(funcionario=banco.funcionario)
            .annotate(mes_ano=TruncMonth('data'))  # Corta a data para apenas Mês/Ano
            .values('mes_ano')                     # Agrupa por esse Mês/Ano
            .annotate(saldo_no_mes=Sum('horas'))   # Soma as horas desse grupo
            .order_by('-mes_ano')                  # Ordena do mais recente para o antigo
        )

        dados_consolidados.append({
            'banco_obj': banco,       # O objeto BancoHoras original (para pegar o total geral)
            'mensal': resumo_mensal,  # A lista com os saldos mês a mês
        })

    # --- NOVO: Formulário para o Modal (mantido do seu código) ---
    form = LancamentoHorasForm()

    context = {
        'lista_bancos': dados_consolidados, # Note que mudamos a variável de 'bancos' para 'lista_bancos'
        'form': form,
        'title': 'Saldos de Banco de Horas'
    }
    return render(request, 'core/banco_horas/banco_horas_list.html', context)



class BancoHorasEditForm(forms.ModelForm):
    class Meta:
        model = BancoHoras
        fields = ['saldo']
        widgets = {
            'saldo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Mantenha os imports existentes
@login_required
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

@login_required
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


@login_required
def historico_funcionario(request, pk):
    """
    Exibe o extrato de lançamentos de um funcionário específico em um Modal.
    pk: ID do Funcionario
    """
    funcionario = get_object_or_404(Funcionario, pk=pk)
    
    # Busca lançamentos e ordena por data decrescente
    lancamentos = LancamentoHoras.objects.filter(
        funcionario=funcionario
    ).order_by('-data')

    context = {
        'funcionario': funcionario,
        'lancamentos': lancamentos,
    }
    
    # Se for requisição AJAX (Modal), renderiza apenas o pedaço do modal
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'core/banco_horas/historico_modal.html', context)
        
    # Fallback caso alguém acesse a URL diretamente (opcional)
    return render(request, 'core/banco_horas/historico_modal.html', context)