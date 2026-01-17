import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, OuterRef, Subquery, Sum, Value, Q
from django.db.models.functions import Coalesce

from apps.banco_horas.models import LancamentoHoras
from apps.empreitadas.models import Empreitada, PagamentoEmpreitada
from apps.ferias.models import PagamentoFerias
from apps.financeiro.pagar.models import FolhaPagamento, ParcelamentoPagar
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
    Gera múltiplos lançamentos e cria a entidade pai ParcelamentoPagar.
    """
    instance_base = form.save(commit=False)
    qtd_parcelas = form.cleaned_data.get('parcelas', 1) or 1
    is_recorrente = form.cleaned_data.get('is_recorrente', False)
    
    # --- CORREÇÃO: Identificar qual campo de valor o model usa (valor ou valor_total) ---
    campo_valor = 'valor'
    if hasattr(instance_base, 'valor'):
        valor_total_form = instance_base.valor or Decimal('0.00')
    elif hasattr(instance_base, 'valor_total'):
        campo_valor = 'valor_total'
        valor_total_form = instance_base.valor_total or Decimal('0.00')
    else:
        # Fallback de segurança
        valor_total_form = Decimal('0.00')
    # ------------------------------------------------------------------------------------

    descricao_base = instance_base.descricao
    
    # 1. Cria o Pai (Parcelamento) se for mais de 1 parcela ou recorrente
    parcelamento_pai = None
    if qtd_parcelas > 1 or is_recorrente:
        parcelamento_pai = ParcelamentoPagar.objects.create(
            descricao=f"{descricao_base} (Ref: {instance_base.credor or ''})",
            valor_total_original=valor_total_form if not is_recorrente else (valor_total_form * qtd_parcelas),
            qtd_parcelas=qtd_parcelas
        )

    objetos_criados = []
    # Verifica qual campo de data usar (vencimento ou gasto)
    data_inicial = getattr(instance_base, 'data_vencimento', None) or getattr(instance_base, 'data_gasto', None) or date.today()
    
    # Cálculos de valor para parcelamento
    if is_recorrente:
        valor_parcela = valor_total_form
        resto = Decimal('0.00')
    else:
        valor_parcela = round(valor_total_form / qtd_parcelas, 2)
        resto = valor_total_form - (valor_parcela * qtd_parcelas)

    for i in range(qtd_parcelas):
        nova_instancia = model_class()
        
        # Copia todos os campos da instância base, ignorando chaves primárias e vínculos
        for field in instance_base._meta.fields:
            if field.name not in ['id', 'pk', 'parcelamento', 'parcelamento_uuid']:
                setattr(nova_instancia, field.name, getattr(instance_base, field.name))
        
        # Define datas (incrementa meses para cada parcela)
        nova_data = add_months(data_inicial, i)
        if hasattr(nova_instancia, 'data_vencimento'):
            nova_instancia.data_vencimento = nova_data
        elif hasattr(nova_instancia, 'data_gasto'):
            nova_instancia.data_gasto = nova_data
            
        # Define a descrição com o número da parcela
        nova_instancia.descricao = f"{descricao_base} ({i+1}/{qtd_parcelas})"

        # Calcula o valor desta parcela específica
        if is_recorrente:
            valor_atual = valor_parcela
        else:
            valor_atual = valor_parcela + resto if i == 0 else valor_parcela

        # --- CORREÇÃO: Atribui o valor ao campo correto identificado anteriormente ---
        if campo_valor == 'valor':
            nova_instancia.valor = valor_atual
            # Sincroniza valor_total se existir (ex: para compatibilidade futura)
            if hasattr(nova_instancia, 'valor_total'):
                nova_instancia.valor_total = valor_atual
        elif campo_valor == 'valor_total':
            nova_instancia.valor_total = valor_atual
            # Sincroniza valor se existir
            if hasattr(nova_instancia, 'valor'):
                nova_instancia.valor = valor_atual
        # -----------------------------------------------------------------------------

        # VÍNCULO COM O PAI
        if parcelamento_pai:
            nova_instancia.parcelamento = parcelamento_pai

        nova_instancia.save()
        objetos_criados.append(nova_instancia)
        
    return objetos_criados


def gerar_folha_mensal(mes, ano):
    data_ref = date(ano, mes, 1)
    
    # Define o último dia do mês para verificar se a demissão ocorreu antes ou durante este mês
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    data_ultimo_dia = date(ano, mes, ultimo_dia)

    # 1. LIMPEZA PREVENTIVA
    # Remove folhas 'Pendente' deste mês que pertençam a funcionários:
    # a) Marcados como excluídos (lixeira)
    # b) Com rescisão datada neste mês ou antes (pois a rescisão substitui a folha)
    FolhaPagamento.objects.filter(
        data_referencia=data_ref,
        status='Pendente'
    ).filter(
        Q(funcionario__is_deleted=True) | 
        Q(funcionario__rescisao__data_demissao__lte=data_ultimo_dia)
    ).delete()

    # 2. SUBQUERIES (Otimização para buscar totais sem loops extras)
    ferias_sum = PagamentoFerias.objects.filter(
        funcionario=OuterRef('pk'),
        vencimento__month=mes, vencimento__year=ano, is_deleted=False
    ).values('funcionario').annotate(total=Sum('valor_a_pagar')).values('total')

    empreitada_sum = PagamentoEmpreitada.objects.filter(
        empreitada__funcionario=OuterRef('pk'),
        data__month=mes, data__year=ano, is_deleted=False
    ).values('empreitada__funcionario').annotate(total=Sum('valor')).values('total')

    # 3. QUERY PRINCIPAL DE FUNCIONÁRIOS
    # Filtra apenas ativos e que NÃO tenham rescisão vigente até o fim deste mês
    funcionarios = Funcionario.objects.filter(is_deleted=False).exclude(
        rescisao__data_demissao__lte=data_ultimo_dia
    ).annotate(
        total_ferias=Coalesce(Subquery(ferias_sum), Value(Decimal('0.00'))),
        total_empreitada=Coalesce(Subquery(empreitada_sum), Value(Decimal('0.00'))),
    ).select_related('dados_trabalhistas')

    registros = []
    
    for func in funcionarios:
        # A. Busca Salário Base
        try:
            salario_base = func.dados_trabalhistas.salario if hasattr(func, 'dados_trabalhistas') else Decimal('0.00')
        except ObjectDoesNotExist:
            salario_base = Decimal('0.00')

        valor_adiantamento = round(salario_base * Decimal('0.40'), 2)

        # B. Integração Banco de Horas
        total_horas_mes = LancamentoHoras.objects.filter(
            funcionario=func,
            data__month=mes,
            data__year=ano,
            is_deleted=False
        ).aggregate(
            total=Sum(F('horas') * F('valor_hora'))
        )['total'] or Decimal('0.00')

        # C. Integração Empreitadas (via annotate ou fallback)
        # Usando o valor já trazido pelo annotate para otimização
        total_empreitadas_mes = func.total_empreitada

        # D. Integração Férias (via annotate ou fallback)
        total_ferias_terco = func.total_ferias

        # E. Cria ou Recupera o registro da Folha
        folha, created = FolhaPagamento.objects.get_or_create(
            funcionario=func,
            data_referencia=data_ref,
            defaults={
                'salario_real': salario_base,
                'adiantamento': valor_adiantamento,
                'ferias_terco': total_ferias_terco, 
                'empreitada': total_empreitadas_mes, 
                'decimo_terceiro': Decimal('0.00'),
                'vale': Decimal('0.00'),
                'horas_extras_valor': total_horas_mes,
                'status': 'Pendente'
            }
        )

        # F. Atualiza valores se já existir (e não estiver pago)
        # Isso garante que se você rodar "Gerar" de novo, ele recalcula horas/empreitadas
        if not created and folha.status == 'Pendente':
            mudou = False
            
            # Verifica mudanças nos valores variáveis
            if folha.horas_extras_valor != total_horas_mes:
                folha.horas_extras_valor = total_horas_mes
                mudou = True
            
            if folha.empreitada != total_empreitadas_mes:
                folha.empreitada = total_empreitadas_mes
                mudou = True
            
            if folha.ferias_terco != total_ferias_terco:
                folha.ferias_terco = total_ferias_terco
                mudou = True
            
            # Se o salário mudou no cadastro, atualiza na folha também
            if folha.salario_real != salario_base:
                folha.salario_real = salario_base
                # Recalcula adiantamento se o salário mudou
                folha.adiantamento = round(salario_base * Decimal('0.40'), 2)
                mudou = True

            if mudou:
                folha.save()

        registros.append(folha)
        
    return registros