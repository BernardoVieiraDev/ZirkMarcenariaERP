from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import PerfilUsuario


# Define como o Perfil aparecerá dentro da página do Usuário
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Informações de Perfil (CPF)'

# Customiza o UserAdmin padrão para incluir o Inline
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

# Re-registra o modelo User com a nova configuração
admin.site.unregister(User)
admin.site.register(User, UserAdmin)