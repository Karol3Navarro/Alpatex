from django.contrib import admin
from .models import Producto, Perfil, CalificacionVendedor, ReporteVendedor, CalificacionCliente, ReporteUsuario
# Register your models here.
admin.site.register(Producto)
admin.site.register(Perfil)
admin.site.register(CalificacionVendedor)
admin.site.register(ReporteVendedor)
admin.site.register(ReporteUsuario)
admin.site.register(CalificacionCliente)