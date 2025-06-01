from django.db import migrations

def actualizar_prioridades(apps, schema_editor):
    Membresia = apps.get_model('admin_alpatex', 'Membresia')
    
    # Actualizar membresía Oro (mayor prioridad)
    try:
        membresia_oro = Membresia.objects.get(nombre='Oro')
        membresia_oro.prioridad_visibilidad = 10
        membresia_oro.save()
    except Membresia.DoesNotExist:
        pass

    # Actualizar membresía Plata
    try:
        membresia_plata = Membresia.objects.get(nombre='Plata')
        membresia_plata.prioridad_visibilidad = 20
        membresia_plata.save()
    except Membresia.DoesNotExist:
        pass

    # Actualizar membresía Básica (menor prioridad)
    try:
        membresia_basica = Membresia.objects.get(nombre='Básico')
        membresia_basica.prioridad_visibilidad = 30
        membresia_basica.save()
    except Membresia.DoesNotExist:
        pass

def revertir_prioridades(apps, schema_editor):
    Membresia = apps.get_model('admin_alpatex', 'Membresia')
    
    # Revertir membresía Oro
    try:
        membresia_oro = Membresia.objects.get(nombre='Oro')
        membresia_oro.prioridad_visibilidad = 10
        membresia_oro.save()
    except Membresia.DoesNotExist:
        pass

    # Revertir membresía Plata
    try:
        membresia_plata = Membresia.objects.get(nombre='Plata')
        membresia_plata.prioridad_visibilidad = 20
        membresia_plata.save()
    except Membresia.DoesNotExist:
        pass

    # Revertir membresía Básica
    try:
        membresia_basica = Membresia.objects.get(nombre='Básico')
        membresia_basica.prioridad_visibilidad = 30
        membresia_basica.save()
    except Membresia.DoesNotExist:
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('admin_alpatex', '0002_alter_membresia_prioridad_visibilidad'),
    ]

    operations = [
        migrations.RunPython(actualizar_prioridades, revertir_prioridades),
    ] 