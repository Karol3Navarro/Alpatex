from django.urls import path, include
from . import views
from admin_alpatex import views as admin_views
from .views import guardar_confirmacion_entrega

urlpatterns = [
    path('index', views.index, name='index'),
    path('home', views.home, name='home'),
    path('login', views.logout, name='login'),
    path('registro', views.registro, name='registro'),
    path('producto/<int:id_producto>/', views.ver_producto, name='ver_producto'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('mapa/', views.map, name='mapa'),
    path('gestionar_productos/', admin_views.gestionar_productos, name='gestionar_productos'),
    path('mis-productos/', views.productos_perfil, name='productos_perf'),
    path('producto/<int:producto_id>/redirigir/', views.redirigir_producto, name='redirigir_producto'),
    path('libros/', views.libros, name='vista_libros'),
    path('videojuegos/', views.videojuegos, name='vista_videojuegos'),
    path('productos/', views.productos, name='vista_productos'),


    path('producto/agregar/', views.producto_add_perf, name='producto_add_perf'),
    path('admin_dashboard/', include('admin_alpatex.urls')),  


    path('membresia/', views.ver_membresia_usuario, name='ver_membresia_usuario'),

    path('producto_del/<str:pk>', views.producto_del, name='producto_del'),
    path('producto_findEdit/<int:pk>/', views.producto_findEdit, name='producto_findEdit'),
    path('productoUpdate', views.editar_producto, name='productoUpdate'),
    path('guardar_confirmacion/', guardar_confirmacion_entrega, name="guardar_confirmacion_entrega"),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('calificar_vendedor/', views.calificar_vendedor, name='calificar_vendedor'),
]