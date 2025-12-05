from django.shortcuts import render
from django.db.models import Sum
from apps.financeiro.pagar.models import Pagar, StatusPagamento
from apps.financeiro.receber.models import Receber
from apps.funcionarios.models import Funcionario
from datetime import datetime

def dashboard(request):
    # Obter a data e hora atuais
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    cont_funcionarios = Funcionario.objects.count()
    pagar_total = Pagar.objects.exclude(status=StatusPagamento.PAGO).aggregate(total=Sum('value'))['total'] or 0
    receber_total = Receber.objects.exclude(status='Pago').exclude(data_vencimento__isnull=False).aggregate(total=Sum('valor'))['total'] or 0
    
    # Filtrando contas a pagar para o mês atual
    pagar_preview = Pagar.objects.filter(due__month=current_month, due__year=current_year)[:5]
    
    context = { 
        'cont_funcionarios': cont_funcionarios,
        'pagar_total': pagar_total,
        'receber_total': receber_total,
        'pagar_preview': pagar_preview,
        'receber_preview': Receber.objects.all()[:5],
    }
    
    return render(request, 'core/dashboard.html', context)
