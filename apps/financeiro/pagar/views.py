import calendar
import io
from datetime import date, datetime, timedelta
from decimal import Decimal

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, DecimalField, F, Q, Sum, Value, When
from django.forms import modelformset_factory
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from apps.financeiro.pagar.models import FolhaPagamento
from apps.financeiro.pagar.services import gerar_folha_mensal
from apps.financeiro.utils import gerar_parcelas
from apps.relatorios.services.holerite import HoleriteExcelService

from .forms import (BoletoForm, ChequeForm, ComissaoArquitetoForm,
                    FaturaCartaoForm, FolhaPagamentoForm,
                    GastoContabilidadeForm, GastoGasolinaForm, GastoGeralForm,
                    GastoImovelForm, GastoUtilidadeForm,
                    GastoVeiculoConsorcioForm, PrestacaoEmprestimoForm,
                    TipoGastoForm)
from .models import (Boleto, Cheque, ComissaoArquiteto, FaturaCartao,
                     FolhaPagamento, GastoBase, GastoContabilidade,
                     GastoGasolina, GastoGeral, GastoImovel, GastoUtilidade,
                     GastoVeiculoConsorcio, PrestacaoEmprestimo)

# ----------------------------------------------------
# MAPA DE MODELOS
# ----------------------------------------------------

MODEL_FORM_MAP = {
    'Boleto': {'model': Boleto, 'form': BoletoForm, 'title': 'Novo Boleto'},
    'FaturaCartao': {'model': FaturaCartao, 'form': FaturaCartaoForm, 'title': 'Nova Fatura de Cartão'},
    'PrestacaoEmprestimo': {'model': PrestacaoEmprestimo, 'form': PrestacaoEmprestimoForm, 'title': 'Nova Prestação de Empréstimo'},
    'GastoVeiculoConsorcio': {'model': GastoVeiculoConsorcio, 'form': GastoVeiculoConsorcioForm, 'title': 'Novo Gasto Veicular'},
    'GastoContabilidade': {'model': GastoContabilidade, 'form': GastoContabilidadeForm, 'title': 'Novo Encargo Contábil'},
    'GastoImovel': {'model': GastoImovel, 'form': GastoImovelForm, 'title': 'Novo Gasto Imobiliário (IPTU/Condomínio)'},
    'GastoUtilidade': {'model': GastoUtilidade, 'form': GastoUtilidadeForm, 'title': 'Nova Conta de Utilidade'},
    'GastoGeral': {'model': GastoGeral, 'form': GastoGeralForm, 'title': 'Novo Gasto Geral'},
    'GastoGasolina': {'model': GastoGasolina, 'form': GastoGasolinaForm, 'title': 'Novo Gasto com Gasolina'},
    'Cheque': {'model': Cheque, 'form': ChequeForm, 'title': 'Novo Gasto com Cheque'},
    'FolhaPagamento': {'model': FolhaPagamento, 'form': FolhaPagamentoForm, 'title': 'Folha pagamento'},
    'ComissaoArquiteto': {'model': ComissaoArquiteto, 'form': ComissaoArquitetoForm, 'title': 'Comissão Arquitetos'}
}

# ----------------------------------------------------
# AUXILIARES
# ----------------------------------------------------

def _get_gasto_object_info(pk, tipo=None):
    """
    Recupera o objeto de gasto de forma segura.
    CORREÇÃO DE SEGURANÇA: Remove a iteração de 'fallback' que causava colisão de IDs.
    O parâmetro 'tipo' agora é obrigatório para identificar a tabela correta.
    """
    if not tipo:
        # Segurança: Retorna None se o tipo não for especificado.
        # IDs não são únicos entre tabelas diferentes.
        return None
    
    if tipo in MODEL_FORM_MAP:
        data = MODEL_FORM_MAP[tipo]
        ModelClass = data['model']
        try:
            obj = ModelClass.objects.get(pk=pk)
            return ModelClass, obj, data['form'], data['title']
        except ModelClass.DoesNotExist:
            return None
            
    return None

def sort_key(obj):
    """Garantir ordenação compatível entre todos os modelos."""
    # Tenta usar a anotação 'data_sort' se criada na view, senão usa lógica padrão
    if hasattr(obj, 'data_sort') and obj.data_sort:
        return obj.data_sort

    campos_data = ['data_vencimento', 'data_gasto', 'data_emissao', 'data_referencia', 'data_pagamento']
    for campo in campos_data:
        if hasattr(obj, campo):
            valor = getattr(obj, campo)
            if valor:
                return valor
    return date(1900, 1, 1)

# ----------------------------------------------------
# VIEW - LISTAGEM UNIFICADA
# ----------------------------------------------------

@login_required
def pagar_list(request):
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    start_date = None
    end_date = None

    # 1. Filtro de Data
    if mes and ano:
        try:
            mes = int(mes)
            ano = int(ano)
            start_date = date(ano, mes, 1)
            if mes == 12:
                end_date = date(ano + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(ano, mes + 1, 1) - timedelta(days=1)
        except ValueError:
            pass 

    # 2. Definição das Categorias para Agrupamento Visual
    cat_operacional = ['GastoGeral', 'GastoGasolina']
    cat_folha = ['FolhaPagamento']
    cat_comissao = ['ComissaoArquiteto']
    
    # Listas de Resultados
    list_contas = []
    list_operacional = []
    list_folha = []
    list_comissao = []
    
    # Totais Globais
    total_pendente = Decimal('0.00')
    total_pago = Decimal('0.00')
    total_registros = 0
    
    # Lista de Status considerados "Pagos"
    STATUS_PAGO_LIST = ['Pago', 'PG', 'Recebido', 'COM']
    select_opts = ['banco_origem', 'movimento_banco'] 

    # 3. Loop nos Modelos (Com Agregação Otimizada)
    for key, data in MODEL_FORM_MAP.items():
        ModelClass = data['model']
        
        # Define o campo de data principal para filtro e ordenação
        campo_data = 'data_vencimento'
        if key in ['GastoGeral', 'GastoGasolina']: campo_data = 'data_gasto'
        elif key == 'Cheque': campo_data = 'data_emissao'
        elif key == 'FolhaPagamento': campo_data = 'data_referencia'
        
        # Filtro Base
        filtros = {'is_deleted': False}
        if start_date and end_date:
            filtros[f"{campo_data}__range"] = (start_date, end_date)
            
        qs = ModelClass.objects.filter(**filtros)

        # Otimização de Queries Relacionadas
        related_fields = [f for f in select_opts if hasattr(ModelClass, f) or 
                          (f == 'banco_origem' and hasattr(ModelClass, 'banco_origem'))]
        if related_fields:
            qs = qs.select_related(*related_fields)

        # --- LÓGICA DE VALOR CONSOLIDADO (NO BANCO DE DADOS) ---
        # Cria uma expressão SQL para o valor, dependendo do modelo
        
        val_expr = None
        
        if key == 'FolhaPagamento':
            # Soma dos componentes da folha
            val_expr = (
                F('salario_real') + 
                F('ferias_terco') + 
                F('empreitada') + 
                F('decimo_terceiro') + 
                F('horas_extras_valor')
            )
        elif key == 'ComissaoArquiteto':
            # Se pago, usa valor_pago, senão valor_comissao
            val_expr = Case(
                When(status__in=STATUS_PAGO_LIST, valor_pago__isnull=False, then=F('valor_pago')),
                default=F('valor_comissao'),
                output_field=DecimalField()
            )
        elif key in ['Boleto', 'GastoVeiculoConsorcio']:
            # Se pago, usa valor_pago, senão valor (nominal)
            val_expr = Case(
                When(status__in=STATUS_PAGO_LIST, valor_pago__isnull=False, then=F('valor_pago')),
                default=F('valor'),
                output_field=DecimalField()
            )
        elif key in ['GastoGeral', 'GastoGasolina']:
            val_expr = F('valor_total')
        else:
            # Modelos simples (GastoBase, Cheque)
            val_expr = F('valor')

        # Anota o QuerySet com 'val_cons' (Valor Consolidado) e 'data_sort'
        # Isso permite somar e ordenar direto pelo banco ou usar o valor pronto no template
        qs = qs.annotate(
            val_cons=val_expr,
            data_sort=F(campo_data)
        )

        # --- AGREGAÇÃO DE TOTAIS (SQL SUM) ---
        # Calcula os totais diretamente no banco, sem iterar em Python
        agregados = qs.aggregate(
            soma_pago=Sum(
                Case(When(status__in=STATUS_PAGO_LIST, then=F('val_cons')), default=0, output_field=DecimalField())
            ),
            soma_pendente=Sum(
                Case(When(~Q(status__in=STATUS_PAGO_LIST), then=F('val_cons')), default=0, output_field=DecimalField())
            )
        )
        
        total_pago += agregados['soma_pago'] or 0
        total_pendente += agregados['soma_pendente'] or 0
        
        # Fetch dos dados para a lista
        resultados = list(qs)
        total_registros += len(resultados)

        # Distribuição nas Listas
        if key in cat_operacional:
            list_operacional.extend(resultados)
        elif key in cat_folha:
            list_folha.extend(resultados)
        elif key in cat_comissao:
            list_comissao.extend(resultados)
        else:
            list_contas.extend(resultados)

    # 4. Ordenação em Memória (Necessária pois misturamos tabelas diferentes)
    list_contas.sort(key=sort_key, reverse=True)
    list_operacional.sort(key=sort_key, reverse=True)
    list_folha.sort(key=sort_key, reverse=True)
    list_comissao.sort(key=sort_key, reverse=True)

    # 5. Paginação
    def paginar_lista(lista, page_param, per_page=50):
        paginator = Paginator(lista, per_page)
        page_number = request.GET.get(page_param)
        try:
            return paginator.page(page_number)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    page_contas = paginar_lista(list_contas, 'p_contas')
    page_operacional = paginar_lista(list_operacional, 'p_ops')
    page_folha = paginar_lista(list_folha, 'p_folha')
    page_comissao = paginar_lista(list_comissao, 'p_com')
    
    form_selecao = TipoGastoForm()

    return render(request, 'core/financeiro/pagar/list.html', {
        'list_contas': page_contas,
        'list_operacional': page_operacional,
        'list_folha': page_folha,
        'list_comissao': page_comissao,
        
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'total_registros': total_registros,
        
        'tipos_disponiveis': MODEL_FORM_MAP.keys(),
        'form_selecao': form_selecao,
        'mes_atual': mes if mes else '',
        'ano_atual': ano if ano else '',
        'is_filtering': bool(mes and ano) 
    })

# ----------------------------------------------------
# VIEW - CRIAÇÃO
# ----------------------------------------------------

@login_required
def pagar_create(request):
    is_modal = request.GET.get('modal') == 'true' or request.POST.get('modal') == 'true'
    template_name = 'core/financeiro/pagar/form_content.html' if is_modal else 'core/financeiro/pagar/form_detalhe.html'
    title = 'Nova Conta a Pagar'

    if request.method == 'POST':
        tipo = request.POST.get('categoria')

        if tipo and tipo in MODEL_FORM_MAP:
            FormClass = MODEL_FORM_MAP[tipo]['form']
            title = MODEL_FORM_MAP[tipo]['title']
            form = FormClass(request.POST)

            if form.is_valid():
                obj = form.save(commit=False)
                
                # Lógica de Parcelamento
                qtd_parcelas = form.cleaned_data.get('parcelas')
                if qtd_parcelas and isinstance(qtd_parcelas, int) and qtd_parcelas > 1:
                    gerar_parcelas(obj, qtd_parcelas, form.cleaned_data)
                else:
                    obj.save()
                    form.save_m2m()

                return redirect('pagar:pagar_list')

            return render(request, template_name, {
                'form': form, 'title': title, 'tipo': tipo,
            })

        tipo_form = TipoGastoForm(request.POST)
        if tipo_form.is_valid():
            tipo = tipo_form.cleaned_data['categoria']
            return redirect(f"{request.path}?tipo={tipo}")

        return render(request, 'core/financeiro/pagar/form_selecao.html', {
            'tipo_form': tipo_form, 'title': title,
        })

    # GET
    tipo = request.GET.get('tipo')
    if tipo and tipo in MODEL_FORM_MAP:
        FormClass = MODEL_FORM_MAP[tipo]['form']
        form = FormClass()
        return render(request, template_name, {
            'form': form, 'title': MODEL_FORM_MAP[tipo]['title'], 'tipo': tipo, 
        })

    return render(request, 'core/financeiro/pagar/form_selecao.html', {
        'tipo_form': TipoGastoForm(), 'title': 'Nova Conta a Pagar - Seleção',
    })

# ----------------------------------------------------
# EDITAR / DELETAR
# ----------------------------------------------------

@login_required
def pagar_edit(request, pk):
    tipo = request.GET.get('tipo') 
    # Correção: O tipo é mandatório agora para evitar colisão de IDs
    found = _get_gasto_object_info(pk, tipo=tipo)
    
    if not found: 
        messages.error(request, "Registro não encontrado ou tipo inválido.")
        return redirect('pagar:pagar_list')
        
    ModelClass, obj, FormClass, title = found

    if request.method == 'POST':
        form = FormClass(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('pagar:pagar_list')
    else:
        form = FormClass(instance=obj)

    return render(request, 'core/financeiro/pagar/form_detalhe.html', {
        'form': form, 'title': f'Editar {title}', 'object': obj,
    })

@login_required
def pagar_delete(request, pk):
    tipo = request.GET.get('tipo')
    found = _get_gasto_object_info(pk, tipo=tipo)
    
    if not found: 
        messages.error(request, "Registro não encontrado.")
        return redirect('pagar:pagar_list')
        
    ModelClass, obj, _, title = found

    if request.method == 'POST':
        obj.delete()
        messages.success(request, f"{title} excluído com sucesso.")
        return redirect('pagar:pagar_list')

    return render(request, 'core/financeiro/pagar/delete.html', {
        'object': obj, 'title': f'Excluir {title}',
    })

# ----------------------------------------------------
# VIEWS ESPECÍFICAS (FOLHA, ETC)
# ----------------------------------------------------

@login_required
def folha_mensal_view(request):
    hoje = date.today()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    
    gerar_folha_mensal(mes, ano)
    
    data_ref = date(ano, mes, 1)
    
    queryset = FolhaPagamento.objects.filter(
        data_referencia=data_ref
    ).select_related('funcionario').order_by('funcionario__nome')

    FolhaFormSet = modelformset_factory(
        FolhaPagamento,
        fields=('salario_real', 'adiantamento', 'empreitada', 'vale', 'horas_extras_valor', 'decimo_terceiro','referencia_holerite', 'observacoes', 'status'),
        extra=0,
        widgets={
            'salario_real': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'adiantamento': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'empreitada': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'vale': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'horas_extras_valor': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01', 'readonly': 'readonly'}),
            'decimo_terceiro': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': '0.01'}),
            'referencia_holerite': forms.TextInput(attrs={'class': 'form-control form-control-sm text-center p-0', 'style': 'width: 50px;'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }
    )
    
    if request.method == 'POST':
        formset = FolhaFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Folha atualizada!")
            return redirect(f"{request.path}?mes={mes}&ano={ano}")
    else:
        formset = FolhaFormSet(queryset=queryset)

    # Cálculo do total também otimizado para evitar loop python desnecessário se não precisar
    # Mas aqui o queryset é pequeno (número de funcionários), então sum() é aceitável.
    total_liquido = sum(item.total_funcionario for item in queryset)

    lista_meses = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ]
    ano_base = hoje.year
    lista_anos = range(ano_base - 2, ano_base + 5)

    return render(request, 'core/financeiro/pagar/folha_mensal.html', {
        'formset': formset,
        'mes_atual': mes,
        'ano_atual': ano,
        'total_liquido': total_liquido,
        'meses': lista_meses,
        'anos': lista_anos,
        'title': f'Espelho da Folha - {mes}/{ano}'
    })

@login_required
def folha_pagar_todos(request):
    mes = int(request.GET.get('mes'))
    ano = int(request.GET.get('ano'))
    data_ref = date(ano, mes, 1)
    
    count = FolhaPagamento.objects.filter(data_referencia=data_ref).update(status='Pago')
    
    messages.success(request, f"{count} pagamentos marcados como 'Pago'!")
    return redirect(f"/pagar/folha/?mes={mes}&ano={ano}")

@login_required
def folha_exportar_excel(request):
    from apps.relatorios.services.follha_pagamento import FuncionarioFolhaExcelService
    
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))
    data_ref = date(ano, mes, 1)
    
    pagamentos = FolhaPagamento.objects.filter(data_referencia=data_ref).order_by('funcionario__nome')
    excel_file = FuncionarioFolhaExcelService.gerar_relatorio_folha(pagamentos)
    
    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Folha_{mes}_{ano}.xlsx'
    return response

@login_required
def folha_fechar_mes(request):
    mes = int(request.GET.get('mes'))
    ano = int(request.GET.get('ano'))
    data_ref = date(ano, mes, 1)

    try:
        with transaction.atomic():
            FolhaPagamento.objects.filter(data_referencia=data_ref).update(status='Pago')

            if mes == 12:
                prox_mes = 1
                prox_ano = ano + 1
            else:
                prox_mes = mes + 1
                prox_ano = ano

            gerar_folha_mensal(prox_mes, prox_ano)

            from apps.relatorios.services.follha_pagamento import FuncionarioFolhaExcelService
            pagamentos = FolhaPagamento.objects.filter(data_referencia=data_ref).select_related('funcionario', 'funcionario__dados_trabalhistas').order_by('funcionario__nome')
            excel_file = FuncionarioFolhaExcelService.gerar_relatorio_folha(pagamentos)

    except Exception as e:
        return HttpResponse(f"Erro ao fechar mês: {str(e)}", status=500)

    response = HttpResponse(excel_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"Folha_FECHAMENTO_{mes:02d}_{ano}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

# ----------------------------------------------------
# HOLERITES
# ----------------------------------------------------

def _preparar_dados_holerite(folha, tipo_holerite):
    funcionario = folha.funcionario
    mes = folha.data_referencia.month
    ano = folha.data_referencia.year
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    
    if tipo_holerite == 'adiantamento':
        titulo = "RECIBO DE ADIANTAMENTO SALARIAL"
        data_pagamento = date(ano, mes, 15) 
    elif tipo_holerite == '13':
        titulo = "RECIBO DE 13º SALÁRIO"
        data_pagamento = date(ano, mes, 20) 
    elif tipo_holerite == 'ferias':
        titulo = "RECIBO DE FÉRIAS"
        data_pagamento = date.today() 
    else: 
        titulo = "RECIBO DE PAGAMENTO DE SALÁRIO"
        data_pagamento = date(ano, mes, ultimo_dia)

    try:
        dados_trab = funcionario.dados_trabalhistas
        cbo = dados_trab.cbo
        funcao = dados_trab.funcao
        admissao = dados_trab.data_admissao_contabilidade.strftime('%d/%m/%Y')
    except:
        cbo = ""
        funcao = "Não Informado"
        admissao = ""

    eventos = []
    
    if tipo_holerite == 'adiantamento':
        if folha.adiantamento <= 0: return None
        eventos.append({'codigo': '001', 'descricao': 'ADIANTAMENTO SALARIAL', 'ref': '', 'vencimento': float(folha.adiantamento), 'desconto': 0.0})

    elif tipo_holerite == '13':
        if folha.decimo_terceiro <= 0: return None
        eventos.append({'codigo': '004', 'descricao': '13º SALÁRIO', 'ref': '', 'vencimento': float(folha.decimo_terceiro), 'desconto': 0.0})

    elif tipo_holerite == 'ferias':
        if folha.ferias_terco <= 0: return None
        eventos.append({'codigo': '003', 'descricao': '1/3 FÉRIAS CONSTITUCIONAL', 'ref': '', 'vencimento': float(folha.ferias_terco), 'desconto': 0.0})

    else: 
        if folha.salario_real > 0:
            eventos.append({'codigo': '001', 'descricao': 'SALÁRIO BASE', 'ref': folha.referencia_holerite or '30d', 'vencimento': float(folha.salario_real), 'desconto': 0.0})
        if folha.empreitada > 0:
            eventos.append({'codigo': '005', 'descricao': 'PRODUTIVIDADE / EMPREITADA', 'ref': '', 'vencimento': float(folha.empreitada), 'desconto': 0.0})
        if folha.horas_extras_valor > 0:
            eventos.append({'codigo': '002', 'descricao': 'HORAS EXTRAS', 'ref': '', 'vencimento': float(folha.horas_extras_valor), 'desconto': 0.0})
        if folha.adiantamento > 0:
            eventos.append({'codigo': '101', 'descricao': 'ADIANTAMENTO SALARIAL', 'ref': '', 'vencimento': 0.0, 'desconto': float(folha.adiantamento)})
        if folha.vale > 0:
            eventos.append({'codigo': '102', 'descricao': 'VALES / OUTROS DESCONTOS', 'ref': '', 'vencimento': 0.0, 'desconto': float(folha.vale)})

    total_vencimentos = sum(e['vencimento'] for e in eventos)
    total_descontos = sum(e['desconto'] for e in eventos)
    valor_liquido = total_vencimentos - total_descontos

    return {
        'empregador': {'nome': 'ZIRK MOVEIS E DECORAÇÕES LTDA', 'cnpj': '08.938.626/0001-55', 'endereco': 'Endereço da Empresa'},
        'funcionario': {'codigo': str(funcionario.id), 'nome': funcionario.nome.upper(), 'cbo': cbo, 'cargo': funcao.upper(), 'admissao': admissao},
        'cabecalho': {'titulo': titulo, 'referencia': folha.data_referencia.strftime('%m/%Y')},
        'eventos': eventos,
        'totais': {'bruto': total_vencimentos, 'descontos': total_descontos, 'liquido': valor_liquido},
        'bases': {'salario_base': float(folha.salario_real), 'inss_base': float(folha.salario_real), 'fgts_base': float(folha.salario_real), 'fgts_mes': 0.0, 'irrf_base': 0.0},
        'data_pagamento': data_pagamento
    }

@login_required
def baixar_holerite_view(request, pk):
    folha = get_object_or_404(FolhaPagamento, pk=pk)
    tipo_holerite = request.GET.get('tipo', 'mensal')
    dados = _preparar_dados_holerite(folha, tipo_holerite)
    
    if not dados:
        messages.warning(request, f"Sem dados para {tipo_holerite}.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    output = io.BytesIO()
    service = HoleriteExcelService(output)
    service.adicionar_holerite(dados, nome_aba="Holerite")
    service.close()
    
    output.seek(0)
    filename = f"Holerite_{tipo_holerite}_{folha.funcionario.nome.split()[0]}.xlsx"
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def baixar_holerite_lote_view(request):
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    tipo_holerite = request.GET.get('tipo', 'mensal')
    
    if not mes or not ano:
        messages.error(request, "Mês e Ano obrigatórios.")
        return redirect('pagar:folha_mensal')

    folhas = FolhaPagamento.objects.filter(
        data_referencia__year=ano, data_referencia__month=mes, is_deleted=False
    ).select_related('funcionario', 'funcionario__dados_trabalhistas').order_by('funcionario__nome')

    lista_dados = []
    for folha in folhas:
        dados = _preparar_dados_holerite(folha, tipo_holerite)
        if dados:
            lista_dados.append((dados, folha.funcionario.nome.split()[0]))

    if not lista_dados:
        messages.warning(request, "Nenhum dado encontrado.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    output = io.BytesIO()
    service = HoleriteExcelService(output)
    used_names = set()
    
    for i in range(0, len(lista_dados), 2):
        d1, n1 = lista_dados[i]
        d2, n2 = (None, "")
        base_name = f"{n1}"
        
        if i + 1 < len(lista_dados):
            d2, n2 = lista_dados[i + 1]
            base_name = f"{n1} e {n2}"

        if len(base_name) > 28:
            base_name = base_name[:28]
            
        nome_aba = base_name
        counter = 1
        while nome_aba.lower() in used_names:
            counter += 1
            suffix = f" {counter}"
            nome_aba = f"{base_name[:31-len(suffix)]}{suffix}"
            
        used_names.add(nome_aba.lower())
        service.adicionar_holerite_duplo(d1, d2, nome_aba=nome_aba)

    service.close()
    
    output.seek(0)
    filename = f"Lote_Holerites_{tipo_holerite}_{mes}-{ano}.xlsx"
    
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response