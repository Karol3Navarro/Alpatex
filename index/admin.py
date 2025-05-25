from django.contrib import admin
from .models import Producto, Perfil, CalificacionVendedor, ReporteVendedor
# Register your models here.
admin.site.register(Producto)
admin.site.register(Perfil)
admin.site.register(CalificacionVendedor)
admin.site.register(ReporteVendedor)