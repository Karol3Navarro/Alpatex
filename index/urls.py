from django.urls import path, include
from . import views
from admin_alpatex import views as admin_views
from .views import guardar_confirmacion_entrega

urlpatterns = [
    path('index', views.index, name='index'),
    path('home', views.home, name='home'),
    path('login', views.logout, name='login'),
    path('registro', views.registrar_usuario, name='registro'),
    path('producto/<int:id_producto>/', views.ver_producto, name='ver_producto'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('mapa/', views.map, name='mapa'),
    path('gestionar_productos/', admin_views.gestionar_productos, name='gestionar_productos'),
    path('mis-productos/', views.productos_perfil, name='productos_perf'),
    path('producto/<int:producto_id>/redirigir/', views.redirigir_producto, name='redirigir_producto'),
    path('libros/', views.libros, name='vista_libros'),
    path('videojuegos/', views.videojuegos, name='vista_videojuegos'),
    path('productos/', views.productos, name='vista_productos'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('agregar-favorito/<int:producto_id>/', views.agregar_favorito, name='agregar_favorito'),
    path('quitar-favorito/<int:producto_id>/', views.quitar_favorito, name='quitar_favorito'),
    path('toggle-favorito/<int:producto_id>/', views.toggle_favorito, name='toggle_favorito'),
    path('search/', views.buscar_productos, name='buscar_productos'),
    path('producto/<int:id>/', views.detalle_producto, name='detalle_producto'),
    path('producto/agregar/', views.producto_add_perf, name='producto_add_perf'),
    path('admin_dashboard/', include('admin_alpatex.urls')),  

    path('producto_del/<str:pk>', views.producto_del, name='producto_del'),
    path('producto_findEdit/<int:pk>/', views.producto_findEdit, name='producto_findEdit'),
    path('productoUpdate', views.editar_producto, name='productoUpdate'),
    path('guardar_confirmacion/', guardar_confirmacion_entrega, name="guardar_confirmacion_entrega"),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    path('calificar_vendedor/', views.calificar_vendedor, name='calificar_vendedor'),
    path('reportar_vendedor/', views.reportar_vendedor, name='reportar_vendedor'),
    path('reportar_usuario/', views.reportar_usuario, name='reportar_usuario'),
    path('terminos/', views.terminos, name='terminos'),

    path('confirmacion/<int:pk>/editar/', views.editar_confirmacion, name='editar_confirmacion'),
    path('confirmacion/<int:pk>/eliminar/', views.eliminar_confirmacion, name='eliminar_confirmacion'),
    

    path('membresia/', views.ver_membresia_usuario, name='ver_membresia_usuario'),
    path('membresia/api/', views.crear_suscripcion_api, name='crear_suscripcion_api'),
    path('membresia/cancelar/', views.cancelar_suscripcion_view, name='cancelar_suscripcion'),
    path('pago_exito/', views.pago_exito, name='pago_exito'),
    path('pago_rechazado/', views.pago_rechazado, name='pago_rechazado'),
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
    path('calificar_cliente/', views.calificar_cliente, name='calificar_cliente'),
]