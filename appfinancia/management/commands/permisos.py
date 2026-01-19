# appfinancia/management/commands/permisos.py
import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

class Command(BaseCommand):
    help = "Lista los permisos de 'appfinancia' y genera un archivo CSV con ellos."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Analizando permisos de la app 'appfinancia'...\n"))

        # Ruta del CSV de salida (en la raíz del proyecto)
        csv_path = os.path.join(settings.BASE_DIR, "permisos_appfinancia.csv")

        # Obtener content types solo de appfinancia
        content_types = ContentType.objects.filter(app_label='appfinancia')
        permisos = Permission.objects.filter(content_type__in=content_types).select_related('content_type').order_by(
            'content_type__model', 'codename'
        )

        if not permisos.exists():
            self.stdout.write(self.style.WARNING("⚠️ No se encontraron permisos en la app 'appfinancia'."))
            return

        permisos_predeterminados = []
        permisos_personalizados = []
        csv_rows = []

        # Clasificar permisos y preparar filas para el CSV
        for perm in permisos:
            codename = perm.codename
            model_name = perm.content_type.model
            app_label = perm.content_type.app_label

            # Determinar si es predeterminado
            is_predeterminado = any(
                codename.startswith(pref) and codename.endswith(f"_{model_name}")
                for pref in ['add', 'change', 'delete', 'view']
            )

            tipo = "Predeterminado" if is_predeterminado else "Personalizado"

            if is_predeterminado:
                permisos_predeterminados.append(perm)
            else:
                permisos_personalizados.append(perm)

            # Agregar fila al CSV
            csv_rows.append({
                "App": app_label,
                "Modelo": model_name,
                "Código del Permiso": codename,
                "Nombre del Permiso": perm.name,
                "Tipo": tipo
            })

        # === Mostrar en consola (como antes) ===
        if permisos_personalizados:
            self.stdout.write(self.style.MIGRATE_HEADING("✨ PERMISOS PERSONALIZADOS"))
            for perm in permisos_personalizados:
                self.stdout.write(f"  • {perm.codename} → {perm.name}")
            self.stdout.write("")

        if permisos_predeterminados:
            self.stdout.write(self.style.MIGRATE_HEADING("⚙️ PERMISOS PREDETERMINADOS (Django)"))
            current_model = None
            for perm in permisos_predeterminados:
                model_name = perm.content_type.model
                if model_name != current_model:
                    current_model = model_name
                    self.stdout.write(f"\n    📂 Modelo: {model_name}")
                self.stdout.write(f"        • {perm.codename} → {perm.name}")
            self.stdout.write("")

        total_personalizados = len(permisos_personalizados)
        total_predeterminados = len(permisos_predeterminados)
        total = total_personalizados + total_predeterminados

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Resumen:\n"
            f"   - Personalizados: {total_personalizados}\n"
            f"   - Predeterminados: {total_predeterminados}\n"
            f"   - Total en 'appfinancia': {total}\n"
        ))

        # === Generar CSV ===
        with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["App", "Modelo", "Código del Permiso", "Nombre del Permiso", "Tipo"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        self.stdout.write(self.style.SUCCESS(f"📤 Archivo CSV guardado en: {csv_path}\n"))