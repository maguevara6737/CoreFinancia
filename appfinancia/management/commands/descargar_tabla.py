# appfinancia/management/commands/descargar_tabla.py

import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import models

class Command(BaseCommand):
    help = 'Exporta todos los registros de un modelo a un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'modelo',
            type=str,
            help='Nombre del modelo a exportar (ej: Historia_Prestamos, Prestamos, Desembolsos)'
        )
        parser.add_argument(
            '--app',
            type=str,
            default='appfinancia',
            help='Nombre de la aplicación donde está el modelo (por defecto: appfinancia)'
        )

    def handle(self, *args, **options):
        nombre_modelo = options['modelo']
        nombre_app = options['app']

        try:
            modelo = apps.get_model(nombre_app, nombre_modelo)
        except LookupError:
            raise CommandError(
                f"No se encontró el modelo '{nombre_modelo}' en la app '{nombre_app}'.\n"
                "Asegúrate de que el nombre esté escrito exactamente como en la definición de la clase (incluyendo mayúsculas)."
            )

        count = modelo.objects.count()
        if count == 0:
            self.stdout.write(self.style.WARNING(f"⚠️ El modelo '{nombre_modelo}' no tiene registros."))
            return

        # Nombre del archivo CSV
        nombre_archivo = f"export_{nombre_app}_{nombre_modelo.lower()}.csv"
        ruta_archivo = os.path.join(os.getcwd(), nombre_archivo)

        # Obtener todos los campos (incluyendo FK)
        nombres_columnas = [field.name for field in modelo._meta.fields]

        self.stdout.write(f"Exportando {count} registros de '{nombre_app}.{nombre_modelo}'...")

        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(nombres_columnas)

                # Usamos iterator() para no cargar todo en memoria si hay muchos registros
                for obj in modelo.objects.all().iterator():
                    fila = []
                    for field in modelo._meta.fields:
                        valor = getattr(obj, field.name)
                        if valor is None:
                            fila.append('')
                        elif isinstance(field, models.ForeignKey):
                            # Exportar la PK del objeto relacionado
                            fila.append(str(valor.pk) if valor else '')
                        else:
                            # Convertir a string y manejar caracteres especiales
                            fila.append(str(valor))
                    writer.writerow(fila)

            self.stdout.write(
                self.style.SUCCESS(f"✅ Exportación completada: '{ruta_archivo}'")
            )

        except Exception as e:
            raise CommandError(f"Error al escribir el archivo CSV: {e}")