# appfinancia/management/commands/crear_detalle_aplicacion.py

from django.core.management.base import BaseCommand
from appfinancia.models import Detalle_Aplicacion_Pago, Pagos, Historia_Prestamos
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = 'Crea un registro en Detalle_Aplicacion_Pago'

    def handle(self, *args, **options):
        try:
            # 🔢 Datos de entrada
            pago_id_valor = 1015           # ← PK de Pagos (pago_id)
            historia_id_valor = 1405       # ← PK implícita de Historia_Prestamos (id)
            monto_aplicado = Decimal('1000000.00')
            componente = "CAPITAL"
            fecha_aplicacion_str = "2025-12-21 02:10:33.643688+00:00"
            fecha_aplicacion = datetime.fromisoformat(fecha_aplicacion_str)

            # 🔍 Obtener instancias usando las PK correctas
            pago = Pagos.objects.get(pago_id=pago_id_valor)
            historia = Historia_Prestamos.objects.get(id=historia_id_valor)  # ← ¡usamos 'id'!

            # ✍️ Crear el detalle
            detalle = Detalle_Aplicacion_Pago.objects.create(
                pago=pago,
                historia_prestamo=historia,
                monto_aplicado=monto_aplicado,
                componente=componente,
                fecha_aplicacion=fecha_aplicacion
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Detalle creado: ID={detalle.id} | Pago={pago.pago_id} | "
                    f"Historia ID={historia.id} (Cuota {historia.numero_cuota})"
                )
            )

        except Pagos.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"❌ Pago con pago_id={pago_id_valor} no existe"))
        except Historia_Prestamos.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"❌ Historia_Prestamos con id={historia_id_valor} no existe"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"💥 Error inesperado: {e}"))