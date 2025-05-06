from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from admin_alpatex.models import Membresia
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
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

    id_producto = models.AutoField(db_column='idProducto', primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_PRODUCTO, default='')  # default value added
    tipo = models.CharField(max_length=20, choices=TIPO_PUBLICACION, default='')
    imagen = models.ImageField(upload_to='productos/', default='productos/default_image.jpg')
    estado_revision = models.CharField(max_length=10, choices=ESTADO_REVISION, default='Pendiente')
    motivo_rechazo = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    contador_visitas = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre
    
    #para facilitar el ordenamiento de productos para el admin
    @property
    def prioridad_verificacion(self):
        try:
            membresia = self.usuario.perfil.membresia
            if membresia and membresia.nombre == 'Oro':
                return 0
            elif membresia and membresia.nombre == 'Plata':
                return 1
        except:
            pass
        return 2  # Básico o sin membresía

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
    foto_perfil = models.ImageField(upload_to=user_directory_path, null=True, blank=True)
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


