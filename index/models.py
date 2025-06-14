from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from admin_alpatex.models import SuscripcionMercadoPago
from admin_alpatex.models import Membresia
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError
import os

##Productos
#Modelo producto
class Producto(models.Model):
    ESTADO_PRODUCTO = [
        ('Nuevo', 'Nuevo'),
        ('Usado', 'Usado'),
    ]
    TIPO_PUBLICACION = [
        ('Venta', 'Venta'),
        ('Intercambio', 'Intercambio'),
    ]
    ESTADO_REVISION = [
        ('Pendiente', 'Pendiente'),
        ('Aceptado', 'Aceptado'),
        ('Rechazado', 'Rechazado'),
    ]
    CATEGORIAS = [
        ('Videojuego', 'Videojuego'),
        ('Libro', 'Libro'),
    ]

    id_producto = models.AutoField(db_column='idProducto', primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_PRODUCTO, default='')  # default value added
    tipo = models.CharField(max_length=20, choices=TIPO_PUBLICACION, default='')
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default='-')
    imagen = models.ImageField(upload_to='productos/', default='productos/default_image.jpg')
    estado_revision = models.CharField(max_length=10, choices=ESTADO_REVISION, default='Pendiente')
    motivo_rechazo = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    contador_visitas = models.IntegerField(default=0)
    disponible = models.BooleanField(default=True)
    precio = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    #para facilitar el ordenamiento de productos para el admin
    @property
    def prioridad_verificacion(self):
        try:
            perfil = self.usuario.perfil
            ahora = timezone.now()
            suscripcion = SuscripcionMercadoPago.objects.filter(
                perfil=perfil,
                fecha_fin__gte=ahora
            ).order_by('-fecha_inicio').first()
            if suscripcion and suscripcion.membresia.nombre == 'Oro':
                return 0
            elif suscripcion and suscripcion.membresia.nombre == 'Plata':
                return 1
        except Exception:
            pass
        return 2  # Básico o sin membresía
    
    @property
    def prioridad_visibilidad(self):
        try:
            perfil = self.usuario.perfil
            ahora = timezone.now()
            suscripcion = SuscripcionMercadoPago.objects.filter(
                perfil=perfil,
                fecha_fin__gte=ahora
            ).order_by('-fecha_inicio').first()
            if suscripcion:
                return suscripcion.membresia.prioridad_visibilidad
        except Exception:
            pass
        return 30  # Valor por defecto para usuarios sin membresía vigente

    def clean(self):
        if self.tipo == 'Venta':
            if self.precio is None or self.precio < 500:
                raise ValidationError("El precio debe ser al menos 500 CLP para productos en venta.")
        else:
            self.precio = None

        super().clean()

#Modelo calificacion producto
class CalificacionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    puntaje = models.IntegerField()
    comentario = models.TextField(blank=True)
    
    def __str__(self):
        return f'{self.producto.nombre} - {self.usuario.username} ({self.puntaje} estrellas)'

##Perfil
#Modelo de perfil
def user_directory_path(instance, filename):
    # El archivo se guardará en MEDIA_ROOT/user_<id>/<filename>
    return f'perfil_images/user_{instance.user.id}/{filename}'

class Perfil(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favoritos = models.ManyToManyField(Producto, related_name='favoritos', blank=True)
    foto_perfil = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True)
    motivo_eliminacion = models.TextField(blank=True, null=True)
    genero = models.CharField(max_length=9, choices=GENERO_CHOICES, default='')
    direccion = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=12, null=True, blank=True)
    membresia = models.ForeignKey(Membresia, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username

    def get_foto_perfil_url(self):
        if self.foto_perfil and hasattr(self.foto_perfil, 'url'):
            return self.foto_perfil.url
        return '/media/perfil_images/user_defecto.PNG'

    def save(self, *args, **kwargs):
        if not self.foto_perfil:
            self.foto_perfil = 'perfil_images/user_defecto.PNG'
        super().save(*args, **kwargs)

@receiver(post_save, sender=User)
def actualizar_foto_perfil_defecto(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.filter(user=instance, foto_perfil__isnull=True).update(foto_perfil='perfil_images/user_defecto.PNG')

class CalificacionVendedor(models.Model):
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calificaciones_recibidas") 
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calificaciones_hechas") 
    puntaje = models.IntegerField() 
    comentario = models.TextField(blank=True, null=True) 
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Calificación de {self.comprador.username} para {self.vendedor.username} en {self.producto.nombre}'

class ReporteVendedor(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True, blank=True)
    comprador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_realizados')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_recibidos')
    motivo = models.TextField()
    puntaje = models.PositiveIntegerField(null=True, blank=True)
    fecha_reporte = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte de {self.comprador} a {self.vendedor} - {self.fecha_reporte}"
    
class ReporteUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_usuario', null=True, blank=True)
    motivo = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)
   

    def __str__(self):
        return f"Reporte de {self.comprador} a {self.vendedor} - {self.fecha_reporte}"

class CalificacionCliente(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_recibidas_cliente')
    vendedor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones_hechas_vendedor')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    puntaje = models.IntegerField()
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Calificación de {self.vendedor} para {self.cliente} en {self.puntaje}'