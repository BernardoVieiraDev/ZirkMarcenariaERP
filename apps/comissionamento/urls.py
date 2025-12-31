from django.urls import path
from . import views

app_name = 'comissionamento'

urlpatterns = [
    # Contratos / Registros Unificados
    path('', views.rt_contratos_list, name='contratos_list'), 
    path('novo/', views.rt_contrato_create, name='contrato_create'),
    path('editar/<int:pk>/', views.rt_contrato_edit, name='contrato_edit'),
    path('excluir/<int:pk>/', views.rt_contrato_delete, name='contrato_delete'),

    # Arquitetas
    path('arquitetas/', views.arquiteta_list, name='arquiteta_list'), 
    path('arquiteta/novo/', views.arquiteta_create, name='arquiteta_create'), 
    path('arquiteta/editar/<int:pk>/', views.arquiteta_edit, name='arquiteta_edit'), 
    path('arquiteta/excluir/<int:pk>/', views.arquiteta_delete, name='arquiteta_delete'),    
]