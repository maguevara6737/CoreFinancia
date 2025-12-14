# appfinancia/management/commands/corregir_desembolsos.py

from django.core.management.base import BaseCommand
from django.db import transaction
from appfinancia.models import Desembolsos

class Command(BaseCommand):
    help = 'Asigna una secuencia única a numero_transaccion_cuota_1 en Desembolsos con prestamo_id >= 90000'

    def handle(self, *args, **options):
        # Obtener todos los desembolsos con prestamo_id >= 90000
        desembolsos = Desembolsos.objects.filter(prestamo_id__gte=90000).order_by('prestamo_id')

        if not desembolsos.exists():
            self.stdout.write(self.style.WARNING("No se encontraron desembolsos con prestamo_id >= 90000."))
            return

        total = desembolsos.count()
        self.stdout.write(f"Encontrados {total} desembolsos para actualizar.")

        secuencia_inicial = 80000

        try:
            with transaction.atomic():
                updated_count = 0
                for idx, desembolso in enumerate(desembolsos):
                    nuevo_valor = secuencia_inicial + idx
                    desembolso.numero_transaccion_cuota_1 = str(nuevo_valor)
                    desembolso.save(update_fields=['numero_transaccion_cuota_1'])
                    updated_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Se actualizaron {updated_count} registros. "
                        f"Secuencia asignada desde {secuencia_inicial} hasta {secuencia_inicial + updated_count - 1}."
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error durante la actualización: {e}"))
            raise