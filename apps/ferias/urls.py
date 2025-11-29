from django.urls import path

from . import views

app_name = "ferias"

urlpatterns = [
    path('', views.listar_funcionarios, name='listar_funcionarios'),
    path('registrar-periodo/', views.registrar_periodo, name='registrar_periodo'),
    path('editar-periodo/<int:pk>/', views.editar_periodo, name='editar_periodo'),
    path('deletar-periodo/<int:pk>/', views.deletar_periodo, name='deletar_periodo'),

    path('registrar-ferias/', views.registrar_ferias, name='registrar_ferias'),
    path('editar-ferias/<int:pk>/', views.editar_ferias, name='editar_ferias'),
    path('deletar-ferias/<int:pk>/', views.deletar_ferias, name='deletar_ferias'),

    # Pagamento rotas
    path('pagamentos/', views.listar_pagamentos, name='listar_pagamentos'),
    path('pagamentos/registrar/', views.registrar_pagamento, name='registrar_pagamento'),
    path('pagamentos/deletar/<int:pk>/', views.deletar_pagamento, name='deletar_pagamento'),

    path('teste/', views.teste, name='teste'),
]
