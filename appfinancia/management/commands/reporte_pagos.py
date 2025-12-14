import os
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from appfinancia.models import Pagos

class Command(BaseCommand):
    help = 'Genera un reporte CSV de los pagos de un préstamo específico, listo para Excel.'

    def add_arguments(self, parser):
        parser.add_argument(
            'prestamo_id',
            type=int,
            help='ID del préstamo (prestamo_id_real) para generar el reporte.'
        )

    def handle(self, *args, **options):
        prestamo_id = options['prestamo_id']

        # Verificar que existan pagos para ese préstamo
        pagos = Pagos.objects.filter(prestamo_id_real=prestamo_id).order_by('fecha_pago')
        if not pagos.exists():
            self.stdout.write(
                self.style.WARNING(f"No se encontraron pagos para el préstamo {prestamo_id}.")
            )
            return

        # Crear directorio de reportes si no existe
        reportes_dir = os.path.join(settings.BASE_DIR, 'appfinancia', 'reportes')
        os.makedirs(reportes_dir, exist_ok=True)

        # Nombre del archivo
        filename = f"reporte_pagos_prestamo_{prestamo_id}.csv"
        filepath = os.path.join(reportes_dir, filename)

        # Escribir CSV
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)

            # Encabezados (en español, claros para Excel)
            writer.writerow([
                'ID Pago',
                'ID Préstamo',
                'ID Cliente',
                'Fecha Pago',
                'Hora Pago',
                'Valor Pago',
                'Estado Pago',
                'Archivo Origen',
                'Creado Por',
                'Fecha Aplicación',
                'Fecha Conciliación'
            ])

            for pago in pagos:
                # Formatear fecha como yyyy-mm-dd (Excel lo reconoce)
                fecha_pago = pago.fecha_pago.strftime('%Y-%m-%d') if pago.fecha_pago else ''
                fecha_aplicacion = pago.fecha_aplicacion_pago.strftime('%Y-%m-%d') if pago.fecha_aplicacion_pago else ''
                fecha_conciliacion = pago.fecha_conciliacion.strftime('%Y-%m-%d') if pago.fecha_conciliacion else ''

                # Formatear monto con separador de miles y 2 decimales
                valor_pago = "{:,.2f}".format(pago.valor_pago) if pago.valor_pago else "0.00"

                writer.writerow([
                    pago.pago_id,
                    pago.prestamo_id_real,
                    pago.cliente_id_real or '',
                    fecha_pago,
                    pago.hora_pago or '',
                    valor_pago,
                    pago.estado_pago,
                    pago.nombre_archivo_id or '',
                    pago.creado_por.username if pago.creado_por else '',
                    fecha_aplicacion,
                    fecha_conciliacion
                ])

        self.stdout.write(
            self.style.SUCCESS(f"✅ Reporte generado: {filepath}")
        )