from django.contrib import admin
from .models import Canal, CanalUsuario, CanalMensaje, ConfirmacionEntrega
# Register your models here.

# Definición de las clases inline para los modelos CanalMensaje y CanalUsuario
# Estas clases permiten editar los mensajes y usuarios asociados a un canal 
# directamente desde la interfaz de administración
class CanalMensajeInline(admin.TabularInline):
    model =CanalMensaje
    extra=1

class CanalUsuarioInline(admin.TabularInline):
    model =CanalUsuario
    extra=1
    
# Clase CanalAdmin que define cómo se verá el modelo Canal en el panel de administración de Django
# Utiliza las clases inline para mostrar los mensajes y usuarios asociados al canal
class CanalAdmin(admin.ModelAdmin):
    inlines =[CanalMensajeInline, CanalUsuarioInline]

    class Meta:
        model =Canal

#registra los modelos en el admin de Django
admin.site.register(Canal, CanalAdmin)
admin.site.register(CanalUsuario)
admin.site.register(CanalMensaje)
admin.site.register(ConfirmacionEntrega)