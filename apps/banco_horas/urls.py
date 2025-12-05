from django.urls import path
from . import views

app_name = 'banco_horas'

urlpatterns = [
    path('registrar/', views.registrar_horas, name='registrar'),
]
