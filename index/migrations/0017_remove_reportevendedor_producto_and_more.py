# Generated by Django 5.2 on 2025-05-29 02:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('index', '0016_reportevendedor_puntaje'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reportevendedor',
            name='producto',
        ),
        migrations.RemoveField(
            model_name='reportevendedor',
            name='puntaje',
        ),
    ]
