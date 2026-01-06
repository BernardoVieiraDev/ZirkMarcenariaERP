from django.contrib import admin
from .models import Socio, CategoriaSocio, LancamentoSocio

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CategoriaSocio)
class CategoriaSocioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'grupo')
    list_filter = ('grupo',)
    search_fields = ('nome',)
    ordering = ('grupo', 'nome')

@admin.register(LancamentoSocio)
class LancamentoSocioAdmin(admin.ModelAdmin):
    # Mostra colunas úteis para identificar o registro
    list_display = ('data', 'socio', 'categoria', 'valor', 'observacao')
    
    # Filtros laterais (AQUI É ONDE VOCÊ VAI FILTRAR AS CATEGORIAS ERRADAS)
    list_filter = ('categoria', 'socio', 'data')
    
    # Barra de pesquisa
    search_fields = ('observacao', 'socio__nome', 'categoria__nome')
    
    # Navegação por data no topo
    date_hierarchy = 'data'