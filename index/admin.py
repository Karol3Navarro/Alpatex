from django.contrib import admin
from .models import Producto, Perfil, CalificacionProducto, CalificacionVendedor
# Register your models here.
admin.site.register(Producto)
admin.site.register(Perfil)
admin.site.register(CalificacionProducto)
admin.site.register(CalificacionVendedor)