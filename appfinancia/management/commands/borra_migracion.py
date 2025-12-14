import os
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from appfinancia.models import (
    Clientes, Desembolsos, Prestamos, Movimientos, Historia_Prestamos,
    Pagos, Detalle_Aplicacion_Pago, Migrados
)


class Command(BaseCommand):
    help = 'Borra todos los registros creados por la migración. Usa "MIGRACION" en Pagos y Migrados. Limpia Historia_Prestamos de forma exhaustiva.'

    def handle(self, *args, **options):
        log_filename = f"borrado_migracion_{datetime.now().strftime('%Y%m%d%H%M')}.log"
        log_path = os.path.join('appfinancia/logs', log_filename)
        os.makedirs('appfinancia/logs', exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("=== INICIANDO BORRADO DE MIGRACIÓN (limpieza exhaustiva) ===")

        try:
            with transaction.atomic():
                # === 1. Identificar préstamos migrados desde Migrados ===
                prestamo_ids_migrados = list(Migrados.objects.values_list('prestamo_id', flat=True))
                logger.info(f"🔍 Préstamos en Migrados: {len(prestamo_ids_migrados)}")

                # === 2. Identificar pagos de migración ===
                pagos_migracion = Pagos.objects.filter(nombre_archivo_id='MIGRACION')
                pago_ids_migracion = list(pagos_migracion.values_list('pago_id', flat=True))
                logger.info(f"🔍 Pagos marcados como 'MIGRACION': {len(pago_ids_migracion)}")

                # === 3. BORRAR Historia_Prestamos de forma EXHAUSTIVA ===
                # a) Por número de operación (pagos aplicados)
                if pago_ids_migracion:
                    historia_por_pago, _ = Historia_Prestamos.objects.filter(
                        numero_operacion__in=pago_ids_migracion
                    ).delete()
                else:
                    historia_por_pago = 0

                # b) Por préstamo en Migrados (cuotas, causaciones, etc.)
                if prestamo_ids_migrados:
                    # Obtener instancias de Prestamos para filtrar correctamente
                    from appfinancia.models import Prestamos
                    prestamos_instancias = Prestamos.objects.filter(
                        prestamo_id__in=prestamo_ids_migrados
                    )
                    historia_por_prestamo, _ = Historia_Prestamos.objects.filter(
                        prestamo_id__in=prestamos_instancias
                    ).delete()
                else:
                    historia_por_prestamo = 0

                total_historia_borrada = historia_por_pago + historia_por_prestamo
                logger.info(f"✅ Historia_Prestamos borrada: {historia_por_pago} (por pago) + {historia_por_prestamo} (por préstamo) = {total_historia_borrada}")

                # === 4. Borrar detalles y pagos ===
                detalles_borrados, _ = Detalle_Aplicacion_Pago.objects.filter(pago_id__in=pago_ids_migracion).delete()
                pagos_borrados, _ = Pagos.objects.filter(pago_id__in=pago_ids_migracion).delete()

                # === 5. Obtener todos los préstamos a borrar (de Migrados + de pagos) ===
                prestamo_ids_desde_pagos = set(pagos_migracion.values_list('prestamo_id_real', flat=True).distinct())
                todos_prestamos_a_borrar = set(prestamo_ids_migrados) | prestamo_ids_desde_pagos

                # === 6. Borrar Movimientos, Prestamos, Desembolsos ===
                movimientos_borrados = 0
                if todos_prestamos_a_borrar:
                    desembolsos_para_mov = Desembolsos.objects.filter(prestamo_id__in=todos_prestamos_a_borrar)
                    for d in desembolsos_para_mov:
                        borrados, _ = Movimientos.objects.filter(
                            cliente_id=d.cliente_id,
                            fecha_valor_mvto=d.fecha_desembolso,
                            valor_movimiento=d.valor
                        ).delete()
                        movimientos_borrados += borrados

                    prestamos_borrados, _ = Prestamos.objects.filter(prestamo_id__in=todos_prestamos_a_borrar).delete()
                    desembolsos_borrados, _ = Desembolsos.objects.filter(prestamo_id__in=todos_prestamos_a_borrar).delete()
                else:
                    prestamos_borrados = desembolsos_borrados = 0

                # === 7. Borrar Migrados ===
                migrados_borrados, _ = Migrados.objects.all().delete()

                logger.info("=== BORRADO COMPLETADO ===")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Limpieza exhaustiva completada:\n"
                        f"  - Préstamos en Migrados: {len(prestamo_ids_migrados)}\n"
                        f"  - Pagos 'MIGRACION': {len(pago_ids_migracion)}\n"
                        f"  - Historia_Prestamos borrada: {total_historia_borrada}\n"
                        f"    - Por numero_operacion: {historia_por_pago}\n"
                        f"    - Por préstamo migrado: {historia_por_prestamo}\n"
                        f"  - Detalles de pago borrados: {detalles_borrados}\n"
                        f"  - Pagos borrados: {pagos_borrados}\n"
                        f"  - Desembolsos borrados: {desembolsos_borrados}\n"
                        f"  - Prestamos borrados: {prestamos_borrados}\n"
                        f"  - Movimientos borrados: {movimientos_borrados}\n"
                        f"  - Migrados eliminados: {migrados_borrados}\n"
                        f"📁 Log: {log_path}"
                    )
                )

        except Exception as e:
            logger.error(f"❌ Error durante el borrado: {e}")
            self.stdout.write(self.style.ERROR(f"❌ Falló el borrado: {e}"))