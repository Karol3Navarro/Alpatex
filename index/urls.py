from django.urls import path, include
from . import views
from admin_alpatex import views as admin_views

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

    
    path('producto/agregar/', views.producto_add_perf, name='producto_add_perf'),
    path('admin_dashboard/', include('admin_alpatex.urls')),  


    path('membresia/', views.ver_membresia_usuario, name='ver_membresia_usuario'),

    path('producto_del/<str:pk>', views.producto_del, name='producto_del'),
    path('producto_findEdit/<int:pk>/', views.producto_findEdit, name='producto_findEdit'),
    path('productoUpdate', views.editar_producto, name='productoUpdate')
]