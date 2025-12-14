# appfinancia/management/commands/validar_prestamo_90008.py

from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from appfinancia.models import (
    Prestamos,
    Fechas_Sistema,
    Historia_Prestamos,
    Conceptos_Transacciones,
    Detalle_Aplicacion_Pago
)

class Command(BaseCommand):
    help = 'Valida los cálculos para el préstamo #90008 (ABRAHAM MORRISSON)'

    def handle(self, *args, **options):
        prestamo_id = 90008

        self.stdout.write(self.style.SUCCESS(f"\n🔍 Validando préstamo ID: {prestamo_id}"))
        self.stdout.write("=" * 60)

        # 1. Fecha de corte
        fecha_sistema = Fechas_Sistema.objects.first()
        if not fecha_sistema:
            self.stdout.write(self.style.ERROR("❌ No hay fecha de sistema definida."))
            return
        fecha_corte = fecha_sistema.fecha_proceso_actual
        self.stdout.write(f"📅 Fecha de corte: {fecha_corte}")

        # 2. Obtener IDs de conceptos
        try:
            cap_id = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
            int_id = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
            seg_id = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
            gto_id = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
            causac_id = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
            conceptos_validos = [cap_id, int_id, seg_id, gto_id]
            causac_concepto = causac_id
        except Conceptos_Transacciones.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"❌ Error con conceptos: {e}"))
            return

        # 3. Obtener el préstamo
        try:
            prestamo = Prestamos.objects.get(prestamo_id=prestamo_id)
            self.stdout.write(f"👤 Cliente: {prestamo.cliente_id}")
        except Prestamos.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Préstamo {prestamo_id} no encontrado."))
            return

        # 4. Historia_Prestamos: agrupar por fecha_vencimiento
        self.stdout.write("\n📊 HISTORIA DE PRÉSTAMOS (solo PLANCAP, PLANINT, PLANSEG, PLANGTO):")
        self.stdout.write("-" * 80)

        # Obtener todas las fechas de vencimiento únicas con conceptos válidos
        fechas_vencimiento = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo,
            concepto_id__in=conceptos_validos
        ).values_list('fecha_vencimiento', flat=True).distinct().order_by('fecha_vencimiento')

        total_programado_global = Decimal('0.00')
        total_pagado_global = Decimal('0.00')
        cuotas_atrasadas_fechas = []

        for fecha in fechas_vencimiento:
            cuota_qs = Historia_Prestamos.objects.filter(
                prestamo_id=prestamo,
                fecha_vencimiento=fecha,
                concepto_id__in=conceptos_validos
            )

            monto_cuota = cuota_qs.aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')
            total_programado_global += monto_cuota

            # ¿Está atrasada?
            atrasada = fecha < fecha_corte

            # ¿Está pagada?
            detalles = Detalle_Aplicacion_Pago.objects.filter(
                historia_prestamo__in=cuota_qs
            )
            monto_pagado = detalles.aggregate(total=Sum('monto_aplicado'))['total'] or Decimal('0.00')
            total_pagado_global += monto_pagado

            if atrasada:
                cuotas_atrasadas_fechas.append(fecha)

            estado_pago = "PAGADA" if monto_pagado >= monto_cuota else "PENDIENTE" if monto_pagado == 0 else "PARCIAL"
            estado_atraso = "ATRASADA" if atrasada else "AL DÍA"

            self.stdout.write(
                f"Fecha: {fecha} | Monto: ${monto_cuota:,.2f} | Pagado: ${monto_pagado:,.2f} | "
                f"{estado_pago} | {estado_atraso}"
            )

        # 5. Calcular días de atraso
        dias_atraso = 0
        if cuotas_atrasadas_fechas:
            ultima_atrasada = max(cuotas_atrasadas_fechas)
            dias_atraso = (fecha_corte - ultima_atrasada).days

        # 6. Resultados finales
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("✅ RESULTADOS VALIDADOS:")
        self.stdout.write(f"• Cuotas atrasadas: {len(cuotas_atrasadas_fechas)}")
        self.stdout.write(f"• Días de atraso: {dias_atraso}")
        self.stdout.write(f"• Total programado (todas las cuotas): ${total_programado_global:,.2f}")
        self.stdout.write(f"• Total pagado: ${total_pagado_global:,.2f}")
        self.stdout.write(f"• Saldo pendiente actual: ${total_programado_global - total_pagado_global:,.2f}")

        # 7. Comparar con los métodos actuales del modelo
        self.stdout.write("\n🔍 Comparación con métodos del modelo:")
        saldo_modelo = prestamo.saldo_pendiente_actual()
        monto_atrasado_modelo = prestamo.monto_atrasado()
        cuotas_atrasadas_modelo, dias_atraso_modelo = prestamo.cuotas_atrasadas_info()

        self.stdout.write(f"• saldo_pendiente_actual() → ${saldo_modelo:,.2f}")
        self.stdout.write(f"• monto_atrasado() → ${monto_atrasado_modelo:,.2f}")
        self.stdout.write(f"• cuotas_atrasadas_info() → ({cuotas_atrasadas_modelo}, {dias_atraso_modelo})")

        self.stdout.write("\n💡 Si los valores no coinciden, los métodos del modelo necesitan ajustes.")