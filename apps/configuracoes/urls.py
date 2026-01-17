from django.urls import path

from . import views

app_name = 'configuracoes'

urlpatterns = [
    path('lixeira/', views.dashboard_lixeira, name='lixeira_dashboard'),
    path('lixeira/<str:model_key>/', views.lixeira_itens, name='lixeira_itens'),
    path('lixeira/<str:model_key>/<int:pk>/restaurar/', views.restaurar_item, name='restaurar_item'),
    path('lixeira/<str:model_key>/<int:pk>/deletar/', views.deletar_permanente, name='deletar_permanente'),
path('criar-admin/', views.criar_novo_admin, name='criar_novo_admin'),
path('editar/', views.editar_configuracoes, name='editar_configuracoes'),
    path('lixeira/<str:model_key>/acoes-em-massa/', views.acoes_lixeira_em_massa, name='acoes_lixeira_em_massa'),
    path('lixeira/<str:model_key>/esvaziar/', views.esvaziar_lixeira, name='esvaziar_lixeira'),
]


