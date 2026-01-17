from django.urls import path
from . import views

app_name = "receber"


urlpatterns = [
    path('', views.receber_list, name='receber'),
    path('add/', views.receber_create, name='receber_add'),
    path('<int:pk>/edit/', views.receber_edit, name='receber_edit'),
    path('<int:pk>/delete/', views.receber_delete, name='receber_delete'),
    
    
    path('caixa-diario/', views.caixa_diario_view, name='caixa_diario'),
    path('caixa-diario/<int:pk>/delete/', views.caixa_diario_delete, name='caixa_diario_delete'),

path('bancos/', views.bancos_list, name='bancos_list'),
    path('bancos/<int:pk>/edit/', views.banco_edit, name='banco_edit'),     # NOVA
    path('bancos/<int:pk>/delete/', views.banco_delete, name='banco_delete'), # NOVA

    # --- MOVIMENTAÇÃO BANCÁRIA ---
    path('movimento-banco/', views.movimento_banco_view, name='movimento_banco'),
    path('movimento-banco/<int:pk>/edit/', views.movimento_banco_edit, name='movimento_banco_edit'), # NOVA
    path('movimento-banco/<int:pk>/delete/', views.movimento_banco_delete, name='movimento_banco_delete'),]


