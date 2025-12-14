# appfinancia/management/commands/corregir_historia_prestamos.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from appfinancia.models import Historia_Prestamos, Prestamos

User = get_user_model()

class Command(BaseCommand):
    help = 'Corrige registros corruptos en Historia_Prestamos donde prestamo_id es un string en lugar de una instancia válida'

    def handle(self, *args, **options):
        # Obtener usuario admin
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(
                self.style.ERROR("❌ No se encontró un superusuario. Crea uno con 'createsuperuser'.")
            )
            return

        self.stdout.write("🔍 Buscando registros corruptos en Historia_Prestamos...")

        registros_corregidos = 0
        registros_error = 0
        total_registros = 0

        try:
            with transaction.atomic():
                # Iterar sobre todos los registros
                for h in Historia_Prestamos.objects.all():
                    total_registros += 1
                    
                    # Verificar si prestamo_id es un string (corrupto)
                    if isinstance(h.prestamo_id, str):
                        self.stdout.write(
                            self.style.WARNING(f"⚠️ Registro ID {h.id}: prestamo_id es string: '{h.prestamo_id}'")
                        )
                        
                        # Intentar extraer el ID numérico
                        try:
                            # Extraer el primer token (asumiendo formato "90008 - NOMBRE - ...")
                            prestamo_id_str = h.prestamo_id.split()[0]
                            prestamo_id_num = int(prestamo_id_str)
                            
                            # Buscar el préstamo correcto
                            prestamo_correcto = Prestamos.objects.get(prestamo_id=prestamo_id_num)
                            
                            # Corregir la relación
                            h.prestamo_id = prestamo_correcto
                            h.usuario = admin_user.username[:15]  # ajustar longitud si es necesario
                            h.save()
                            
                            registros_corregidos += 1
                            self.stdout.write(
                                self.style.SUCCESS(f"✅ Corregido: ID {h.id} → Préstamo {prestamo_id_num}")
                            )
                            
                        except (ValueError, IndexError, Prestamos.DoesNotExist) as e:
                            registros_error += 1
                            self.stdout.write(
                                self.style.ERROR(f"❌ Error al corregir ID {h.id}: {str(e)}")
                            )
                            # Opcional: marcar para revisión manual
                            # h.observaciones = f"ERROR_CORRECCION: {str(e)}"
                            # h.save()
                    
                    # Opcional: verificar registros que tienen prestamo_id como entero pero no existen
                    elif isinstance(h.prestamo_id, int):
                        try:
                            prestamo = Prestamos.objects.get(prestamo_id=h.prestamo_id)
                            # Ya está correcto, no hacer nada
                        except Prestamos.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f"⚠️ Registro ID {h.id}: préstamo {h.prestamo_id} no existe")
                            )
                    
                    # Si ya es una instancia válida, está correcto
                    # No necesitamos hacer nada

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error fatal durante la corrección: {e}"))
            return

        # Resumen final
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 RESUMEN DE CORRECCIÓN")
        self.stdout.write("="*50)
        self.stdout.write(f"Total registros analizados: {total_registros}")
        self.stdout.write(f"Registros corregidos: {registros_corregidos}")
        self.stdout.write(f"Registros con errores: {registros_error}")
        
        if registros_corregidos > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ ¡{registros_corregidos} registros corregidos exitosamente!"))
            self.stdout.write("🔄 Ahora puedes acceder al Admin de Préstamos sin errores.")
        else:
            self.stdout.write(self.style.WARNING("ℹ️ No se encontraron registros corruptos que necesiten corrección."))

        self.stdout.write("="*50)