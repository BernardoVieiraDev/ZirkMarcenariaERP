from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from apps.dashboard.forms import LoginFormComCPF  # Importe o form

urlpatterns = [
path('', auth_views.LoginView.as_view(
        template_name='core/login.html',
        authentication_form=LoginFormComCPF,
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('admin/', admin.site.urls),
    path('dashboard/',  include("apps.dashboard.urls")),
    path('rescisao/', include('apps.rescisao.urls')),
    path("funcionarios/", include("apps.funcionarios.urls")),
    path("pagar/", include("apps.financeiro.pagar.urls")),
    path("receber/", include("apps.financeiro.receber.urls")),
    path("ferias/", include("apps.ferias.urls")),
    path('banco-horas/', include('apps.banco_horas.urls')),
    path('comissionamento/', include('apps.comissionamento.urls')),
    path('relatorios/', include("apps.relatorios.urls")),
    path('socios/', include('apps.socios.urls')),
]


