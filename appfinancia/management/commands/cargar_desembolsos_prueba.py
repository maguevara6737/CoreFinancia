# appfinancia/management/commands/cargar_desembolsos_prueba.py
# 1. Ejecuta en terminal: python manage.py cargar_desembolsos_prueba
#Para limpiar después (opcional) borrar los regs creados por este comando:
#    python manage.py shell
#     from appfinancia.models import Desembolsos
#     Desembolsos.objects.filter(prestamo_id__gte=10000, prestamo_id__lt=10020).delete()  

#prestamo_id: uso un rango 10000–10019 para evitar colisiones. Si ya tienes préstamos con IDs altos, ajusta el valor inicial (ej: 20000 + i).    

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now
from appfinancia.models import (
    Clientes, Asesores, Aseguradoras, Vendedores, Tasas,
    Desembolsos, Fechas_Sistema
)

class Command(BaseCommand):
    help = 'Carga 20 desembolsos de prueba usando registros existentes en la BD.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando carga de desembolsos de prueba...")

        # === 1. Verificar que existan registros mínimos ===
        if not Clientes.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No hay clientes en la base de datos."))
            return
        if not Asesores.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No hay asesores en la base de datos."))
            return
        if not Aseguradoras.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No hay aseguradoras en la base de datos."))
            return
        if not Vendedores.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No hay vendedores en la base de datos."))
            return
        if not Tasas.objects.exists():
            self.stdout.write(self.style.ERROR("❌ No hay tasas en la base de datos."))
            return

        # === 2. Obtener listas de IDs existentes (más eficiente que traer objetos completos) ===
        clientes_ids = list(Clientes.objects.values_list('cliente_id', flat=True))
        asesores_ids = list(Asesores.objects.values_list('asesor_id', flat=True))
        aseguradoras_ids = list(Aseguradoras.objects.values_list('aseguradora_id', flat=True))
        vendedores_ids = list(Vendedores.objects.values_list('cod_venta_id', flat=True))
        tasas_tipos = list(Tasas.objects.values_list('tipo_tasa', flat=True))

        self.stdout.write(f"✅ Seleccionando entre {len(clientes_ids)} clientes, {len(asesores_ids)} asesores, etc.")

        # === 3. Fecha base ===
        try:
            fecha_base = Fechas_Sistema.load().fecha_proceso_actual
        except Exception:
            self.stdout.write(self.style.WARNING("No se encontró Fechas_Sistema. Usando fecha actual."))
            fecha_base = now().date()

        # === 4. Valores de prueba ===
        montos = [410_675, 324_381, 620_399, 745_888, 859_232, 940_333, 1_340_010, 1_530_525, 2_124_666, 2_321_000, 3_123_456, 5_000_000, 10_000_000]
        tasas = [8.50, 10.00, 12.50, 15.00, 18.00, 20.40, 21.6, 24.00]
        plazos = [3,4, 6, 8, 10, 12, 18, 24, 36]
        dias_cobro = [1, 6, 12, 15, 20, 25, 28, 30]

        # === 5. Crear desembolsos ===
        with transaction.atomic():
            creados = 0
            for i in range(30):
                # Generar fecha de desembolso
                dias_atras = random.randint(0, 90)
                fecha_desembolso = fecha_base - timedelta(days=dias_atras)

                from dateutil.relativedelta import relativedelta
                plazo = random.choice(plazos)
                fecha_vencimiento = fecha_desembolso + relativedelta(months=plazo)
                valor_desembolso = random.choice(montos)
                # Generar un prestamo_id único (ajusta el rango si es necesario)
                prestamo_id = 90020 + i  # Asegúrate de que no exista

                desembolso = Desembolsos.objects.create(
                    prestamo_id=prestamo_id,
                    cliente_id_id=random.choice(clientes_ids),        # ← nota el _id
                    asesor_id_id=random.choice(asesores_ids),         # ← nota el _id
                    aseguradora_id_id=random.choice(aseguradoras_ids),# ← nota el _id
                    vendedor_id_id=random.choice(vendedores_ids),     # ← nota el _id
                    tipo_tasa_id=random.choice(tasas_tipos),          # ← nota el _id
                    tasa=random.choice(tasas),
                    valor=valor_desembolso,
                    valor_cuota_1=round(valor_desembolso * 0.20),
                    numero_transaccion_cuota_1="88888",
                    valor_cuota_mensual=0,
                    valor_seguro_mes=round(valor_desembolso * 0.04),
                    tiene_fee=random.choice(['SI', 'NO']),
                    dia_cobro=random.choice(dias_cobro),
                    plazo_en_meses=plazo,
                    fecha_desembolso=fecha_desembolso,
                    fecha_vencimiento=fecha_vencimiento,
                    estado='ELABORACION',
                    fecha_creacion=now()
                )
                creados += 1
                self.stdout.write(
                    f"✅ Desembolso {i+1}/20: ID={desembolso.prestamo_id}, "
                    f"Cliente={desembolso.cliente_id_id}, Monto={desembolso.valor:,}"
                )

            self.stdout.write(
                self.style.SUCCESS(f"✅ ¡{creados} desembolsos de prueba creados exitosamente!")
            )
            self.stdout.write("💡 Para eliminarlos después:")
            self.stdout.write("   from appfinancia.models import Desembolsos")
            self.stdout.write("   Desembolsos.objects.filter(prestamo_id__gte=90000, prestamo_id__lt=90020).delete()")