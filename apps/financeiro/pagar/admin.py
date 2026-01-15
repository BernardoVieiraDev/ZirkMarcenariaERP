from typing import Tuple

from django.contrib import admin

from .models import (
    Boleto,
    GastoVeiculoConsorcio,
    GastoUtilidade,
    FaturaCartao,
    PrestacaoEmprestimo,
    GastoContabilidade,
    GastoImovel,
    Cheque,
    Emprestimo,
    Pessoa,
    PagamentoFuncionario,
    ComissaoArquiteto,
    GastoGeral,
    GastoGasolina,
    FolhaPagamento,
)

# ==============================================================================
# CONSTANTES TIPADAS (EVITA ERRO DO PYLANCE)
# ==============================================================================

GASTO_BASE_LIST_DISPLAY: Tuple[str, ...] = (
    "get_model_name",
    "credor",
    "descricao",
    "valor",
    "data_vencimento",
    "status",
    "forma_pagamento",
    "is_deleted",
)

# ==============================================================================
# AÇÃO GLOBAL PARA RESTAURAR (Soft Delete)
# ==============================================================================

@admin.action(description="Restaurar registros selecionados da Lixeira")
def restaurar_registros(modeladmin, request, queryset):
    queryset.update(is_deleted=False, deleted_at=None)


# ==============================================================================
# ADMIN BASE PARA MODELOS COM SOFT DELETE
# ==============================================================================

class SoftDeleteAdmin(admin.ModelAdmin):
    list_filter = ("is_deleted",)
    actions = (restaurar_registros,)

    def get_queryset(self, request):
        # Mostra tudo (ativos + lixeira)
        return self.model.all_objects.all()


# ==============================================================================
# ADMIN BASE PARA GASTOS (HERDAM DE GastoBase)
# ==============================================================================

class GastoBaseAdmin(SoftDeleteAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY
    list_filter = ("status", "forma_pagamento", "is_deleted")
    search_fields = ("credor", "descricao")
    ordering = ("-data_vencimento",)


# ==============================================================================
# ADMINS ESPECÍFICOS (HERDAM DE GASTO BASE)
# ==============================================================================

@admin.register(Boleto)
class BoletoAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + (
        "data_pagamento",
        "valor_pago",
        "juros",
    )


@admin.register(GastoVeiculoConsorcio)
class GastoVeiculoConsorcioAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + (
        "tipo_gasto",
        "veiculo_referencia",
    )


@admin.register(GastoUtilidade)
class GastoUtilidadeAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + ("tipo_cliente",)


@admin.register(FaturaCartao)
class FaturaCartaoAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + ("cartao",)


@admin.register(PrestacaoEmprestimo)
class PrestacaoEmprestimoAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + ("prestacao",)


@admin.register(GastoContabilidade)
class GastoContabilidadeAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + ("tipo_gasto",)


@admin.register(GastoImovel)
class GastoImovelAdmin(GastoBaseAdmin):
    list_display = GASTO_BASE_LIST_DISPLAY + (
        "tipo_gasto",
        "local_lote",
        "numero_inscricao",
    )


# ==============================================================================
# MODELOS INDEPENDENTES (SOFT DELETE)
# ==============================================================================

@admin.register(Cheque)
class ChequeAdmin(SoftDeleteAdmin):
    list_display = (
        "numero_cheque",
        "descricao",
        "valor",
        "data_emissao",
        "status",
        "is_deleted",
    )
    list_filter = ("status", "is_deleted")
    search_fields = ("numero_cheque", "descricao")


@admin.register(ComissaoArquiteto)
class ComissaoArquitetoAdmin(SoftDeleteAdmin):
    list_display = (
        "arquiteto",
        "data_pagamento",
        "valor_comissao",
        "forma_pagamento",
        "status",
        "is_deleted",
    )
    list_filter = ("status", "forma_pagamento", "is_deleted")


@admin.register(GastoGeral)
class GastoGeralAdmin(SoftDeleteAdmin):
    list_display = (
        "descricao",
        "credor",
        "data_gasto",
        "valor_total",
        "forma_principal_pagamento",
        "status",
        "is_deleted",
    )
    list_filter = ("status", "forma_principal_pagamento", "is_deleted")


@admin.register(GastoGasolina)
class GastoGasolinaAdmin(SoftDeleteAdmin):
    list_display = (
        "descricao",
        "data_gasto",
        "valor_total",
        "carro",
        "status",
        "is_deleted",
    )


@admin.register(FolhaPagamento)
class FolhaPagamentoAdmin(SoftDeleteAdmin):
    list_display = (
        "funcionario",
        "data_referencia",
        "total_funcionario",
        "forma_pagamento",
        "status",
        "is_deleted",
    )
    list_filter = ("status", "forma_pagamento", "is_deleted")
    ordering = ("-data_referencia",)


# ==============================================================================
# MODELOS SIMPLES (SEM SOFT DELETE)
# ==============================================================================

@admin.register(Emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "valor_total",
        "data_inicio",
        "data_final_prevista",
    )


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "cargo", "salario_base")
    search_fields = ("nome",)


@admin.register(PagamentoFuncionario)
class PagamentoFuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        "funcionario",
        "mes_referencia",
        "total_liquido",
    )
    ordering = ("-mes_referencia",)
