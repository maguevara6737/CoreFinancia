# appfinancia/management/commands/reportar_devengamiento.py
# forma de uso para solo emitir totales por la consola:
#        python manage.py reportar_devengamiento 2025-09-01 2025-09-30 
#Con total + detalle, muestra por consola
#        python manage.py reportar_devengamiento 2025-09-01 2025-09-30 --detalle
#para csv:
    
#
import csv
import os
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from datetime import datetime
from appfinancia.utils import total_intereses_por_periodo


class Command(BaseCommand):
    help = 'Reporta el devengamiento (causación) de intereses en un periodo dado.'
    


    def add_arguments(self, parser):
        parser.add_argument(
            'fecha_inicio',
            type=str,
            help='Fecha de inicio en formato YYYY-MM-DD'
        )
        parser.add_argument(
            'fecha_fin',
            type=str,
            help='Fecha de fin en formato YYYY-MM-DD'
        )
        parser.add_argument(
            '--detalle',
            action='store_true',
            help='Mostrar desglose detallado por préstamo y periodo en consola'
        )
        parser.add_argument(
            '--csv',
            type=str,
            help='Ruta del archivo CSV de salida (ej. reporte_devengamiento.csv)'
        )

    def handle(self, *args, **options):
        try:
            fecha_inicio = datetime.strptime(options['fecha_inicio'], '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(options['fecha_fin'], '%Y-%m-%d').date()

            if fecha_inicio > fecha_fin:
                self.stderr.write(
                    self.style.ERROR("❌ La fecha de inicio no puede ser posterior a la fecha de fin.")
                )
                return
        except ValueError:
            self.stderr.write(
                self.style.ERROR("❌ Formato de fecha inválido. Use YYYY-MM-DD.")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"🔍 Calculando devengamiento desde {fecha_inicio} hasta {fecha_fin}...")
        )

        try:
            resultado = total_intereses_por_periodo(fecha_inicio, fecha_fin)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error al calcular devengamiento: {e}"))
            return

        total = resultado['total_intereses']
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ TOTAL INTERESES DEVENGADOS: ${total:,.2f}\n")
        )

        # === Opción 1: Mostrar en consola (detalle) ===
        if options['detalle']:
            detalle = resultado['detalle_por_prestamo']
            if not detalle:
                self.stdout.write("ℹ️  No se encontraron préstamos activos con devengamiento en el periodo.")
            else:
                for prestamo_id, periodos in detalle.items():
                    self.stdout.write(f"\nPrestamo ID: {prestamo_id}")
                    self.stdout.write("-" * 80)
                    for p in periodos:
                        self.stdout.write(
                            f"  {p['periodo_inicio']} a {p['periodo_fin']} "
                            f"({p['dias']} días) | "
                            f"Saldo: ${p['saldo_inicial']:,.2f} | "
                            f"Tasa: {p['tasa']:.4f}% | "
                            f"Interés: ${p['interes_causado']:,.2f} "
                            f"[{p['tipo_evento']}]"
                        )
                self.stdout.write("\n✔️ Reporte detallado finalizado.")

        # === Opción 2: Exportar a CSV ===
        if options['csv']:
            csv_path = options['csv']
            try:
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # Cabecera
                    writer.writerow([
                        'prestamo_id',
                        'periodo_inicio',
                        'periodo_fin',
                        'dias',
                        'saldo_inicial',
                        'tasa',
                        'interes_causado',
                        'tipo_evento'
                    ])
                    # Datos
                    for prestamo_id, periodos in resultado['detalle_por_prestamo'].items():
                        for p in periodos:
                            writer.writerow([
                                prestamo_id,
                                p['periodo_inicio'],
                                p['periodo_fin'],
                                p['dias'],
                                f"{p['saldo_inicial']:.2f}",
                                f"{p['tasa']:.6f}",
                                f"{p['interes_causado']:.2f}",
                                p['tipo_evento']
                            ])
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Reporte exportado a: {os.path.abspath(csv_path)}")
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Error al guardar CSV: {e}"))

        self.stdout.write(self.style.SUCCESS("✔️ Proceso completado."))
        