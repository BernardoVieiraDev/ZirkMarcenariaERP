from django.urls import path

from . import views

app_name = "funcionarios"
urlpatterns = [
    path('criar/', views.criar_funcionario, name='criar_funcionario'),
    path('', views.lista_funcionarios, name='funcionarios'),
    path('editar/<int:pk>/edit/', views.editar_funcionario, name='editar_funcionario'),
    path('deletar/<int:pk>/delete/', views.deletar_funcionario, name='deletar_funcionario'),
    path('exportar_excel/<int:pk>/', views.gerar_excel_funcionario, name='gerar_excel_funcionario'),  # <-- URL
    path('buscar-endereco/', views.buscar_endereco_por_cep, name='buscar_endereco'),

]