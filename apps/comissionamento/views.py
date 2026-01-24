# apps/comissionamento/views.py

import uuid
from decimal import Decimal

from dateutil.relativedelta import relativedelta  # pip install python-dateutil
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

# --- MUDANÇA 1: Adicionada a importação de ParcelamentoPagar ---
from apps.financeiro.pagar.models import ComissaoArquiteto, StatusPagamento, ParcelamentoPagar
from apps.financeiro.receber.models import Banco
from apps.financeiro.receber.models import Receber

from .forms import ArquitetaForm, ContratoRTForm
from .models import Arquiteta, ContratoRT

# === VIEWS DE CONTRATO E FINANCEIRO ===

# zirk_rh_financeiro/apps/comissionamento/views.py

@login_required
def rt_contratos_list(request):
    contratos = ContratoRT.objects.filter(is_deleted=False)\
        .select_related('arquiteta', 'cliente')\
        .prefetch_related('comissoes_pagar__banco_origem')\
        .order_by('-data_contrato')    
    # DADOS PARA O MODAL
    bancos = Banco.objects.all()
    # --- CORREÇÃO AQUI: Buscando as arquitetas para o dropdown ---
    arquitetas = Arquiteta.objects.all().order_by('nome') 
    # -----------------------------------------------------------
    categorias = Receber._meta.get_field('categoria').choices
    
    total_rt = contratos.aggregate(
        total=Sum('valor_rt')
    )['total'] or Decimal('0.00')
    
    total_pago = ContratoRT.objects.filter(
        is_deleted=False,
        parcelas_receber__status='Recebido'
    ).aggregate(
        total=Sum('parcelas_receber__valor_recebido')
    )['total'] or Decimal('0.00')
    
    context = {
        'contratos': contratos,
        'bancos': bancos,
        'arquitetas': arquitetas,  # <--- ADICIONE ESTA LINHA
        'categorias': categorias,
        'total_pago': total_pago,  
        'total_rt': total_rt, 
        'title': 'Gestão de Contratos e Comissões',
    }
    return render(request, 'core/comissionamento/contratos_list.html', context)


@login_required
def rt_contrato_create(request):
    if request.method == 'POST':
        form = ContratoRTForm(request.POST)
        if form.is_valid():
            # 1. Salva o Contrato
            contrato = form.save()
            
            # 2. Verifica se o usuário quer gerar o financeiro
            valor_rt = contrato.valor_rt or Decimal('0.00')
            gerar_fin = form.cleaned_data.get('gerar_financeiro')

            if gerar_fin and valor_rt > 0:
                try:
                    banco = form.cleaned_data.get('banco_pagamento')
                    
                    # CORREÇÃO/DEBUG: Tenta pegar do cleaned_data, se falhar tenta direto do POST
                    qtd_input = form.cleaned_data.get('qtd_parcelas')
                    if not qtd_input:
                        try:
                            qtd_input = int(request.POST.get('qtd_parcelas', 1))
                        except ValueError:
                            qtd_input = 1
                    
                    qtd_parcelas = qtd_input if qtd_input and qtd_input > 0 else 1
                    
                    # Log para verificar no terminal do servidor
                    print(f"DEBUG: Gerando financeiro. Parcelas: {qtd_parcelas} | Valor RT: {valor_rt}")

                    data_base = form.cleaned_data.get('primeiro_vencimento') 
                    if not data_base:
                        data_base = contrato.data_contrato or timezone.now().date()
                        
                    forma_pagto = form.cleaned_data.get('forma_pagamento')
                    
                    valor_total = valor_rt
                    valor_parcela = (valor_total / qtd_parcelas).quantize(Decimal('0.01'))
                    
                    # Criação do ParcelamentoPagar (Pai)
                    grupo_parcelamento = None
                    if qtd_parcelas > 1:
                        grupo_parcelamento = ParcelamentoPagar.objects.create(
                            descricao=f"",
                            valor_total_original=valor_total,
                            qtd_parcelas=qtd_parcelas
                        )

                    for i in range(qtd_parcelas):
                        # Ajuste de centavos na última parcela
                        if i == qtd_parcelas - 1:
                            valor_atual = valor_total - (valor_parcela * (qtd_parcelas - 1))
                        else:
                            valor_atual = valor_parcela
                            
                        data_venc = data_base + relativedelta(months=i)
                        desc_parcela = f"Comissão {contrato.cliente} ({i+1}/{qtd_parcelas})"
                        
                        nova_comissao = ComissaoArquiteto(
                            arquiteto=contrato.arquiteta,
                            contrato_rt=contrato,
                            valor_comissao=valor_atual,
                            data_vencimento=data_venc, 
                            data_pagamento=None,
                            banco_origem=banco,
                            forma_pagamento=forma_pagto,
                            status=StatusPagamento.PENDENTE,
                            parcelamento=grupo_parcelamento,
                            observacoes=desc_parcela
                        )
                        nova_comissao.save() 
                    
                    messages.success(request, f"Contrato salvo e {qtd_parcelas} parcela(s) de comissão gerada(s)!")
                    
                except Exception as e:
                    print(f"ERRO AO GERAR FINANCEIRO: {e}") 
                    messages.warning(request, f"Contrato salvo, mas erro ao gerar financeiro: {e}")
            else:
                messages.success(request, "Contrato registrado (sem financeiro gerado).")
                
            return redirect('comissionamento:contratos_list')
    else:
        form = ContratoRTForm()
        form.fields['primeiro_vencimento'].initial = timezone.now().date()

    return render(request, 'core/comissionamento/contrato_form.html', {'form': form, 'title': 'Novo Contrato'})

@login_required
def rt_contrato_edit(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    if request.method == 'POST':
        form = ContratoRTForm(request.POST, instance=contrato)
        if form.is_valid():
            form.save()
            messages.success(request, "Contrato atualizado!")
            return redirect('comissionamento:contratos_list')
    else:
        form = ContratoRTForm(instance=contrato)
    return render(request, 'core/comissionamento/contrato_form.html', {'form': form, 'title': 'Editar Contrato'})


@login_required
def gerar_financeiro_contrato(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    if request.method == 'POST':
        try:
            # Dados Básicos
            qtd_parcelas = int(request.POST.get('qtd_parcelas', 1))
            data_vencimento_str = request.POST.get('data_vencimento')
            data_base = timezone.datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
            
            # NOVOS CAMPOS CAPTURADOS
            banco_id = request.POST.get('banco_id')
            categoria_selecionada = request.POST.get('categoria')
            descricao_personalizada = request.POST.get('descricao_personalizada') 

            # Validações
            if not banco_id:
                messages.error(request, "É obrigatório selecionar um Banco.")
                return redirect('comissionamento:contratos_list')
                
            if contrato.parcelas_receber.exists():
                messages.warning(request, "Este contrato já possui financeiro gerado.")
                return redirect('comissionamento:contratos_list')

            # Busca instância do banco
            banco_obj = get_object_or_404(Banco, pk=banco_id)

            valor_total = contrato.valor_servico
            valor_parcela = (valor_total / qtd_parcelas).quantize(Decimal('0.01'))
            
            grupo_uuid = uuid.uuid4()
            recebimentos = []
            
            for i in range(qtd_parcelas):
                if i == qtd_parcelas - 1:
                    valor_atual = valor_total - (valor_parcela * (qtd_parcelas - 1))
                else:
                    valor_atual = valor_parcela

                # Define a descrição
                if descricao_personalizada:
                    desc_final = f"{descricao_personalizada} - {i+1}/{qtd_parcelas}"
                else:
                    desc_final = f"Proj. {contrato.cliente.nome_completo} - Parc {i+1}/{qtd_parcelas}"

                nova_conta = Receber(
                    descricao=desc_final,
                    cliente=contrato.cliente, 
                    
                    categoria=categoria_selecionada, 
                    banco_destino=banco_obj,
                    
                    valor=valor_atual,
                    data_vencimento=data_base + relativedelta(months=i),
                    status='Pendente',
                    tipo_recebimento='PRAZO' if qtd_parcelas > 1 else 'VISTA',
                    contrato_rt=contrato,
                    parcelamento_uuid=grupo_uuid
                )       
                recebimentos.append(nova_conta)
            
            Receber.objects.bulk_create(recebimentos)
            messages.success(request, f"Financeiro gerado no banco {banco_obj} com categoria {categoria_selecionada}!")
            
        except Exception as e:
            messages.error(request, f"Erro ao gerar: {str(e)}")
            
    return redirect('comissionamento:contratos_list')


@login_required
def painel_controle_rt(request):
    """
    Dashboard para Arquiteto ver o status de seus clientes.
    """
    contratos = ContratoRT.objects.filter(is_deleted=False)\
        .select_related('arquiteta', 'cliente')\
        .prefetch_related('parcelas_receber')\
        .order_by('arquiteta__nome')

    dados_dashboard = []
    
    for c in contratos:
        parcelas = c.parcelas_receber.all()
        total_previsto = parcelas.aggregate(Sum('valor'))['valor__sum'] or Decimal('0.00')
        total_recebido = parcelas.filter(status='Recebido').aggregate(Sum('valor_recebido'))['valor_recebido__sum'] or Decimal('0.00')
        
        pendente = total_previsto - total_recebido
        progresso = (total_recebido / total_previsto * 100) if total_previsto > 0 else 0
        
        dados_dashboard.append({
            'contrato': c,
            'status_financeiro': c.status_pagamento,
            'progresso': round(progresso, 1),
            'financeiro': {
                'total': total_previsto,
                'recebido': total_recebido,
                'falta': pendente
            }
        })

    return render(request, 'core/comissionamento/painel_rt.html', {'dados': dados_dashboard})


@login_required
def rt_contrato_delete(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    if request.method == 'POST':
        nome = contrato.cliente
        contrato.delete()
        messages.success(request, f"Registro de {nome} excluído com sucesso.")
        return redirect('comissionamento:contratos_list')
        
    context = {
        'contrato': contrato,
        'title': f'Excluir Registro: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_delete.html', context)


@login_required
def arquiteta_list(request):
    arquitetas = Arquiteta.objects.all().order_by('nome')
    form = ArquitetaForm()

    context = {
        'arquitetas': arquitetas,
        'form': form,  
        'title': 'Cadastro de Arquitetas'
    }
    return render(request, 'core/comissionamento/arquiteta_list.html', context)


@login_required
def arquiteta_create(request):
    if request.method == 'POST':
        form = ArquitetaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Arquiteta cadastrada com sucesso.")
            return redirect('comissionamento:arquiteta_list') 
    else:
        form = ArquitetaForm()
    context = {'form': form, 'title': 'Nova Arquiteta'}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)


@login_required
def arquiteta_edit(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    if request.method == 'POST':
        form = ArquitetaForm(request.POST, instance=arquiteta)
        if form.is_valid():
            form.save()
            messages.success(request, "Arquiteta atualizada com sucesso.")
            return redirect('comissionamento:arquiteta_list')
    else:
        form = ArquitetaForm(instance=arquiteta)
    context = {'form': form, 'title': f'Editar: {arquiteta.nome}', 'edit_mode': True}
    return render(request, 'core/comissionamento/arquiteta_form.html', context)


@login_required
def arquiteta_delete(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    if arquiteta.contratort_set.exists():
        messages.error(request, "Não é possível excluir: existem registros vinculados a esta arquiteta.")
        return redirect('comissionamento:arquiteta_list')
        
    if request.method == 'POST':
        arquiteta.delete()
        messages.success(request, "Arquiteta excluída com sucesso.")
        return redirect('comissionamento:arquiteta_list')
    context = {'arquiteta': arquiteta, 'title': f'Excluir Arquiteta: {arquiteta.nome}'}
    return render(request, 'core/comissionamento/arquiteta_delete.html', context)



# zirk_rh_financeiro/apps/comissionamento/views.py

# ... imports existentes ...
from django.db.models import Sum # Certifique-se que Sum está importado

@login_required
def rt_contrato_detail(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    # --- 1. Financeiro: Contas a Receber (Cliente) ---
    parcelas = contrato.parcelas_receber.all().order_by('data_vencimento')

    total_gerado = contrato.total_previsto_financeiro
    total_recebido = contrato.total_recebido
    saldo_restante = total_gerado - total_recebido

    # --- 2. Financeiro: Comissões a Pagar (Arquiteto) ---
    # Busca as comissões vinculadas (related_name='comissoes_pagar' no model ComissaoArquiteto)
    comissoes = contrato.comissoes_pagar.filter(is_deleted=False).order_by('data_vencimento')
    
    # Cálculos de Totais das Comissões
    total_comissao_previsto = comissoes.aggregate(total=Sum('valor_comissao'))['total'] or Decimal('0.00')
    
    # Soma o que já foi pago (status Pago, Recebido, etc)
    total_comissao_pago = comissoes.filter(
        status__in=['Pago', 'PG', 'Recebido', 'COM']
    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
    
    saldo_comissao = total_comissao_previsto - total_comissao_pago

    context = {
        'contrato': contrato,
        'parcelas': parcelas,
        'total_gerado': total_gerado,
        'total_recebido': total_recebido,
        'saldo_restante': saldo_restante,
        
        # Novos dados para o template
        'comissoes': comissoes,
        'total_comissao_previsto': total_comissao_previsto,
        'total_comissao_pago': total_comissao_pago,
        'saldo_comissao': saldo_comissao,
        
        'title': f'Detalhes: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_detail.html', context)