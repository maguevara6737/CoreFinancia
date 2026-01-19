from django.core.management.base import BaseCommand
from datetime import date
from appfinancia.models import Historia_Prestamos

class Command(BaseCommand):
    help = 'Corrige fechas de vencimiento del préstamo 90035: cambia día 28 → 30 (excepto febrero)'

    def handle(self, *args, **options):
        MESES_SIN_30 = {2}
        registros = Historia_Prestamos.objects.filter(
            prestamo_id__prestamo_id=90035,
            fecha_vencimiento__day=28
        )
        self.stdout.write(
            self.style.SUCCESS("🔄 Actualizando fechas a día 30 (excepto febrero)...")
        )
        actualizados = 0

        for reg in registros:
            fv = reg.fecha_vencimiento
            fv_date = fv.date() if hasattr(fv, 'date') else fv

            if fv_date.month in MESES_SIN_30:
                self.stdout.write(f"  ℹ️  ID {reg.id}: {fv_date} → febrero, omitido")
                continue

            try:
                nueva_fecha = date(fv_date.year, fv_date.month, 30)
                if nueva_fecha != fv_date:
                    reg.fecha_vencimiento = nueva_fecha
                    reg.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ ID {reg.id}: {fv_date} → {nueva_fecha}")
                    )
                    actualizados += 1
                else:
                    self.stdout.write(f"  ℹ️  ID {reg.id}: ya es {fv_date}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error en ID {reg.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Total actualizados: {actualizados}"))