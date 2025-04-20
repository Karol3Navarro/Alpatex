from django.urls import path
from . import views

urlpatterns = [
    path('index', views.index, name='index'),
    path('home', views.home, name='home'),
    path('login', views.logout, name='login'),
    path('registro', views.registro, name='registro'),
    path('producto_add', views.producto_add, name='producto_add'),
    path('producto/<int:id_producto>/', views.ver_producto, name='ver_producto'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
]