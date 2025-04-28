from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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


    def __str__(self):
        return self.nombre

class Perfil(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Otro', 'Otro'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='perfil_images/', null=True, blank=True)
    genero = models.CharField(max_length=9, choices=GENERO_CHOICES, default='')
    direccion = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=12, null=True, blank=True)

    def __str__(self):
        return self.user.username
