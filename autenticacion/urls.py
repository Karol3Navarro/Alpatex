from django.urls import path
from . import views

app_name = 'autenticacion'  # Definir el espacio de nombres

urlpatterns = [
    path('cambiar-clave/', views.cambiar_clave, name='cambiar_clave'),
    path('reset-clave/<uidb64>/<token>/', views.reset_clave, name='reset_clave'),
    path('clave-cambiada/', views.clave_cambiada, name='clave_cambiada'),  # Cambio aquí
    path('clave-enviada/', views.clave_enviada, name='clave_enviada'),  # Ruta para 'clave_enviada'
    path('correo-enviado-modal/', views.correo_modal, name='correo_modal'),




]
