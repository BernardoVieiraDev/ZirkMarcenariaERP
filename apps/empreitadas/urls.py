from django.urls import path
from . import views

app_name = 'empreitadas'

urlpatterns = [
    path('', views.empreitada_list, name='list'),
    path('nova/', views.empreitada_create, name='create'),
    path('<int:pk>/', views.empreitada_detail, name='detail'),
    
    path('<int:pk>/editar/', views.empreitada_edit, name='edit'),
    path('<int:pk>/excluir/', views.empreitada_delete, name='delete'),


]