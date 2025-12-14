

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appfinancia', '0047_pagos_archivos_pagos'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pagos_archivos',
            name='creado_por',
        ),
        migrations.DeleteModel(
            name='Pagos',
        ),
        migrations.DeleteModel(
            name='Pagos_Archivos',
        ),
    ]
