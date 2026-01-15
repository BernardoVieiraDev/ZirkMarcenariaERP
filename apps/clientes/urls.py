from django.urls import path

from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.lista_clientes, name='list'),
    path('novo/', views.criar_cliente, name='create'),
    path('editar/<int:pk>/', views.editar_cliente, name='update'),
    path('excluir/<int:pk>/', views.deletar_cliente, name='delete'),
    path('detalhes/<int:pk>/', views.detalhe_cliente, name='detail'),
    path('buscar-cep/', views.buscar_endereco_por_cep, name='buscar_cep'),
]