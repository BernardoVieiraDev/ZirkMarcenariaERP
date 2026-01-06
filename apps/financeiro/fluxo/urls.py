from django.urls import path
from . import views

# app_name = 'fluxo' # Descomente se quiser usar namespace (ex: fluxo:semanal)

urlpatterns = [
    # Visualização Semanal (Padrão ou /semanal/)
    path('semanal/', views.fluxo_semanal, name='fluxo_semanal'),
    
    # Visualização Mensal
    path('mensal/', views.fluxo_mensal, name='fluxo_mensal'),
    
    # Exportação para Excel
    path('exportar/<str:tipo>/', views.exportar_fluxo, name='exportar_fluxo'),
]