from django.urls import path
from . import views
from index import views as index_views  # Importa la vista de perfil desde la app 'index'


urlpatterns = [
    path('', views.dashboard, name='admin_dashboard'),
    path('reporte_productos/', views.reporte_productos, name='reporte_productos'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('perfil/<str:username>/', views.perfil_usuario, name='perfil_usuario'),
    path('exportar_excel/', views.export_to_excel, name='exportar_excel'),
    path('home_admin', views.home_admin, name='home_admin'),
    path('membresias/', views.listar_membresias, name='listar_membresias'),
    path('membresias/nueva/', views.crear_membresia, name='crear_membresia'),
    path('membresias/editar/<int:membresia_id>/', views.editar_membresia, name='editar_membresia'),
    path('membresias/eliminar/<int:membresia_id>/', views.eliminar_membresia, name='eliminar_membresia'),
    path('gestionar-productos/', views.gestionar_productos, name='gestionar_productos'),
    path('usuarios_reportados/', views.usuarios_reportados, name='usuarios_reportados'),
    path('usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('exportar_pdf/', views.export_to_pdf, name='exportar_pdf'),
    path('reporte/usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('export/usuarios/excel/', views.export_usuarios_to_excel, name='export_usuarios_excel'),
    path('export/usuarios/pdf/', views.export_usuarios_to_pdf, name='export_usuarios_pdf'),
    path('admin/producto/<int:id_producto>/', views.ver_producto_admin, name='ver_producto_admin'),
    path('usuarios/eliminados/', views.usuarios_eliminados, name='usuarios_eliminados'),
    path('usuarios/reactivar/<int:user_id>/', views.reactivar_usuario, name='reactivar_usuario'),


  # Ruta para el dashboard
]
