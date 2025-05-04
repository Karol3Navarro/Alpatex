from django.db import models

# Create your models here.
class Membresia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    prioridad_visibilidad = models.IntegerField(default=0)
    distintivo = models.CharField(max_length=50, null=True, blank=True)
    verificacion_prioritaria = models.BooleanField(default=False)
    estadisticas = models.BooleanField(default=False)
    precio = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre



