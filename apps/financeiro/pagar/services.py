import calendar
from datetime import date
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce

from apps.banco_horas.models import LancamentoHoras
from apps.empreitadas.models import Empreitada, PagamentoEmpreitada
from apps.ferias.models import PagamentoFerias
from apps.financeiro.pagar.models import FolhaPagamento, ParcelamentoPagar
from apps.financeiro.receber.models import CaixaDiario, MovimentoBanco
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

    # 1. Pega a data base correta, independentemente de qual formulário seja
    data_inicial = getattr(instance_base, 'data_vencimento', None) or \
                   getattr(instance_base, 'data_gasto', None) or \
                   getattr(instance_base, 'data_referencia', None) or \
                   getattr(instance_base, 'data_emissao', None) or \
                   date.today()

    qtd_parcelas = form.cleaned_data.get('parcelas', 1) or 1
    is_recorrente = form.cleaned_data.get('is_recorrente', False)
    
    # --- Identificar DINAMICAMENTE qual campo de valor o model usa ---
    campo_valor = 'valor'
    if hasattr(instance_base, 'valor') and instance_base.valor is not None:
        valor_total_form = instance_base.valor
    elif hasattr(instance_base, 'valor_total') and instance_base.valor_total is not None:
        campo_valor = 'valor_total'
        valor_total_form = instance_base.valor_total
    elif hasattr(instance_base, 'valor_comissao') and instance_base.valor_comissao is not None:
        campo_valor = 'valor_comissao'
        valor_total_form = instance_base.valor_comissao
    elif hasattr(instance_base, 'salario_real') and instance_base.salario_real is not None:
        campo_valor = 'salario_real'
        valor_total_form = instance_base.salario_real
    else:
        valor_total_form = Decimal('0.00')
    # ---------------------------------------------------------------------------

    descricao_base = getattr(instance_base, 'descricao', '') or "Despesa"
    
    parcelamento_pai = None
    if qtd_parcelas > 1 or is_recorrente:
        credor_nome = getattr(instance_base, 'credor', '')
        if not credor_nome and hasattr(instance_base, 'arquiteto'): credor_nome = str(instance_base.arquiteto)
        if not credor_nome and hasattr(instance_base, 'funcionario'): credor_nome = str(instance_base.funcionario)
        
        parcelamento_pai = ParcelamentoPagar.objects.create(
            descricao=f"{descricao_base} (Ref: {credor_nome})",
            valor_total_original=valor_total_form if not is_recorrente else (valor_total_form * qtd_parcelas),
            qtd_parcelas=qtd_parcelas
        )

    objetos_criados = []
    
    if is_recorrente:
        valor_parcela = valor_total_form
        resto = Decimal('0.00')
    else:
        valor_parcela = round(valor_total_form / qtd_parcelas, 2)
        resto = valor_total_form - (valor_parcela * qtd_parcelas)

    for i in range(qtd_parcelas):
        nova_instancia = model_class()
        
        for field in instance_base._meta.fields:
            if field.name not in ['id', 'pk', 'parcelamento', 'parcelamento_uuid']:
                setattr(nova_instancia, field.name, getattr(instance_base, field.name))
        
        nova_data = add_months(data_inicial, i)
        
        # 2. Atualiza a data da parcela avançando 1 mês por vez no campo correto
        if hasattr(nova_instancia, 'data_vencimento'): 
            nova_instancia.data_vencimento = nova_data
        elif hasattr(nova_instancia, 'data_gasto'): 
            nova_instancia.data_gasto = nova_data
        elif hasattr(nova_instancia, 'data_referencia'): 
            nova_instancia.data_referencia = nova_data
        elif hasattr(nova_instancia, 'data_emissao'): 
            nova_instancia.data_emissao = nova_data
            
        if hasattr(nova_instancia, 'descricao'):
            nova_instancia.descricao = f"{descricao_base} ({i+1}/{qtd_parcelas})"

        valor_atual = valor_parcela if is_recorrente else (valor_parcela + resto if i == 0 else valor_parcela)

        # --- ATRIBUI O VALOR DIVIDIDO PARA O CAMPO CORRETO ---
        if campo_valor == 'valor':
            nova_instancia.valor = valor_atual
        elif campo_valor == 'valor_total':
            nova_instancia.valor_total = valor_atual
        elif campo_valor == 'valor_comissao':
            nova_instancia.valor_comissao = valor_atual
        elif campo_valor == 'salario_real':
            nova_instancia.salario_real = valor_atual
        # -----------------------------------------------------

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


# --- ADICIONE ESTES IMPORTS NO TOPO DO ARQUIVO ---

# --- ADICIONE ESTA CLASSE NO FINAL DO ARQUIVO ---

class GestorPagamentoService:
    """
    Serviço responsável por pegar um Gasto (Almoço, Gasolina, Geral)
    e criar/atualizar o lançamento correspondente no Banco ou Caixa.
    """
    def __init__(self, instance):
        self.instance = instance
        # Descobre qual é o nome do modelo (Ex: 'GastoAlmoco', 'GastoGasolina')
        self.model_name = instance.__class__.__name__

    def processar_lancamento(self):
        # 1. Se não estiver pago, removemos qualquer lançamento financeiro existente
        if self.instance.status != 'Pago':
            self._remover_financeiro()
            return

        # 2. Prepara os dados comuns
        valor = self._get_valor()
        data = self._get_data()
        descricao = str(self.instance)

        # 3. Direciona para Banco ou Caixa
        if self.instance.origem_pagamento == 'BANCO':
            self._processar_banco(valor, data, descricao)
        elif self.instance.origem_pagamento == 'CAIXA':
            self._processar_caixa(valor, data, descricao)

    def _get_valor(self):
        # GastoAlmoco usa 'valor_total', outros usam 'valor'
        if hasattr(self.instance, 'valor_total'):
            return self.instance.valor_total
        return getattr(self.instance, 'valor', 0)

    def _get_data(self):
        # GastoAlmoco usa 'data_gasto', outros usam 'data_pagamento'
        if hasattr(self.instance, 'data_gasto'):
            return self.instance.data_gasto
        return getattr(self.instance, 'data_pagamento', self.instance.data_vencimento)

# No método _processar_banco e _processar_caixa em GestorPagamentoService

# Em apps/financeiro/pagar/services.py

    def _processar_banco(self, valor, data, descricao):
        if not self.instance.banco_origem:
            return 

        if valor > 0:
            valor = valor * -1

        dados_movimento = {
            'data': data,
            'historico': descricao,  # CORREÇÃO: De 'descricao' para 'historico'
            'valor': valor,
            'tipo': 'SAIDA',
            'banco': self.instance.banco_origem,
            # 'categoria': ... (REMOVIDO: O modelo MovimentoBanco não tem esse campo)
        }

        movimento = self.instance.movimento_banco

        if movimento:
            for key, value in dados_movimento.items():
                setattr(movimento, key, value)
            movimento.save()
        else:
            movimento = MovimentoBanco.objects.create(**dados_movimento)
            
            self.instance.movimento_banco = movimento
            self.instance.save(update_fields=['movimento_banco'])
            
        if self.instance.movimento_caixa:
            self.instance.movimento_caixa.delete()

    def _processar_caixa(self, valor, data, descricao):
        if valor > 0:
            valor = valor * -1

        dados_caixa = {
            'data': data,
            'historico': descricao, # CORREÇÃO: De 'descricao' para 'historico'
            'valor': valor,
            'tipo': 'SAIDA',
        }

        movimento = self.instance.movimento_caixa

        if movimento:
            for key, value in dados_caixa.items():
                setattr(movimento, key, value)
            movimento.save()
        else:
            movimento = CaixaDiario.objects.create(**dados_caixa)
            
            self.instance.movimento_caixa = movimento
            self.instance.save(update_fields=['movimento_caixa'])

        if self.instance.movimento_banco:
            self.instance.movimento_banco.delete()

    def _remover_financeiro(self):
        if self.instance.movimento_banco:
            self.instance.movimento_banco.delete()
        if self.instance.movimento_caixa:
            self.instance.movimento_caixa.delete()