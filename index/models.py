from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Producto(models.Model):
    id_producto = models.AutoField(db_column='idProducto', primary_key=True)
    nombre = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario

    def __str__(self):
        return str(self.nombre)
class Perfil(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='perfil_images/', null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, default='O')
    direccion = models.CharField(max_length=255, null=True, blank=True)
    rut = models.CharField(max_length=12, null=True, blank=True)

    def __str__(self):
        return self.user.username
