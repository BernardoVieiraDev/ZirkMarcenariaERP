# minha_app/urls.py
from django.urls import path
from . import views

app_name = "pagar"
urlpatterns = [
    # Lista Unificada
    path('', views.pagar_list, name='pagar_list'), 
    # Criação Dinâmica Única
    path('add/', views.pagar_create, name='pagar_create'), 
    # Edição e Deleção (Dinâmica)
    path('<int:pk>/edit/', views.pagar_edit, name='pagar_edit'),
    path('<int:pk>/delete/', views.pagar_delete, name='pagar_delete'),

    path('folha/', views.folha_mensal_view, name='folha_mensal'),
    path('folha/', views.folha_mensal_view, name='folha_mensal'),
    path('folha/exportar/', views.folha_exportar_excel, name='folha_exportar'),
    path('folha/pagar-todos/', views.folha_pagar_todos, name='folha_pagar_todos'), 
path('folha/holerite/<int:pk>/', views.baixar_holerite_view, name='baixar_holerite'),
    path('folha/fechar-mes/', views.folha_fechar_mes, name='folha_fechar_mes'),

path('folha/baixar-lote/', views.baixar_holerite_lote_view, name='baixar_holerite_lote'),


]