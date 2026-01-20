from django.db import transaction
from django.utils import timezone

from appfinancia.models import Financiacion
from appfinancia.services.financiacion_validaciones import f_financiacion_ok
from appfinancia.services.financiacion_correo_aprobacion import f_correo_aprobacion
from appfinancia.services.financiacion_pdf import f_generar_pdf_plan_pagos

def f_aprobar_financiacion(solicitud_id, usuario=None):
    """   
    Aprueba una financiación de forma atómica:
    - Valida reglas de negocio
    - Genera plan de pagos + PDF
    - Cambia estado
    - Envía correo de aprobación
    """

    try:
        financiacion = Financiacion.objects.get(solicitud_id=solicitud_id)
    except Financiacion.DoesNotExist:
        raise Exception("La financiación no existe.")

    # =============================
    # VALIDACIONES
    # =============================
    ok, errores = f_financiacion_ok(solicitud_id)

    if not ok:
        if isinstance(errores, dict):
            mensajes = "\n".join(
                [f"- {campo}: {mensaje}" for campo, mensaje in errores.items()]
            )
        else:
            mensajes = str(errores)

        raise Exception(
            f"No se puede aprobar la financiación por los siguientes errores:\n{mensajes}"
        )

    # =============================
    # EJECUCIÓN ATÓMICA
    # =============================
    with transaction.atomic():

        # 1 Generar Plan de Pagos + PDF
        #f_plan_pagos_cuota_fija(solicitud_id)
        
        #2 Imprimir el Plan de Pagos en pdf
        f_generar_pdf_plan_pagos(solicitud_id)

        #3 Cambiar estado
        financiacion.estado_solicitud = "APROBADO"
        financiacion.fecha_aprobacion = timezone.now()

        if usuario:
            financiacion.aprobado_por = usuario

        financiacion.save()

        # 4 Enviar correo
        f_correo_aprobacion(solicitud_id)
        
        try:
            f_correo_aprobacion(solicitud_id)
        except Exception as e:
            print(f"⚠️ Error enviando correo: {e}")

    return True


#from django.db import transaction
#from django.utils import timezone

def f_reenvio_correo_financiacion(solicitud_id, usuario=None):
    """
    Reenvía el correo de una financiación ya aprobada.
    """
    try:
        financiacion = Financiacion.objects.get(solicitud_id=solicitud_id)
    except Financiacion.DoesNotExist:
        raise Exception("La financiación no existe.")

    # 1. VALIDACIÓN DE ESTADO
    if financiacion.estado_solicitud != "APROBADO":
        # Lanzamos una excepción para que el Admin o la Vista la capture y muestre el mensaje
        raise Exception("Para reenviar un correo de aprobación, la financiación debe tener estado APROBADO.")

    # =============================
    # EJECUCIÓN ATÓMICA
    # =============================
    try:
        with transaction.atomic():
            # Nota: Si solo vas a reenviar correo, los pasos 1, 2 y 3 
            # normalmente ya se hicieron en la aprobación original.
            # Pero si quieres asegurar que el PDF esté actualizado, descomenta:
            
            # 1. Regenerar Plan de Pagos
            # f_plan_pagos_cuota_fija(solicitud_id)
            
            # 2. Regenerar PDF
            # f_generar_pdf_plan_pagos(solicitud_id)

            # 3. Actualizar quién reenvió (Opcional)
            # financiacion.save()

            # 4. Enviar correo de aprobación
            f_correo_aprobacion(solicitud_id)

        return True

    except Exception as e:
        # Si algo falla en el proceso atómico, lanzamos el error
        raise Exception(f"Error en el reenvío: {str(e)}")
    