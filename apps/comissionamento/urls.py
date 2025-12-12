from django.urls import path
from . import views

app_name = 'comissionamento'

urlpatterns = [
    # Visão Geral de Todos os Contratos de RT (Aba RTs POR CLIENTE)
    path('', views.rt_contratos_list, name='contratos_list'), 
    
    # Detalhe do Contrato e Histórico de Pagamentos (Aba RT (2))
    path('<int:pk>/', views.rt_contrato_detail, name='contrato_detail'),
    
    # Registro de Novo Pagamento para um Contrato Específico
    path('<int:contrato_pk>/pagamento/novo/', views.rt_pagamento_create, name='pagamento_create'),
    
    path('arquiteta/novo/', views.arquiteta_create, name='arquiteta_create'),
    
path('contrato/novo/', views.rt_contrato_create, name='contrato_create'),
    ]