from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Producto(models.Model):
    id_producto = models.AutoField(db_column='idProducto', primary_key=True)
    nombre = models.CharField(max_length=100)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)  # Relación con el usuario

    def __str__(self):
        return str(self.nombre)