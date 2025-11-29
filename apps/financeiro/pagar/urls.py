from django.urls import path

from . import views

app_name = "pagar"
urlpatterns = [
    path('', views.pagar_list, name='pagar'),
    path('add/', views.pagar_create, name='pagar_add'),
    path('<int:pk>/edit/', views.pagar_edit, name='pagar_edit'),
    path('<int:pk>/delete/', views.pagar_delete, name='pagar_delete'),

]