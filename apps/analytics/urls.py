from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('financeiro/', views.financial_dashboard_view, name='financial_dashboard'),
]
#analytics/financeiro