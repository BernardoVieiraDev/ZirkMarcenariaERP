import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from apps.banco_horas.models import LancamentoHoras
# Importação necessária para buscar os pagamentos das empreitadas
from apps.empreitadas.models import Empreitada, PagamentoEmpreitada
# --- CORREÇÃO: Importar o modelo de Pagamento de Férias ---
from apps.ferias.models import PagamentoFerias
from apps.financeiro.pagar.models import FolhaPagamento
from apps.funcionarios.models import Funcionario


def add_months(source_date, months):
    """Adiciona meses a uma data corretamente."""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def gerar_lancamentos_parcelados(form, model_class, user=None):
    """
    Gera múltiplos lançamentos baseados nos dados do formulário.
    """
    instance_base = form.save(commit=False)
    qtd_parcelas = form.cleaned_data.get('qtd_parcelas', 1) or 1
    is_recorrente = form.cleaned_data.get('is_recorrente', False)
    
    objetos_criados = []
    valor_total = instance_base.valor or Decimal('0.00')
    data_inicial = instance_base.data_vencimento or instance_base.data_gasto or date.today()
    descricao_original = instance_base.descricao
    
    if is_recorrente:
        valor_parcela = valor_total
        resto = Decimal('0.00')
    else:
        valor_parcela = round(valor_total / qtd_parcelas, 2)
        resto = valor_total - (valor_parcela * qtd_parcelas)

    for i in range(qtd_parcelas):
        nova_instancia = model_class()
        for field in instance_base._meta.fields:
            if field.name not in ['id', 'pk']:
                setattr(nova_instancia, field.name, getattr(instance_base, field.name))
        
        nova_data = add_months(data_inicial, i)
        
        if hasattr(nova_instancia, 'data_vencimento'):
            nova_instancia.data_vencimento = nova_data
        elif hasattr(nova_instancia, 'data_gasto'):
            nova_instancia.data_gasto = nova_data
            
        if is_recorrente:
            nova_instancia.descricao = f"{descricao_original} ({i+1}/{qtd_parcelas})"
            nova_instancia.valor = valor_parcela
            if hasattr(nova_instancia, 'valor_total'): nova_instancia.valor_total = valor_parcela
        else:
            nova_instancia.descricao = f"{descricao_original} ({i+1}/{qtd_parcelas})"
            valor_atual = valor_parcela + resto if i == 0 else valor_parcela
            nova_instancia.valor = valor_atual
            if hasattr(nova_instancia, 'valor_total'): nova_instancia.valor_total = valor_atual

        nova_instancia.save()
        objetos_criados.append(nova_instancia)
        
    return objetos_criados


def gerar_folha_mensal(mes, ano):
    data_ref = date(ano, mes, 1)
    
    # Subqueries para somar valores sem loops
    ferias_sum = PagamentoFerias.objects.filter(
        funcionario=OuterRef('pk'),
        vencimento__month=mes, vencimento__year=ano, is_deleted=False
    ).values('funcionario').annotate(total=Sum('valor_a_pagar')).values('total')

    empreitada_sum = PagamentoEmpreitada.objects.filter(
        empreitada__funcionario=OuterRef('pk'),
        data__month=mes, data__year=ano, is_deleted=False
    ).values('empreitada__funcionario').annotate(total=Sum('valor')).values('total')

    # Query única anotada
    funcionarios = Funcionario.objects.filter(is_deleted=False).annotate(
        total_ferias=Coalesce(Subquery(ferias_sum), Value(Decimal('0.00'))),
        total_empreitada=Coalesce(Subquery(empreitada_sum), Value(Decimal('0.00'))),
        # Fazer o mesmo para Banco de Horas (requer lógica de valor_hora * horas, mais complexo em SQL puro,
        # talvez manter o loop do banco de horas se for complexo, mas otimizar o resto)
    ).select_related('dados_trabalhistas')

    registros = []
    
    for func in funcionarios:
        # 1. Busca Salário Base
        try:
            salario_base = func.dados_trabalhistas.salario if hasattr(func, 'dados_trabalhistas') else Decimal('0.00')
        except ObjectDoesNotExist:
            salario_base = Decimal('0.00')

        valor_adiantamento = round(salario_base * Decimal('0.40'), 2)

        # 2. Integração Banco de Horas
        total_horas_mes = LancamentoHoras.objects.filter(
            funcionario=func,
            data__month=mes,
            data__year=ano,
            is_deleted=False
        ).aggregate(
            total=Sum(F('horas') * F('valor_hora'))
        )['total'] or Decimal('0.00')

        # 3. Integração Empreitadas
        total_empreitadas_mes = PagamentoEmpreitada.objects.filter(
            empreitada__funcionario=func,
            data__month=mes,
            data__year=ano,
            is_deleted=False
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        # 4. Integração Férias (1/3) - NOVO
        # Soma os pagamentos de 1/3 cujo vencimento cai neste mês
        total_ferias_terco = PagamentoFerias.objects.filter(
            funcionario=func,
            vencimento__month=mes,
            vencimento__year=ano,
            is_deleted=False
        ).aggregate(
            total=Sum('valor_a_pagar')
        )['total'] or Decimal('0.00')

        # 5. Cria ou Recupera o registro da Folha
        folha, created = FolhaPagamento.objects.get_or_create(
            funcionario=func,
            data_referencia=data_ref,
            defaults={
                'salario_real': salario_base,
                'adiantamento': valor_adiantamento,
                'ferias_terco': total_ferias_terco, # Campo populado automaticamente
                'empreitada': total_empreitadas_mes, 
                'decimo_terceiro': Decimal('0.00'),
                'vale': Decimal('0.00'),
                'horas_extras_valor': total_horas_mes,
                'status': 'Pendente'
            }
        )

        # 6. Atualiza valores se já existir (e não estiver pago)
        if not created:
            mudou = False
            
            if folha.horas_extras_valor != total_horas_mes:
                folha.horas_extras_valor = total_horas_mes
                mudou = True
            
            if folha.empreitada != total_empreitadas_mes:
                folha.empreitada = total_empreitadas_mes
                mudou = True
            
            # Atualiza se o valor de férias mudou
            if folha.ferias_terco != total_ferias_terco:
                folha.ferias_terco = total_ferias_terco
                mudou = True
                
            if mudou:
                # Adicionado 'ferias_terco' aos campos a atualizar
                folha.save(update_fields=['horas_extras_valor', 'empreitada', 'ferias_terco'])

        registros.append(folha)
        
    return registros