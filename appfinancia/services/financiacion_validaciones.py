# appfinancia/services/financiacion_validaciones.py

from appfinancia.models import Financiacion

def f_financiacion_ok(solicitud_id):
    """
    Valida si una solicitud de financiación puede ser aprobada.

    Retorna:
    - (True, {})  → si cumple todas las reglas
    - (False, {campo: mensaje}) → si NO cumple
    """

    errores = {}

    try:
        financiacion = Financiacion.objects.get(solicitud_id=solicitud_id)
    except Financiacion.DoesNotExist:
        return False, {
            "solicitud_id": "La solicitud de financiación no existe."
        }

    # =============================
    # ESTADO
    # =============================
    if financiacion.estado_solicitud != "RECIBIDO":
        errores["estado_solicitud"] = "Debe estar en estado RECIBIDO."

    # =============================
    # VALORES FINANCIEROS
    # =============================
    if not financiacion.valor_prestamo:
        errores["valor_prestamo"] = "Debe ingresar el valor del préstamo."

    if not financiacion.valor_cuota_inicial:
        errores["valor_cuota_inicial"] = "Debe ingresar el valor de la cuota inicial."

    if financiacion.seguro_vida == "SI" and not financiacion.valor_seguro_vida:
        errores["valor_seguro_vida"] = (
            "Debe ingresar el valor del seguro de vida cuando aplica."
        )

    if not financiacion.tasa:
        errores["tasa"] = "Debe ingresar la tasa de interés."

    if not financiacion.seguro_vida:
        errores["seguro_vida"] = "Debe indicar si aplica seguro de vida."

    # =============================
    # CLIENTE
    # =============================
    if financiacion.cliente_nuevo is None:
        errores["cliente_nuevo"] = "Debe indicar si el cliente es nuevo."

    if financiacion.cliente_vetado != "NO":
        errores["cliente_vetado"] = "El cliente se encuentra vetado."

    # =============================
    # DATOS DE LA PÓLIZA
    # =============================
    if not financiacion.placas:
        errores["placas"] = "Debe ingresar las placas del vehículo."

    if not financiacion.numero_poliza:
        errores["numero_poliza"] = "Debe ingresar el número de la póliza."

    # =============================
    # DOCUMENTACIÓN
    # =============================
    if financiacion.info_cliente_valida is not True:
        errores["info_cliente_valida"] = "La información del cliente no está validada."

    if financiacion.adjunta_documento_identificacion is not True:
        errores["adjunta_documento_identificacion"] = (
            "Debe adjuntar el documento de identificación."
        )

    if financiacion.adjunta_poliza_seguro is not True:
        errores["adjunta_poliza_seguro"] = "Debe adjuntar la póliza de seguro."

    if financiacion.adjunta_autorizacion_datos is not True:
        errores["adjunta_autorizacion_datos"] = (
            "Debe adjuntar la autorización de datos personales."
        )

    if financiacion.seguro_vida == "SI" and financiacion.adjunta_seguro_vida is not True:
        errores["adjunta_seguro_vida"] = (
            "Debe adjuntar el documento del seguro de vida."
        )

    # ===================================
    # VALIDAR EL VALOR DE LA CUOTA INICIAL
    # ====================================
    
    #valor_seguro_vida = Decimal(financiacion.valor_seguro_vida or 0)
    #tasa = Decimal(str(financiacion.tasa or 0)) / Decimal("100")
     
    #cuota_base = (valor_poliza * tasa) / (1 - (1 + tasa) ** (-plazo))
    #cuota_base = (valor_prestamo * tasa) / (1 - (1 + tasa) ** (-plazo))
    #cuota_base = cuota_base.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

      

    # =============================
    # RESULTADO FINAL
    # =============================
    if errores:
        return False, errores

    return True, {}

# ====================================== 
# Validar el formulario de Financiación:
# ======================================
   
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from appfinancia.utils import get_politicas
    

def f_validar_financiacion_form(obj):
    """
    Recibe 'obj' (la instancia de Financiacion).
    """
    #from .utils import get_politicas # Asegúrate de que la ruta sea correcta
    
    try:
        politicas = get_politicas()
    except Exception as e:
        raise ValidationError(f"Error al cargar políticas: {e}")

    errores = {}

    # ESTADO
    if obj.estado_solicitud != "RECIBIDO":
        errores["estado_solicitud"] = "Debe estar en estado RECIBIDO para modificar valores."

    # VALORES FINANCIEROS
    if not obj.valor_prestamo:
        errores["valor_prestamo"] = "Debe ingresar el valor del préstamo."
    elif obj.valor_prestamo <= 0:
        errores['valor_prestamo'] = "El valor del préstamo debe ser mayor a cero."
    elif not (politicas.valor_cred_min <= obj.valor_prestamo <= politicas.valor_cred_max):
        errores['valor_prestamo'] = f"El préstamo debe estar entre ${politicas.valor_cred_min:,.0f} y ${politicas.valor_cred_max:,.0f}."

    if not obj.valor_cuota_inicial:
        errores["valor_cuota_inicial"] = "Debe ingresar el valor de la cuota inicial."

    if obj.seguro_vida == "SI" and not obj.valor_seguro_vida:
        errores["valor_seguro_vida"] = "Debe ingresar el valor del seguro de vida cuando aplica."

    # CLIENTE Y VETO
    if obj.cliente_vetado != "NO":
        errores["cliente_vetado"] = "No se puede procesar: El cliente se encuentra vetado."

    # DOCUMENTACIÓN (Validación de Booleanos)
    if not obj.info_cliente_valida:
        errores["info_cliente_valida"] = "La información del cliente debe ser validada manualmente."

    # VALIDACIÓN DE CUOTA INICIAL (Cálculo Financiero)
    if obj.valor_prestamo and obj.tasa and obj.numero_cuotas:
        try:
            v_valor_prestamo = Decimal(obj.valor_prestamo)
            v_tasa = Decimal(obj.tasa) / Decimal("100")
            v_plazo = int(obj.numero_cuotas)
            
            if v_plazo > 0 and v_tasa > 0:
                v_cuota_base = (v_valor_prestamo * v_tasa) / (1 - (1 + v_tasa) ** (-v_plazo))
                v_cuota_base = v_cuota_base.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

                if Decimal(obj.valor_cuota_inicial or 0) < v_cuota_base:
                    errores['valor_cuota_inicial'] = f"La cuota inicial debe cubrir al menos la cuota base de ${v_cuota_base:,.0f}"
        except Exception:
            errores['tasa'] = "Error en el cálculo de la cuota. Verifique tasa y plazo."

    return errores # Retornamos el diccionario. Si está vacío, es que todo está OK.
