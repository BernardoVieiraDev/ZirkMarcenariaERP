from django.urls import path
from . import views

app_name = 'banco_horas'

urlpatterns = [
    path('', views.banco_horas_list, name='banco_horas_list'),
    path('registrar/', views.registrar_horas, name='registrar'),
    path('editar/<int:pk>/', views.banco_horas_edit, name='banco_horas_edit'),
]
