from django.urls import path

from . import views

app_name = 'banco_horas'

urlpatterns = [
    path('', views.banco_horas_list, name='banco_horas_list'),
    path('registrar/', views.registrar_horas, name='registrar'),
    path('editar/<int:pk>/', views.banco_horas_edit, name='banco_horas_edit'),
    # Adicionado a rota para deletar:
    path('excluir/<int:pk>/', views.banco_horas_delete, name='banco_horas_delete'),
    path('historico/<int:pk>/', views.historico_funcionario, name='historico_funcionario'),

]