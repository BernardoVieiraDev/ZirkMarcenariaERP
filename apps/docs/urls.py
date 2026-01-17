# apps/docs/urls.py
from django.urls import path
from .views import (
    DocsIndexView, 
    DocsRHView, 
    DocsFinanceiroView, 
    DocsComercialView,
    DocsRelatoriosView
)

app_name = 'docs'

urlpatterns = [
    path('', DocsIndexView.as_view(), name='index'),
    path('rh/', DocsRHView.as_view(), name='rh'),
    path('financeiro/', DocsFinanceiroView.as_view(), name='financeiro'),
    path('comercial/', DocsComercialView.as_view(), name='comercial'),
    path('relatorios/', DocsRelatoriosView.as_view(), name='relatorios'),
]