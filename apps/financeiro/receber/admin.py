from django.contrib import admin
from django.utils.html import format_html
from .models import Receber, Banco, CaixaDiario, MovimentoBanco

# ==============================================================================
# AÇÃO GLOBAL PARA RESTAURAR
# ==============================================================================
@admin.action(description="Restaurar registros selecionados da Lixeira")
def restaurar_registros(modeladmin, request, queryset):
    for obj in queryset:
        obj.restore()
    modeladmin.message_user(request, f"{queryset.count()} registros restaurados com sucesso.")

# ==============================================================================
# ADMIN BASE COM SOFT DELETE
# ==============================================================================
class SoftDeleteAdmin(admin.ModelAdmin):
    list_filter = ("is_deleted",)
    actions = [restaurar_registros]

    def get_queryset(self, request):
        # Mostra todos os objetos (ativos + lixeira)
        return self.model.all_objects.all()

    def delete_queryset(self, request, queryset):
        """
        Sobrescreve a ação padrão de deletar em massa do Admin.
        Ao invés de fazer um SQL DELETE direto (queryset.delete()),
        chama o método .delete() de cada instância para ativar o Soft Delete.
        """
        for obj in queryset:
            obj.delete()

# ==============================================================================
# ADMINS AUXILIARES
# ==============================================================================
@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'agencia', 'conta', 'saldo_inicial')

@admin.register(CaixaDiario)
class CaixaDiarioAdmin(admin.ModelAdmin):
    list_display = ('data', 'historico', 'tipo', 'valor')
    list_filter = ('tipo', 'data')
    search_fields = ('historico',)
    ordering = ('-data',)

@admin.register(MovimentoBanco)
class MovimentoBancoAdmin(SoftDeleteAdmin):
    list_display = ('banco', 'data', 'historico', 'tipo', 'valor', 'is_deleted')
    list_filter = ('tipo', 'data', 'banco', 'is_deleted')

# ==============================================================================
# ADMIN PRINCIPAL (RECEBER)
# ==============================================================================
@admin.register(Receber)
class ReceberAdmin(SoftDeleteAdmin):
    # Campos exibidos na lista
    list_display = (
        'descricao',
        'cliente',
        'categoria',
        'data_vencimento',
        'valor',
        'valor_recebido',
        'status_colorido',
        'forma_recebimento',
        'is_deleted',
    )

    # Filtros
    list_filter = (
        'status',
        'forma_recebimento',
        'tipo_recebimento',
        'data_vencimento',
        'is_deleted',
    )

    # Busca
    search_fields = (
        'descricao',
        'cliente',
        'categoria',
    )

    # Ordenação
    ordering = ('-data_vencimento',)

    # Somente leitura
    readonly_fields = (
        'parcelamento_uuid',
        'movimento_banco',
        'movimento_caixa',
        'deleted_at',
        'is_deleted',
    )

    # Organização do formulário
    fieldsets = (
        ('Informações Gerais', {
            'fields': (
                'descricao',
                'cliente',
                'categoria',
                'observacoes',
            )
        }),
        ('Valores e Datas', {
            'fields': (
                'valor',
                'data_vencimento',
                'valor_recebido',
                'data_recebimento',
            )
        }),
        ('Classificação', {
            'fields': (
                'status',
                'tipo_recebimento',
                'forma_recebimento',
            )
        }),
        ('Destino / Integração', {
            'fields': (
                'banco_destino',
                'movimento_banco',
                'movimento_caixa',
                'parcelamento_uuid',
            )
        }),
        ('Controle de Exclusão', {
            'classes': ('collapse',),
            'fields': ('is_deleted', 'deleted_at')
        }),
    )

    list_per_page = 25
    date_hierarchy = 'data_vencimento'

    def status_colorido(self, obj):
        if obj.status == 'Recebido':
            return format_html('<span style="color: green; font-weight: bold;">✔ Recebido</span>')
        return format_html('<span style="color: orange; font-weight: bold;">⏳ Pendente</span>')
    status_colorido.short_description = 'Status'