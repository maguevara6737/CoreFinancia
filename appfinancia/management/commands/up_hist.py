from django.core.management.base import BaseCommand
from decimal import Decimal
from appfinancia.models import Historia_Prestamos


class Command(BaseCommand):
    help = 'Actualiza registros específicos en Historia_Prestamos: capital_aplicado_periodo y numero_pago_referencia'

    def handle(self, *args, **options):
        # Registro 1
        try:
            registro1 = Historia_Prestamos.objects.get(id=1064)
            registro1.capital_aplicado_periodo = Decimal('464200.00')
            registro1.numero_pago_referencia = "PAGO_nnn"
            registro1.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Registro id=1064 actualizado: capital_aplicado_periodo=464200.00, numero_pago_referencia='PAGO_nnn'"
                )
            )
        except Historia_Prestamos.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Registro id=1064 no encontrado.")
            )

        # Registro 2
        try:
            registro2 = Historia_Prestamos.objects.get(id=1566)
            registro2.capital_aplicado_periodo = Decimal('65883.27')
            registro2.numero_pago_referencia = "PAGO_mmm"
            registro2.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Registro id=1566 actualizado: capital_aplicado_periodo=65883.27, numero_pago_referencia='PAGO_mmm'"
                )
            )
        except Historia_Prestamos.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("❌ Registro id=1566 no encontrado.")
            )

        self.stdout.write(self.style.SUCCESS("✔️ Actualización completada."))