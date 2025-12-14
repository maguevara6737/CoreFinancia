# appfinancia/management/commands/pagos_prueba.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from appfinancia.models import Desembolsos, Pagos, Pagos_Archivos

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea pagos de prueba a partir de Desembolsos con prestamo_id >= 90000'

    def handle(self, *args, **options):
        # Obtener superusuario
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            raise SystemExit("❌ No se encontró un superusuario. Ejecuta 'createsuperuser'.")

        # Nombre fijo del archivo
        nombre_archivo_id = "pagos pse 2025_3"
        archivo_obj, _ = Pagos_Archivos.objects.get_or_create(
            nombre_archivo_id=nombre_archivo_id,
            defaults={'descripcion': 'Pagos de prueba generados vía comando pagos_prueba'}
        )

        # Filtrar desembolsos
        desembolsos = Desembolsos.objects.filter(prestamo_id__gte=90000)

        if not desembolsos.exists():
            self.stdout.write(self.style.WARNING("No hay desembolsos con prestamo_id >= 90000."))
            return

        total = desembolsos.count()
        self.stdout.write(f"🔎 Encontrados {total} desembolsos candidatos.")

        try:
            with transaction.atomic():
                creados = 0
                for des in desembolsos:
                    # Validar que los campos necesarios existan
                    if des.valor_cuota_1 is None or des.numero_transaccion_cuota_1 is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Desembolso {des.prestamo_id}: faltan valor_cuota_1 o numero_transaccion_cuota_1. Omitido."
                            )
                        )
                        continue

                    # Asegurar que prestamo_id_real sea un entero (BigIntegerField)
                    try:
                        prestamo_id_real = int(des.prestamo_id)
                    except (TypeError, ValueError):
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Desembolso {des.prestamo_id}: prestamo_id no es convertible a entero. Omitido."
                            )
                        )
                        continue

                    # Crear el pago
                    Pagos.objects.create(
                        nombre_archivo_id=archivo_obj,
                        fecha_carga_archivo=timezone.now(),
                        ref_bancaria=str(des.numero_transaccion_cuota_1)[:100],
                        fecha_pago=des.fecha_desembolso,
                        hora_pago=timezone.now().time(),  # usa hora actual si no tienes campo en Desembolsos
                        valor_pago=Decimal(str(des.valor_cuota_1)).quantize(Decimal('0.01')),
                        prestamo_id_real=prestamo_id_real,
                        cliente_id_real=None,  # opcional: podrías obtenerlo si existe relación
                        poliza_id_real="",
                        estado_pago="conciliado",
                        canal_red_pago="PSE",
                        cuenta_bancaria="PRUEBAS",
                        tipo_cuenta_bancaria="",  # opcional
                        banco_origen="",
                        ref_red="",
                        ref_cliente_1="",
                        ref_cliente_2="",
                        ref_cliente_3="",
                        estado_transaccion_reportado="",
                        cliente_id_reportado="",
                        prestamo_id_reportado="",
                        poliza_id_reportado="",
                        estado_conciliacion="",
                        creado_por=admin_user,
                    )
                    creados += 1

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Se crearon {creados} pagos de prueba.")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            raise