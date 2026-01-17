from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmpreitadaForm, PagamentoEmpreitadaForm
from .models import Empreitada, PagamentoEmpreitada


@login_required
def empreitada_list(request):
    empreitadas = Empreitada.objects.filter(is_deleted=False).order_by('status', '-data_inicio')
    return render(request, 'core/empreitadas/list.html', {'empreitadas': empreitadas})

@login_required
def empreitada_detail(request, pk):
    empreitada = get_object_or_404(Empreitada, pk=pk)
    
    if request.method == 'POST':
        form = PagamentoEmpreitadaForm(request.POST)
        if form.is_valid():
            pagamento = form.save(commit=False)
            pagamento.empreitada = empreitada
            
            # CORREÇÃO: Verifica SE ultrapassa. Se sim, avisa e NÃO SALVA.
            if (empreitada.total_pago + pagamento.valor) > empreitada.valor_total:
                messages.warning(request, "Atenção: O valor lançado ultrapassa o total da empreitada! Operação cancelada.")
                # Não chamamos pagamento.save() aqui, apenas recarregamos a página
            else:
                # Se estiver tudo certo, aí sim salva
                pagamento.save()
                messages.success(request, "Pagamento/Retirada lançado com sucesso!")
                return redirect('empreitadas:detail', pk=pk)
    else:
        form = PagamentoEmpreitadaForm()

    return render(request, 'core/empreitadas/detail.html', {
        'empreitada': empreitada,
        'form': form
    })

@login_required
def empreitada_create(request):
    if request.method == 'POST':
        form = EmpreitadaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Empreitada cadastrada!")
            return redirect('empreitadas:list')
    else:
        form = EmpreitadaForm()
    
    return render(request, 'core/empreitadas/form.html', {'form': form, 'title': 'Nova Empreitada'})

@login_required
def empreitada_edit(request, pk):
    empreitada = get_object_or_404(Empreitada, pk=pk)
    
    if request.method == 'POST':
        form = EmpreitadaForm(request.POST, instance=empreitada)
        if form.is_valid():
            form.save()
            messages.success(request, "Empreitada atualizada com sucesso!")
            return redirect('empreitadas:list')
    else:
        form = EmpreitadaForm(instance=empreitada)
    
    return render(request, 'core/empreitadas/form.html', {
        'form': form,
        'titulo': f'Editar: {empreitada.funcionario.nome}'
    })

@login_required
def empreitada_delete(request, pk):
    empreitada = get_object_or_404(Empreitada, pk=pk)
    
    if request.method == 'POST':
        # Soft Delete (Marca como excluído sem apagar do banco)
        empreitada.is_deleted = True 
        empreitada.save()
        messages.success(request, "Empreitada excluída com sucesso!")
        return redirect('empreitadas:list')
        
    return render(request, 'core/empreitadas/delete.html', {
        'empreitada': empreitada
    })