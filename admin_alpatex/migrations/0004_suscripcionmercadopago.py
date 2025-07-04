# Generated by Django 5.2 on 2025-06-01 21:40

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_alpatex', '0003_update_membresia_prioridades'),
        ('index', '0020_perfil_fecha_eliminacion_perfil_motivo_eliminacion'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuscripcionMercadoPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_id', models.CharField(max_length=100, unique=True)),
                ('estado', models.CharField(choices=[('active', 'Activa'), ('cancelled', 'Cancelada'), ('expired', 'Expirada')], default='active', max_length=20)),
                ('fecha_inicio', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_fin', models.DateTimeField(blank=True, null=True)),
                ('fecha_cancelacion', models.DateTimeField(blank=True, null=True)),
                ('ultimo_pago', models.DateTimeField(blank=True, null=True)),
                ('proximo_pago', models.DateTimeField(blank=True, null=True)),
                ('token_tarjeta', models.CharField(blank=True, max_length=100, null=True)),
                ('ultimos_cuatro_digitos', models.CharField(blank=True, max_length=4, null=True)),
                ('tipo_tarjeta', models.CharField(blank=True, max_length=50, null=True)),
                ('membresia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admin_alpatex.membresia')),
                ('perfil', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='index.perfil')),
            ],
        ),
    ]
