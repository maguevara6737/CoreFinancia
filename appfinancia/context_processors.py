from .models import Fechas_Sistema

def fecha_sistema(request):
    try:
        fecha = Fechas_Sistema.load()
    except Exception:
        fecha = None

    return {
        'FECHA_PROCESO_ACTUAL': fecha.fecha_proceso_actual if fecha else None,
        'ESTADO_SISTEMA': fecha.estado_sistema if fecha else None,
    }
