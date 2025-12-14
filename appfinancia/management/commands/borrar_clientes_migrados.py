from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from appfinancia.models import Clientes, Prestamos

class Command(BaseCommand):
    help = 'Borra los clientes migrados (identificados por fecha_nacimiento = 1900-01-01)'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Identificar clientes migrados
                clientes_migrados = Clientes.objects.filter(fecha_nacimiento=date(1900, 1, 1))
                total = clientes_migrados.count()
                if total == 0:
                    self.stdout.write(self.style.WARNING("⚠️ No se encontraron clientes migrados para borrar."))
                    return

                # Verificar si alguno tiene préstamos (usando consulta explícita)
                clientes_con_prestamos = []
                for cliente in clientes_migrados:
                    if Prestamos.objects.filter(cliente_id=cliente.cliente_id).exists():
                        clientes_con_prestamos.append(cliente.cliente_id)

                if clientes_con_prestamos:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ {len(clientes_con_prestamos)} clientes migrados tienen préstamos y no se pueden borrar: {clientes_con_prestamos}"
                        )
                    )
                    return

                # Borrar solo si ninguno tiene préstamos
                borrados, _ = clientes_migrados.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Se borraron {borrados} clientes migrados.")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al borrar clientes migrados: {e}"))