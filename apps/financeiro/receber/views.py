from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReceberForm
from .models import Receber


# Create your views here.
def receber_list(request):
    qs = Receber.objects.all()
    total = qs.aggregate(total=Sum('value'))['total'] or 0
    return render(request, 'core/financeiro/receber/list.html', {'list': qs, 'total': total})

def receber_create(request):
    if request.method == 'POST':
        form = ReceberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm()
    return render(request, 'core/financeiro/receber/form.html', {'form': form, 'title': 'Nova Conta a Receber'})

def receber_edit(request, pk):
    obj = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        form = ReceberForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('receber:receber')
    else:
        form = ReceberForm(instance=obj)
    return render(request, 'core/financeiro/receber/form.html', {'form': form, 'title': 'Editar Conta a Receber'})

def receber_delete(request, pk):
    obj = get_object_or_404(Receber, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('receber:receber')
    return render(request, 'core/financeiro/receber/delete.html', {'object': obj})

