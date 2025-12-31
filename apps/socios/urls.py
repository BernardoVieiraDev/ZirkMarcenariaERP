from django.urls import path
from . import views

app_name = 'socios'

urlpatterns = [
    # Rotas de cadastro e relatórios
    path('novo/', views.registrar_despesa, name='registrar_despesa'),
    path('relatorio/', views.relatorio_anual, name='relatorio_anual'),
    path('extrato/', views.listar_lancamentos, name='listar_lancamentos'),
    path('exportar/', views.exportar_relatorio, name='exportar_excel'),
    path('novo-socio/', views.cadastrar_socio, name='cadastrar_socio'),

    # Rotas de Edição e Exclusão (pk deve ser inteiro)
    path('editar/<int:pk>/', views.editar_lancamento, name='editar_lancamento'),
    path('excluir/<int:pk>/', views.excluir_lancamento, name='excluir_lancamento'),
]