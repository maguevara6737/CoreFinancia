from django.core.management.base import BaseCommand
from appfinancia.services.financiacion_imap import procesar_emails


class Command(BaseCommand):
    help = "Lee correos de financiación desde Gmail y los guarda en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("📨 INICIANDO LECTURA DE CORREOS DE FINANCIACIÓN")
        self.stdout.write("=" * 60)

        try:
            procesar_emails()
            self.stdout.write(self.style.SUCCESS("✅ Proceso finalizado correctamente"))
        except Exception as e:
            self.stdout.write(self.style.ERROR("❌ Error ejecutando el proceso"))
            self.stdout.write(str(e))
