from django.contrib import admin
from .models import PeriodoAquisitivo, Ferias

class FeriasInline(admin.TabularInline):
    model = Ferias
    extra = 0

@admin.register(PeriodoAquisitivo)
class PeriodoAquisitivoAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "data_inicio", "data_fim", "dias_direito")
    inlines = [FeriasInline]
