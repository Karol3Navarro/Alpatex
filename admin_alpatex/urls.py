from django.urls import path
from . import views
from index import views as index_views  # Importa la vista de perfil desde la app 'index'


urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('reporte_productos/', views.reporte_productos, name='reporte_productos'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('perfil/<str:username>/', views.perfil_usuario, name='perfil_usuario'),
    path('exportar_excel/', views.export_to_excel, name='exportar_excel'),




  # Ruta para el dashboard
]
