from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
# --- Adicione estes imports no topo se não existirem ---
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q  
from django.shortcuts import get_object_or_404, redirect, render

from apps.banco_horas.models import LancamentoHoras
# --- IMPORTS ---
from apps.clientes.models import Cliente
from apps.comissionamento.models import Arquiteta, ContratoRT
from apps.dashboard.models import PerfilUsuario
from apps.empreitadas.models import Empreitada, PagamentoEmpreitada
from apps.ferias.models import Ferias, PagamentoFerias
from apps.financeiro.pagar.models import Emprestimo  # Importar Emprestimo
from apps.financeiro.pagar.models import (Boleto, Cheque, ComissaoArquiteto,
                                          FaturaCartao, FolhaPagamento,
                                          GastoContabilidade, GastoGasolina,
                                          GastoGeral, GastoImovel,
                                          GastoUtilidade,
                                          GastoVeiculoConsorcio,
                                          PrestacaoEmprestimo)
from apps.financeiro.receber.models import CaixaDiario  # Importar CaixaDiario
from apps.financeiro.receber.models import MovimentoBanco, Receber
from apps.funcionarios.models import Funcionario
from apps.rescisao.models import Rescisao
from apps.socios.models import (  # Certifique-se que LancamentoSocio está importado
    LancamentoSocio, Socio)

from .forms import AdminCreationForm  # Importe o novo form
from .forms import ConfiguracaoGlobalForm
from .models import ConfiguracaoGlobal

# from apps.socios.models import Socio


def is_admin(user):
    return user.is_superuser or user.is_staff
# ... Mantenha o código existente ...

# ... (Imports existentes)
from django.contrib.auth.models import User

# ...

@login_required
@user_passes_test(is_admin)
def criar_novo_admin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            # ... (Lógica de salvamento mantém-se igual) ...
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            cpf = form.cleaned_data['cpf']
            cpf_limpo = ''.join(filter(str.isdigit, cpf))

            if User.objects.filter(username=username).exists():
                messages.error(request, "⚠️ Este nome de usuário já existe.")
            else:
                try:
                    user = User.objects.create_user(username=username, password=password)
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                    
                    PerfilUsuario.objects.create(user=user, cpf=cpf_limpo)
                    
                    messages.success(request, f"✅ Admin {username} criado com sucesso!")
                    return redirect('configuracoes:criar_novo_admin')
                except Exception as e:
                    messages.error(request, f"Erro ao criar admin: {e}")
    else:
        form = AdminCreationForm()

    # --- ALTERADO: Busca Superusuários OU Staff (Membros da equipe) ---
    admins = User.objects.filter(Q(is_superuser=True) | Q(is_staff=True)).order_by('username')

    return render(request, 'core/configuracoes/criar_admin.html', {
        'form': form,
        'admins': admins
    })
# ... (Restante do arquivo permanece igual)

@login_required
@user_passes_test(is_admin)
def dashboard_lixeira(request):
    mapa_categorias = {
        'cadastros': [ # Sugestão de nova categoria para organizar melhor
            ('Clientes', Cliente),
            ('Funcionários', Funcionario),
            ('Sócios', Socio),
            ('Arquitetos Parceiros', Arquiteta),
        ],
        'financeiro': [
            ('Receitas / Recibos', Receber),
            ('Movimentações Bancárias', MovimentoBanco),
            ('Caixa Diário', CaixaDiario), # <--- NOVO
            ('Contratos RT', ContratoRT),
            ('Comissões Pagas', ComissaoArquiteto),
            ('Boletos', Boleto),
            ('Gastos Gerais', GastoGeral),
            ('Contas de Consumo', GastoUtilidade),
            ('Cartões de Crédito', FaturaCartao),
            ('Imóveis', GastoImovel),
            ('Veículos', GastoVeiculoConsorcio),
            ('Impostos', GastoContabilidade),
            ('Contratos de Empréstimo', Emprestimo), # <--- NOVO
            ('Prestações de Empréstimo', PrestacaoEmprestimo),
            ('Combustível', GastoGasolina),
            ('Cheques', Cheque),
            ('Lançamentos de Sócios', LancamentoSocio), # <--- NOVO
        ],
        'rh': [
            ('Folha de Pagamento', FolhaPagamento),
            ('Férias (Períodos)', Ferias),
            ('Pagamentos de Férias', PagamentoFerias), # <--- NOVO
            ('Rescisões', Rescisao),
            ('Banco de Horas (Lançamentos)', LancamentoHoras), # <--- NOVO
        ],
        'obras': [ # Sugestão de categoria para empreitadas
            ('Empreitadas', Empreitada), # <--- NOVO
            ('Pagamentos de Empreitada', PagamentoEmpreitada), # <--- NOVO
        ]
    }
    
    resumo = { 'cadastros': [], 'financeiro': [], 'rh': [], 'obras': [] } # Adicione as novas chaves aqui
    total_geral = 0
    
    for categoria, lista_models in mapa_categorias.items():
        # Garante que a chave existe no resumo (caso adicione mais categorias)
        if categoria not in resumo: 
            resumo[categoria] = []
            
        for nome_amigavel, model_class in lista_models:
            if model_class and hasattr(model_class, 'trash'):
                qtd = model_class.trash.count()
                if qtd > 0:
                    resumo[categoria].append({
                        'nome': nome_amigavel,
                        'model_key': f"{model_class._meta.app_label}.{model_class._meta.model_name}",
                        'qtd': qtd
                    })
                    total_geral += qtd

    return render(request, 'core/configuracoes/lixeira_dashboard.html', {
        'resumo': resumo,
        'total_geral': total_geral
    })
# ... (As funções lixeira_itens, restaurar_item, deletar_permanente e editar_configuracoes continuam iguais) ...
@login_required
@user_passes_test(is_admin)
def lixeira_itens(request, model_key):
    try:
        app_label, model_name = model_key.split('.')
        model = apps.get_model(app_label, model_name)
    except (LookupError, ValueError):
        messages.error(request, "Modelo inválido.")
        return redirect('configuracoes:lixeira_dashboard')

    if not hasattr(model, 'trash'):
        messages.error(request, "Lixeira não habilitada para este item.")
        return redirect('configuracoes:lixeira_dashboard')

    itens_list = model.trash.all().order_by('-deleted_at')
    paginator = Paginator(itens_list, 20)
    itens = paginator.get_page(request.GET.get('page'))

    return render(request, 'core/configuracoes/lixeira_itens.html', {
        'itens': itens,
        'verbose_name': model._meta.verbose_name_plural.title(),
        'model_key': model_key
    })

@login_required
@user_passes_test(is_admin)
def restaurar_item(request, model_key, pk):
    try:
        app_label, model_name = model_key.split('.')
        model = apps.get_model(app_label, model_name)
        item = model.trash.get(pk=pk)
        item.restore()
        messages.success(request, "Restaurado com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro: {e}")
    return redirect('configuracoes:lixeira_itens', model_key=model_key)

@login_required
@user_passes_test(is_admin)
def deletar_permanente(request, model_key, pk):
    try:
        app_label, model_name = model_key.split('.')
        model = apps.get_model(app_label, model_name)
        item = model.trash.get(pk=pk)
        item.hard_delete()
        messages.success(request, "Excluído permanentemente.")
    except Exception as e:
        messages.error(request, f"Erro: {e}")
    return redirect('configuracoes:lixeira_itens', model_key=model_key)

@login_required
@user_passes_test(is_admin)
def editar_configuracoes(request):
    config, _ = ConfiguracaoGlobal.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ConfiguracaoGlobalForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Salvo!")
            return redirect('configuracoes:lixeira_dashboard')
    else:
        form = ConfiguracaoGlobalForm(instance=config)
    return render(request, 'core/configuracoes/editar.html', {'form': form})


# ... (imports existentes e outras views)

@login_required
@user_passes_test(is_admin)
def acoes_lixeira_em_massa(request, model_key):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        item_ids = request.POST.getlist('item_ids')
        
        if not item_ids:
            messages.warning(request, "Nenhum item selecionado.")
            return redirect('configuracoes:lixeira_itens', model_key=model_key)

        try:
            app_label, model_name = model_key.split('.')
            model = apps.get_model(app_label, model_name)
            
            # Busca os itens na lixeira
            itens = model.trash.filter(pk__in=item_ids)
            qtd = itens.count()

            if acao == 'restaurar':
                for item in itens:
                    item.restore()
                messages.success(request, f"✅ {qtd} itens restaurados com sucesso!")
            
            elif acao == 'excluir':
                for item in itens:
                    item.hard_delete()
                messages.success(request, f"🗑️ {qtd} itens excluídos permanentemente.")
                
        except Exception as e:
            messages.error(request, f"Erro ao processar ação: {e}")
            
    return redirect('configuracoes:lixeira_itens', model_key=model_key)

@login_required
@user_passes_test(is_admin)
def esvaziar_lixeira(request, model_key):
    try:
        app_label, model_name = model_key.split('.')
        model = apps.get_model(app_label, model_name)
        
        itens = model.trash.all()
        qtd = itens.count()
        
        if qtd > 0:
            for item in itens:
                item.hard_delete()
            messages.success(request, f"✅ Lixeira esvaziada! {qtd} itens foram removidos.")
        else:
            messages.info(request, "A lixeira já está vazia.")
            
    except Exception as e:
        messages.error(request, f"Erro ao esvaziar lixeira: {e}")
        
    return redirect('configuracoes:lixeira_itens', model_key=model_key)

