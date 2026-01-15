from django.contrib import admin
from .models import ConfiguracaoGlobal

# Mixin para adicionar funcionalidade de "Restaurar" no Admin do Django
class SoftDeleteAdminMixin:
    def get_queryset(self, request):
        # No admin, queremos ver TUDO (use o manager all_objects que você criou)
        qs = self.model.all_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def delete_model(self, request, obj):
        # Usa o soft delete definido no model
        obj.delete()

    actions = ['restaurar_registros']

    @admin.action(description='Restaurar registros selecionados')
    def restaurar_registros(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} itens restaurados com sucesso.")

@admin.register(ConfiguracaoGlobal)
class ConfiguracaoGlobalAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'lixeira_ativa', 'dias_retencao_lixeira', 'limpeza_automatica_ativa']
    
    # Impede adicionar mais de uma configuração
    def has_add_permission(self, request):
        return not ConfiguracaoGlobal.objects.exists()