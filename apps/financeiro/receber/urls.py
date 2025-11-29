from django.urls import path
from . import views

app_name = "receber"


urlpatterns = [
    path('', views.receber_list, name='receber'),
    path('add/', views.receber_create, name='receber_add'),
    path('<int:pk>/edit/', views.receber_edit, name='receber_edit'),
    path('<int:pk>/delete/', views.receber_delete, name='receber_delete'),
]

