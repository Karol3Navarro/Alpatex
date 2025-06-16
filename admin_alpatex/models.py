from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.

# Modelo para representar los tipos de membresías disponibles en la plataforma
class Membresia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()
    prioridad_visibilidad = models.IntegerField(default=0)
    distintivo = models.CharField(max_length=50, null=True, blank=True)
    verificacion_prioritaria = models.BooleanField(default=False)
    estadisticas = models.BooleanField(default=False)
    precio = models.PositiveIntegerField()
    plan_id = models.CharField(max_length=100, null=True, blank=True) #ids de los planes en mercado pago (prueba)

    def __str__(self):
        return self.nombre

# Relaciona un perfil de usuario con una membresía específica y almacena información de la suscripción
# como el estado, fechas de inicio y fin, y detalles de pago
class SuscripcionMercadoPago(models.Model):
    # Define los estados posibles de la suscripción
    ESTADO_CHOICES = [
        ('active', 'Activa'),
        ('cancelled', 'Cancelada'),
        ('expired', 'Expirada'),
    ]
    # Relaciona la suscripción con un perfil de usuario y una membresía
    perfil = models.ForeignKey('index.Perfil', on_delete=models.CASCADE) #relacion con el perfil del usuario
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE) #relacion con el tipo de membresia
    subscription_id = models.CharField(max_length=100, unique=True) #id de la suscripcion en mercado pago
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='active')
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    ultimo_pago = models.DateTimeField(null=True, blank=True)
    proximo_pago = models.DateTimeField(null=True, blank=True)
    token_tarjeta = models.CharField(max_length=100, null=True, blank=True)
    ultimos_cuatro_digitos = models.CharField(max_length=4, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=50, null=True, blank=True)
    
    # Relaciona la suscripción con un plan de Mercado Pago
    def __str__(self):
        return f"Suscripción {self.subscription_id} - {self.perfil.user.username}"

    #Actualiza la fecha de fin de la suscripción
    def cancelar(self):
        self.estado = 'cancelled'
        # Actualiza la fecha de cancelación a la fecha actual
        self.fecha_cancelacion = timezone.now()
        # La membresía seguirá activa hasta la fecha_fin
        self.save()

    #Calcula la fecha del próximo pago (30 días después del último)
    def actualizar_proximo_pago(self):
        if self.ultimo_pago:
            # Si ya hay un último pago, calcula el próximo pago sumando 30 días
            self.proximo_pago = self.ultimo_pago + timedelta(days=30)
            self.save()

    #Verifica si la suscripción ha expirado
    def verificar_estado(self):
        # Si la suscripción está activa y tiene una fecha de fin, verifica si ha pasado esa fecha
        #Si la fecha de fin es nula, la suscripción no ha expirado
        #si la fecha de fin es menor a la fecha actual, cambia el estado a 'expired'
        if self.estado == 'active' and self.fecha_fin and timezone.now() > self.fecha_fin:
            self.estado = 'expired'
            self.save()
        return self.estado



