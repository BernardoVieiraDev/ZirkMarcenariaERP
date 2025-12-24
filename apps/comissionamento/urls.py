from django.urls import path
from . import views

app_name = 'comissionamento'

urlpatterns = [
    # Contratos
    path('', views.rt_contratos_list, name='contratos_list'), 
    path('<int:pk>/', views.rt_contrato_detail, name='contrato_detail'),
    path('contrato/novo/', views.rt_contrato_create, name='contrato_create'),
    path('contrato/editar/<int:pk>/', views.rt_contrato_edit, name='contrato_edit'),
    path('contrato/excluir/<int:pk>/', views.rt_contrato_delete, name='contrato_delete'),

    # Pagamentos
    path('<int:contrato_pk>/pagamento/novo/', views.rt_pagamento_create, name='pagamento_create'),
    path('pagamento/editar/<int:pk>/', views.rt_pagamento_edit, name='pagamento_edit'),
    path('pagamento/excluir/<int:pk>/', views.rt_pagamento_delete, name='pagamento_delete'),

    # Arquitetas
    path('arquitetas/', views.arquiteta_list, name='arquiteta_list'), 
    path('arquiteta/novo/', views.arquiteta_create, name='arquiteta_create'), 
    path('arquiteta/editar/<int:pk>/', views.arquiteta_edit, name='arquiteta_edit'), 
    path('arquiteta/excluir/<int:pk>/', views.arquiteta_delete, name='arquiteta_delete'),    
]