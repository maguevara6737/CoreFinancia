# appfinancia/management/commands/borra_asesores_repetidos.py

from django.core.management.base import BaseCommand
from django.db.models import Count
from appfinancia.models import Asesores, Aseguradoras, Desembolsos


class Command(BaseCommand):
    help = "Elimina registros duplicados en Asesores y Aseguradoras que no tengan desembolsos asociados."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔍 Iniciando limpieza de duplicados..."))

        # Limpiar Asesores duplicados
        self.limpiar_duplicados(
            modelo=Asesores,
            campo_nombre='asesor_nombre',
            campo_pk='asesor_id',          # ← campo primario
            campo_fk='asesor_id'           # ← campo ForeignKey en Desembolsos
        )

        # Limpiar Aseguradoras duplicadas
        self.limpiar_duplicados(
            modelo=Aseguradoras,
            campo_nombre='aseguradora_nombre',
            campo_pk='aseguradora_id',     # ← campo primario
            campo_fk='aseguradora_id'      # ← campo ForeignKey en Desembolsos
        )

        self.stdout.write(self.style.SUCCESS("✅ Limpieza completada."))

    def limpiar_duplicados(self, modelo, campo_nombre, campo_pk, campo_fk):
        """Elimina duplicados basados en un campo de nombre, solo si no tienen desembolsos."""
        # Encontrar nombres duplicados: ¡usar campo_pk en lugar de 'id'!
        duplicados = (
            modelo.objects
            .values(campo_nombre)
            .annotate(count=Count(campo_pk))  # ← CORRECCIÓN CLAVE
            .filter(count__gt=1)
        )

        total_eliminados = 0

        for item in duplicados:
            nombre = item[campo_nombre]
            self.stdout.write(f"🔎 Procesando '{nombre}' en {modelo.__name__}...")

            # Obtener registros con ese nombre, ordenados por PK (conservar el primero)
            registros = modelo.objects.filter(**{campo_nombre: nombre}).order_by(campo_pk)
            pk_a_conservar = registros.first()

            # Eliminar los demás (solo si no tienen desembolsos)
            for registro in registros[1:]:
                tiene_desembolsos = Desembolsos.objects.filter(
                    **{campo_fk: registro}
                ).exists()

                if not tiene_desembolsos:
                    registro.delete()
                    total_eliminados += 1
                    self.stdout.write(
                        self.style.WARNING(f"   ❌ Eliminado {campo_pk} {getattr(registro, campo_pk)} (sin desembolsos)")
                    )
                else:
                    self.stdout.write(
                        self.style.NOTICE(f"   ⚠️  Conservado {campo_pk} {getattr(registro, campo_pk)} (tiene desembolsos)")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ {modelo.__name__}: {total_eliminados} registros duplicados eliminados."
            )
        )