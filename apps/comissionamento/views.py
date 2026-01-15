# Em apps/comissionamento/views.py
import uuid
from decimal import Decimal

from dateutil.relativedelta import relativedelta  # pip install python-dateutil
from django.contrib import messages
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.financeiro.pagar.models import ComissaoArquiteto, StatusPagamento
from apps.financeiro.receber.models import Banco  # <--- Importe o Banco aqui
from apps.financeiro.receber.models import Receber

from .forms import ArquitetaForm, ContratoRTForm
from .models import Arquiteta, ContratoRT

# --- VIEWS DE CONTRATOS (Agora Unificadas) ---


# ... (Mantenha as views de Arquiteta iguais) ...

# === VIEWS DE CONTRATO E FINANCEIRO ===

def rt_contratos_list(request):
    contratos = ContratoRT.objects.filter(is_deleted=False).select_related('arquiteta', 'cliente').order_by('-data_contrato')
    
    # NOVOS DADOS PARA O MODAL
    # Pegamos apenas bancos ativos
    bancos = Banco.objects.all()
    # Pegamos as opções de categoria definidas no Model Receber dinamicamente
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
        'categorias': categorias,
        'total_pago': total_pago,  
        'total_rt': total_rt, 
        'title': 'Gestão de Contratos e Comissões',
    }
    return render(request, 'core/comissionamento/contratos_list.html', context)


# Em zirk_rh_financeiro/apps/comissionamento/views.py

def rt_contrato_create(request):
    if request.method == 'POST':
        form = ContratoRTForm(request.POST)
        if form.is_valid():
            # 1. Salva o Contrato
            contrato = form.save()
            
            # 2. Verifica se o usuário quer gerar o financeiro
            valor_rt = contrato.valor_rt or Decimal('0.00')
            
            if form.cleaned_data.get('gerar_financeiro') and valor_rt > 0:
                try:
                    banco = form.cleaned_data.get('banco_pagamento')
                    qtd_parcelas = form.cleaned_data.get('qtd_parcelas') or 1
                    
                    data_base = form.cleaned_data.get('primeiro_vencimento') 
                    if not data_base:
                        data_base = contrato.data_contrato or timezone.now().date()
                        
                    forma_pagto = form.cleaned_data.get('forma_pagamento')
                    
                    valor_total = valor_rt
                    valor_parcela = (valor_total / qtd_parcelas).quantize(Decimal('0.01'))
                    grupo_uuid = uuid.uuid4()
                    
                    for i in range(qtd_parcelas):
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
                            
                            # === CORREÇÃO AQUI ===
                            # Antes estava data_pagamento=data_venc. 
                            # Agora o campo obrigatório é data_vencimento.
                            data_vencimento=data_venc, 
                            
                            # data_pagamento (real) fica vazio pois nasce Pendente
                            data_pagamento=None, 
                            # =====================

                            banco_origem=banco,
                            forma_pagamento=forma_pagto,
                            status=StatusPagamento.PENDENTE,
                            parcelamento_uuid=grupo_uuid,
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
            descricao_personalizada = request.POST.get('descricao_personalizada') # Opcional: para mudar o nome "Ref. Contrato..."

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

                # Define a descrição (Nome do projeto ou padrão)
                if descricao_personalizada:
                    desc_final = f"{descricao_personalizada} - {i+1}/{qtd_parcelas}"
                else:
                    desc_final = f"Proj. {contrato.cliente.nome_completo} - Parc {i+1}/{qtd_parcelas}"

                nova_conta = Receber(
                    descricao=desc_final,
                    cliente=contrato.cliente, # <--- Passe o objeto direto (remova o .nome_completo)
                    
                    # AQUI USAMOS OS DADOS SELECIONADOS PELO USUÁRIO
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

def painel_controle_rt(request):
    """
    Dashboard para Arquiteto ver o status de seus clientes.
    """
    # Busca contratos com os relacionamentos necessários
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

# --- VIEWS DE ARQUITETA (Sem alterações lógicas) ---
def arquiteta_list(request):
    arquitetas = Arquiteta.objects.all().order_by('nome')
    form = ArquitetaForm()

    context = {
        'arquitetas': arquitetas,
        'form': form,  
        'title': 'Cadastro de Arquitetas'
    }
    return render(request, 'core/comissionamento/arquiteta_list.html', context)
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

def arquiteta_delete(request, pk):
    arquiteta = get_object_or_404(Arquiteta, pk=pk)
    # Verifica dependência com o novo modelo ContratoRT
    if arquiteta.contratort_set.exists():
        messages.error(request, "Não é possível excluir: existem registros vinculados a esta arquiteta.")
        return redirect('comissionamento:arquiteta_list')
        
    if request.method == 'POST':
        arquiteta.delete()
        messages.success(request, "Arquiteta excluída com sucesso.")
        return redirect('comissionamento:arquiteta_list')
    context = {'arquiteta': arquiteta, 'title': f'Excluir Arquiteta: {arquiteta.nome}'}
    return render(request, 'core/comissionamento/arquiteta_delete.html', context)


def rt_contrato_detail(request, pk):
    contrato = get_object_or_404(ContratoRT, pk=pk)
    
    # Busca todas as parcelas vinculadas a este contrato no Financeiro
    # O 'related_name' definido no model Receber é 'parcelas_receber'
    parcelas = contrato.parcelas_receber.all().order_by('data_vencimento')

    # Cálculos para o Dashboard rápido
    total_gerado = contrato.total_previsto_financeiro
    total_recebido = contrato.total_recebido
    saldo_restante = total_gerado - total_recebido

    context = {
        'contrato': contrato,
        'parcelas': parcelas,
        'total_gerado': total_gerado,
        'total_recebido': total_recebido,
        'saldo_restante': saldo_restante,
        'title': f'Detalhes: {contrato.cliente}'
    }
    return render(request, 'core/comissionamento/contrato_detail.html', context)

