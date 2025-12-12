# minha_app/urls.py
from django.urls import path
from . import views

app_name = "relatorios"


urlpatterns = [
    path('', views.list_planilhas, name='listar_planilhas'),
    path('exportar_boletos/', views.exportar_todos_boletos, name='exportar_todos_boletos'),
    path('exportar_utilidades/', views.exportar_utilidades, name='exportar_utilidades'),
    path('exportar_cheques/', views.exportar_cheques, name='exportar_cheques'),
    path('exportar_contabilidade/', views.exportar_contabilidade, name='exportar_contabilidade'),
    path('exportar_cartoes/', views.exportar_cartoes, name='exportar_cartoes'),
    path('exportar_bndes/', views.exportar_bndes, name='exportar_bndes'),
    path('exportar_gastos_gerais/', views.exportar_gastos_gerais, name='exportar_gastos_gerais'),
    path('exportar_veiculos/', views.exportar_veiculos, name='exportar_veiculos'),
    path('exportar_condominio/', views.exportar_condominio, name='exportar_condominio'),
    path('exportar_iptu/', views.exportar_iptu, name='exportar_iptu'),
    path('exportar_gasolina/', views.exportar_gasolina, name='exportar_gasolina'),
    path('exportar_comissoes/', views.exportar_comissoes, name='exportar_comissoes'),
    path('exportar_prestacoes/', views.exportar_prestacoes, name='exportar_prestacoes'),
path('exportar_folha/', views.exportar_folha, name='exportar_folha'),
]