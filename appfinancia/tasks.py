#TAREA DIARIA MASIVA

# tasks.py o script diario
from datetime import date, timedelta
from .models import Prestamos
from .utils import cerrar_periodo_interes

def calcular_intereses_diarios_masivo():
    """
    Tarea diaria: cierra el período de interés de todos los préstamos activos hasta ayer.
    """
    hoy = date.today()
    ayer = hoy - timedelta(days=1)

    # Obtener préstamos activos (ajusta el filtro según tu modelo)
    prestamos_activos = Prestamos.objects.filter(
        estado__in=['ACTIVO', 'VIGENTE']
    ).values_list('prestamo_id', flat=True)

    for prestamo_id in prestamos_activos:
        try:
            cerrar_periodo_interes(prestamo_id, ayer)
        except Exception as e:
            # Loguear error, pero no detener todo
            print(f"Error en préstamo {prestamo_id}: {e}")

# Ejecutar diariamente con cron (ejemplo en Linux):
# 0 1 * * * /ruta/a/tu/entorno/bin/python /ruta/a/corefinancia/manage.py shell -c "from appfinancia.tasks import calcular_intereses_diarios_masivo; calcular_intereses_diarios_masivo()"
