import os
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea un backup de la base de datos PostgreSQL"

    def handle(self, *args, **options):
        db_settings = settings.DATABASES.get('default')
        if not db_settings:
            raise CommandError("No se encontró la configuración de la base de datos 'default'.")

        if db_settings['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError("Este comando solo soporta PostgreSQL.")

        # Extraer credenciales
        host = db_settings.get('HOST') or 'localhost'
        port = db_settings.get('PORT') or '5432'
        name = db_settings['NAME']
        user = db_settings['USER']
        password = db_settings.get('PASSWORD')

        # Carpeta de backups
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(exist_ok=True)

        # Nombre del archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{name}_{timestamp}.sql"
        filepath = backup_dir / filename

        # Comando pg_dump
        cmd = [
            "pg_dump",
            "--host", host,
            "--port", str(port),
            "--username", user,
            "--dbname", name,
            "--no-password",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "--file", str(filepath)
        ]

        # Establecer PGPASSWORD en el entorno si está definido
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        try:
            self.stdout.write(f"Iniciando backup de '{name}' en {filepath}...")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                raise CommandError(f"Error al ejecutar pg_dump:\n{result.stderr}")

            self.stdout.write(
                self.style.SUCCESS(f"✅ Backup completado: {filepath}")
            )

        except FileNotFoundError:
            raise CommandError("El comando 'pg_dump' no está instalado o no está en el PATH.")
        except Exception as e:
            raise CommandError(f"Error inesperado: {e}")