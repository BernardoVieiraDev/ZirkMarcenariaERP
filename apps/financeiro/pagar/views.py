from django.shortcuts import render, get_object_or_404, redirect
from .models import Pagar
from .forms import  PagarForm 
from django.db.models import Sum


def pagar_list(request):
    qs = Pagar.objects.all()
    total = qs.aggregate(total=Sum('value'))['total'] or 0
    return render(request, 'core/financeiro/pagar/list.html', {'list': qs, 'total': total})

def pagar_create(request):
    if request.method == 'POST':
        form = PagarForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pagar:pagar')
    else:
        form = PagarForm()
    return render(request, 'core/financeiro/pagar/form.html', {'form': form, 'title': 'Nova Conta a Pagar'})

def pagar_edit(request, pk):
    obj = get_object_or_404(Pagar, pk=pk)
    if request.method == 'POST':
        form = PagarForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('pagar:pagar')
    else:
        form = PagarForm(instance=obj)
    return render(request, 'core/financeiro/pagar/form.html', {'form': form, 'title': 'Editar Conta a Pagar'})

def pagar_delete(request, pk):
    obj = get_object_or_404(Pagar, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('pagar:pagar')
    return render(request, 'core/financeiro/pagar/delete.html', {'object': obj})

