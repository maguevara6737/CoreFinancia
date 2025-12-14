# appfinancia/management/commands/descargar_tabla.py

import csv
import os
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models

# === CONFIGURACIÓN: CAMBIA ESTO ===
NOMBRE_MODELO = "Acumulado_Interes"  # ← Cambia por el nombre de tu modelo (ej: "Prestamos", "Desembolsos", etc.)
NOMBRE_APP = "appfinancia"            # ← Nombre de tu aplicación Django
# =================================

class Command(BaseCommand):
    help = 'Exporta todos los registros de un modelo a un archivo CSV'

    def handle(self, *args, **options):
        try:
            # Obtener el modelo dinámicamente
            modelo = apps.get_model(NOMBRE_APP, NOMBRE_MODELO)
        except LookupError:
            self.stderr.write(
                self.style.ERROR(
                    f"Error: No se encontró el modelo '{NOMBRE_MODELO}' en la app '{NOMBRE_APP}'."
                )
            )
            return

        # Nombre del archivo CSV
        nombre_archivo = f"export_{NOMBRE_MODELO.lower()}.csv"
        ruta_archivo = os.path.join(os.getcwd(), nombre_archivo)

        # Obtener todos los campos del modelo (solo campos de base de datos)
        campos = [field for field in modelo._meta.fields if not isinstance(field, models.ForeignKey)]
        campos_fk = [field for field in modelo._meta.fields if isinstance(field, models.ForeignKey)]

        # Lista de nombres de columnas
        nombres_columnas = [field.name for field in modelo._meta.fields]

        self.stdout.write(f"Exportando {modelo.objects.count()} registros de '{NOMBRE_MODELO}'...")

        # Escribir CSV
        with open(ruta_archivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Escribir encabezados
            writer.writerow(nombres_columnas)

            # Escribir filas
            for obj in modelo.objects.all().iterator():
                fila = []
                for field in modelo._meta.fields:
                    valor = getattr(obj, field.name)
                    if valor is None:
                        fila.append('')
                    elif isinstance(valor, models.Model):
                        # Para ForeignKey, exportar la PK (o str si prefieres)
                        fila.append(str(valor.pk))
                    else:
                        # Convertir a string y manejar comas/saltos si es necesario
                        fila.append(str(valor))
                writer.writerow(fila)

        self.stdout.write