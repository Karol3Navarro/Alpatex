from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.
class Membresia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    prioridad_visibilidad = models.IntegerField(default=0)
    distintivo = models.CharField(max_length=50, null=True, blank=True)
    verificacion_prioritaria = models.BooleanField(default=False)
    estadisticas = models.BooleanField(default=False)
    precio = models.PositiveIntegerField()
    plan_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nombre

class SuscripcionMercadoPago(models.Model):
    ESTADO_CHOICES = [
        ('active', 'Activa'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]

    perfil = models.ForeignKey('index.Perfil', on_delete=models.CASCADE)
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE)
    subscription_id = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='active')
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    ultimo_pago = models.DateTimeField(null=True, blank=True)
    proximo_pago = models.DateTimeField(null=True, blank=True)
    token_tarjeta = models.CharField(max_length=100, null=True, blank=True)
    ultimos_cuatro_digitos = models.CharField(max_length=4, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Suscripción {self.subscription_id} - {self.perfil.user.username}"

    def cancelar(self):
        self.estado = 'cancelled'
        self.fecha_cancelacion = timezone.now()
        # La membresía seguirá activa hasta la fecha_fin
        self.save()

    def actualizar_proximo_pago(self):
        if self.ultimo_pago:
            self.proximo_pago = self.ultimo_pago + timedelta(days=30)
            self.save()

    def verificar_estado(self):
        if self.estado == 'active' and self.fecha_fin and timezone.now() > self.fecha_fin:
            self.estado = 'expired'
            self.save()
        return self.estado



