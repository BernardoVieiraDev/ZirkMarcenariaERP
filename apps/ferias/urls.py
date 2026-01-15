from django.urls import path

from . import views

app_name = "ferias"

urlpatterns = [
    path('', views.listar_funcionarios, name='listar_funcionarios'),
    path('registrar-periodo/', views.registrar_periodo, name='registrar_periodo'),
    path('editar-periodo/<int:pk>/', views.editar_periodo, name='editar_periodo'),
    path('deletar-periodo/<int:pk>/', views.deletar_periodo, name='deletar_periodo'),
path('ferias-coletivas/', views.registrar_ferias_coletivas, name='registrar_ferias_coletivas'),
    path('registrar-ferias/', views.registrar_ferias, name='registrar_ferias'),
    path('editar-ferias/<int:pk>/', views.editar_ferias, name='editar_ferias'),
    path('deletar-ferias/<int:pk>/', views.deletar_ferias, name='deletar_ferias'),

    # Pagamento rotas
    path('pagamentos/', views.listar_pagamentos, name='listar_pagamentos'),
    path('pagamentos/registrar/', views.registrar_pagamento, name='registrar_pagamento'),
    path('pagamentos/deletar/<int:pk>/', views.deletar_pagamento, name='deletar_pagamento'),
path('pagamentos/editar/<int:pk>/', views.editar_pagamento, name='editar_pagamento'),
path('exportar-planilha/', views.exportar_planilha_geral, name='exportar_planilha_ferias'),
path('recibos/', views.listar_recibos, name='listar_recibos'),
    path('recibos/registrar/', views.registrar_recibo, name='registrar_recibo'),
    path('recibos/editar/<int:pk>/', views.editar_recibo, name='editar_recibo'),
    path('recibos/deletar/<int:pk>/', views.deletar_recibo, name='deletar_recibo'),


]
