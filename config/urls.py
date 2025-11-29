from django.contrib import admin
from django.urls import path, include


  
urlpatterns = [
    path('dashboard/',  include("apps.dashboard.urls")),
    path("funcionarios/", include("apps.funcionarios.urls")),
    path("pagar/", include("apps.financeiro.pagar.urls")),
    path("receber/", include("apps.financeiro.receber.urls")),
    path("ferias/", include("apps.ferias.urls")),
]


