# minha_app/urls.py
from django.urls import path
from . import views

app_name = "pagar"
urlpatterns = [
    # Lista Unificada
    path('', views.pagar_list, name='pagar_list'), # Ajustei o nome para 'pagar_list'
    # Criação Dinâmica Única
    path('add/', views.pagar_create, name='pagar_create'), 
    # Edição e Deleção (Dinâmica)
    path('<int:pk>/edit/', views.pagar_edit, name='pagar_edit'),
    path('<int:pk>/delete/', views.pagar_delete, name='pagar_delete'),


    #Teste excel
]