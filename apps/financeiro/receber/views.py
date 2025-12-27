from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ReceberForm
from .models import Receber

def receber_list(request):
    qs = Receber.objects.all().order_by('status', 'data_vencimento') # Ordena por status e data
    total = qs.aggregate(total=Sum('valor'))['total'] or 0
    
    # Formulário vazio para o modal de criação (se usado na listagem)
    form = ReceberForm()
    
    return render(request, 'core/financeiro/receber/list.html', {
        'list': qs, 
        'total': total, 
        'form': form
    })

def receber_create(request):
    if request.method == 'POST':
        form = ReceberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm()
    
    return render(request, 'core/financeiro/receber/form.html', {
        'form': form, 
        'title': 'Nova Receita'
    })

def receber_edit(request, pk):
    obj = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        form = ReceberForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm(instance=obj)
        
    return render(request, 'core/financeiro/receber/form.html', {
        'form': form, 
        'title': 'Editar Receita'
    })

def receber_delete(request, pk):
    obj = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('receber:receber')
        
    return render(request, 'core/financeiro/receber/delete.html', {'object': obj})