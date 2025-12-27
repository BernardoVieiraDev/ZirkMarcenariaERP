from django.urls import path
from . import views

# Esta linha é OBRIGATÓRIA para usar 'rescisao:...'
app_name = 'rescisao'

urlpatterns = [
    path('', views.RescisaoListView.as_view(), name='rescisao_list'),
    path('novo/', views.RescisaoCreateView.as_view(), name='rescisao_create'),
    path('editar/<int:pk>/', views.RescisaoUpdateView.as_view(), name='rescisao_update'),
    path('excluir/<int:pk>/', views.RescisaoDeleteView.as_view(), name='rescisao_delete'),
    path('excel/<int:pk>/', views.gerar_excel_rescisao, name='rescisao_excel'),
]