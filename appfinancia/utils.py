# utils.py
# archivo 'utils.py' (MANTENER solo esto al inicio) 
#incluido el 2025/11/29 par solucionar las referencias circulares. (pam)
from __future__ import annotations


from django.core.cache import cache
from django.db import transaction

CACHE_TIMEOUT = 3600  # 1 hora

#Obtener las Políticas de crédito
def get_politicas():
    from .models import Politicas
    """
    Retorna el objeto único de Politicas.
    Usa caché para evitar múltiples consultas a la BD.
    Lanza excepción si no está configurado.
    """
    CACHE_KEY = 'politicas_globales'
    politicas = cache.get(CACHE_KEY)
    
    if politicas is None:
        try:
            politicas = Politicas.objects.get()
            # Cachear por 1 hora (3600 segundos)
            cache.set(CACHE_KEY, politicas, timeout=3600)
        except Politicas.DoesNotExist:
            raise RuntimeError("❌ Las políticas globales no han sido configuradas. "
                             "Por favor, configúrelas en el panel de administración.")
    
    return politicas
    
#Obtener el numerador de préstamos    
#def get_next_prestamo_id():
#    from .models import Numeradores
#    """
#    Obtiene el siguiente ID para préstamo de forma atómica y segura.
#    """
#    with transaction.atomic():
#        # Bloquea la fila para evitar concurrencia
#        numerador = Numeradores.objects.select_for_update().first()
#        if numerador is None:
#            # Crea la fila si no existe (solo debería pasar una vez)
#            numerador = Numeradores.objects.create(numerador_prestamo=1000)
#        else:
#            numerador.numerador_prestamo += 1
#            numerador.save(update_fields=['numerador_prestamo'])
#        return numerador.numerador_prestamo
        

# utils.py
#from django.db import transaction
#from django.core.cache import cache
#from .models import Numeradores

#CACHE_TIMEOUT = 3600  # 1 hora

def _increment_field(field_name: str) -> int:
    from .models import Numeradores
    """
    Incrementa atómicamente un campo y devuelve el nuevo valor.
    """
    with transaction.atomic():
        # Bloquear la fila única
        numerador = Numeradores.objects.select_for_update().first()
        if numerador is None:
            numerador, _ = Numeradores.objects.get_or_create()

        # Obtener y actualizar
        current_value = getattr(numerador, field_name)
        new_value = current_value + 1
        setattr(numerador, field_name, new_value)
        numerador.save(update_fields=[field_name])

        # Opcional: actualizar caché
        cache_key = f"numerador_{field_name}"
        cache.set(cache_key, new_value, timeout=CACHE_TIMEOUT)

        return new_value

# === FUNCIONES PÚBLICAS (exactamente como solicitaste) ===

def get_next_asientos_id() -> int:
    """Obtiene el siguiente ID para asientos contables."""
    return _increment_field('numerador_asientos')

def get_next_transaccion_id() -> int:
    """Obtiene el siguiente ID para transacciones."""
    return _increment_field('numerador_transaccion')

def get_next_prestamo_id() -> int:
    """Obtiene el siguiente ID para préstamos."""
    return _increment_field('numerador_prestamo')

def get_next_conciliacion_id() -> int:
    """Obtiene el siguiente ID para conciliaciones."""
    return _increment_field('numerador_conciliacion')

def get_next_pagos_id() -> int:
    """Obtiene el siguiente ID para pagos."""
    return _increment_field('numerador_pagos')

def get_next_secuencial_1_id() -> int:
    """Obtiene el siguiente ID del contador auxiliar 1."""
    return _increment_field('numerador_aux_1')

def get_next_secuencial_2_id() -> int:
    """Obtiene el siguiente ID del contador auxiliar 2."""
    return _increment_field('numerador_aux_2')

def get_next_secuencial_3_id() -> int:
    """Obtiene el siguiente ID del contador auxiliar 3."""
    return _increment_field('numerador_aux_3')

def get_next_secuencial_4_id() -> int:
    """Obtiene el siguiente ID del contador auxiliar 4."""
    return _increment_field('numerador_aux_4')

def get_next_secuencial_5_id() -> int:
    """Obtiene el siguiente ID del contador auxiliar 5."""
    return _increment_field('numerador_aux_5')

#===========================   DESEMBOLSO BACKEND ==================================
# appfinancia/utils.py
from decimal import Decimal, getcontext, ROUND_HALF_UP
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

# Ajuste de precisión decimal para cálculos financieros
getcontext().prec = 28
ROUND = ROUND_HALF_UP



def obtener_user_name_from_django_user(user_obj):
    """
    Recibe request.user y retorna su username o str(user_obj) si no tiene atributo.
    """
    try:
        return user_obj.username
    except Exception:
        return str(user_obj)



#---------------------- desembolso func
from datetime import date


def create_prestamo(desembolso):
    
    from .models import Prestamos
    """
    Creates a Prestamo record based on a Desembolso instance.
    Uses default values for optional fields if not provided.
    """
    print(f"DEBUG: create_prestamo recibió desembolso = {desembolso}, tipo = {type(desembolso)}")
    if desembolso is None or not hasattr(desembolso, 'pk'):
        raise ValueError(f"Desembolso inválido: {desembolso}")
    
    prestamo = Prestamos.objects.create(
        prestamo_id=desembolso,
        cliente_id=desembolso.cliente_id,
        asesor_id=desembolso.asesor_id,
        aseguradora_id=desembolso.aseguradora_id,
        vendedor_id=desembolso.vendedor_id,
        tipo_tasa=desembolso.tipo_tasa,
        tasa=desembolso.tasa,
        valor=desembolso.valor,
        valor_cuota_1=desembolso.valor_cuota_1,
        valor_cuota_mensual=desembolso.valor_cuota_mensual,
        valor_seguro_mes=desembolso.valor_seguro_mes,
        tiene_fee=desembolso.tiene_fee,
        dia_cobro=desembolso.dia_cobro,
        plazo_en_meses=desembolso.plazo_en_meses,
        fecha_desembolso=desembolso.fecha_desembolso,
        fecha_vencimiento=desembolso.fecha_vencimiento,
        suspender_causacion='NO',
        revocatoria='NO',
    )
    return prestamo



def create_movimiento(desembolso):
    from .models import Desembolsos, Movimientos 
    """
    Creates a Movimiento record based on a Desembolso instance.
    """
    movimiento = Movimientos.objects.create(
        cliente_id=desembolso.cliente_id,
        asesor_id=desembolso.asesor_id,
        valor_movimiento=desembolso.valor,
        fecha_valor_mvto=desembolso.fecha_desembolso,
    )
    return movimiento
#----------------------------------------
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta



def create_loan_payments(prestamo, desembolso, plan_pagos, user_name):
    """
    Guarda el plan de pagos generado por calculate_loan_schedule
    como registros en Historia_Prestamos, usando los conceptos adecuados.
    """
    from .models import Conceptos_Transacciones, Historia_Prestamos  # ✅ Corregido

    concepto_capital = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
    concepto_interes = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
    concepto_seguro = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
    concepto_gastos = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
    #concepto_capital = "PLANCAP"
    #concepto_interes = "PLANINT"
    #concepto_seguro =  "PLANSEG"
    #concepto_gastos =  "PLANGTO"

    created_count = 0

    for cuota in plan_pagos:
        numero_cuota = cuota['numero_cuota']
        fecha_vencimiento = cuota['fecha_vencimiento']

        # Crear registro para capital
        if cuota['capital'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo,
                fecha_efectiva=prestamo.fecha_desembolso,
                fecha_proceso=timezone.now().date(),
                ordinal_interno=0,
                numero_operacion=created_count,
                concepto_id=concepto_capital,
                monto_transaccion=float(cuota['capital']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
                usuario=user_name,
            )
            created_count += 1

        # Crear registro para intereses
        if cuota['intereses'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo,
                fecha_efectiva=prestamo.fecha_desembolso,
                fecha_proceso=timezone.now().date(),
                ordinal_interno=0,
                numero_operacion=created_count,
                concepto_id=concepto_interes,
                monto_transaccion=float(cuota['intereses']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
                usuario=user_name,
            )
            created_count += 1

        # Crear registro para seguro
        if cuota['seguro'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo,
                fecha_efectiva=prestamo.fecha_desembolso,
                fecha_proceso=timezone.now().date(), 
                ordinal_interno=0,
                numero_operacion=created_count,
                concepto_id=concepto_seguro,
                monto_transaccion=float(cuota['seguro']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
                usuario=user_name,
            )
            created_count += 1

        # Crear registro para gastos
        if cuota['gastos'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo,
                fecha_efectiva=prestamo.fecha_desembolso,
                fecha_proceso=timezone.now().date(), 
                ordinal_interno=0,
                numero_operacion=created_count,
                concepto_id=concepto_gastos,
                monto_transaccion=float(cuota['gastos']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
                usuario=user_name,
            )
            created_count += 1

    return created_count
	

from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta
from datetime import date

#----------------------------------------
def calculate_loan_schedule(desembolso):
    """
    Calculates the loan payment schedule based on the Desembolso object.
    Returns a list of dictionaries with:
    - numero_cuota
    - capital
    - intereses
    - fecha_vencimiento
    - seguro
    - gastos
    - otros campos...
    """
    from .models import Desembolsos  # Importar solo si es necesario

    results = []
    valor = Decimal(desembolso.valor or 0)
    valor_cuota_1 = Decimal(desembolso.valor_cuota_1 or 0)
    monto = (valor - valor_cuota_1).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    plazo_total = int(desembolso.plazo_en_meses or 0)

    # tasa anual en porcentaje -> convertir a decimal mensual con 30/360
    tasa_pct = Decimal(desembolso.tasa or 0)
    tasa_mensual = (tasa_pct / Decimal('100')) * (Decimal('30') / Decimal('360'))

    # Cuota 1
    if plazo_total >= 1:
        results.append({
            'numero_cuota': 1,
            'capital': valor_cuota_1.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'intereses': Decimal('0.00'),
            'fecha_vencimiento': desembolso.fecha_desembolso,
            'seguro': Decimal(desembolso.valor_seguro_mes or 0),
            'gastos': Decimal('0.00'),
            'saldo_capital': Decimal('0.00'),
            'saldo_intereses': Decimal('0.00'),
            'saldo_seguro': Decimal('0.00'),
            'saldo_gastos': Decimal('0.00'),
        })

    # Cuotas restantes
    cuotas_restantes = max(plazo_total - 1, 0)
    if cuotas_restantes == 0 or monto == Decimal('0.00'):
        return results

    # Si hay cuotas restantes, calculamos pago nivelado (anualidad) sobre 'monto' con 'cuotas_restantes' periodos
    r = tasa_mensual  # decimal
    n = cuotas_restantes

    # Si r == 0 -> pago = monto / n
    if r == 0:
        pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        # pago = monto * r / (1 - (1+r) ** -n)
        one_plus_r = (Decimal('1') + r)
        denom = (Decimal('1') - (one_plus_r ** (Decimal(-n))))
        if denom == 0:
            pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            pago_mensual = (monto * r / denom).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    saldo = monto
    fecha_base = desembolso.fecha_desembolso

    for i in range(1, cuotas_restantes + 1):
        # número de cuota global será (i+1) porque la 1 ya fue guardada
        numero = i + 1
        if r == 0:
            intereses = Decimal('0.00')
            capital = pago_mensual
        else:
            intereses = (saldo * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            capital = (pago_mensual - intereses).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Si es la última cuota, ajustar capital para evitar residuos por redondeo
        if i == cuotas_restantes:
            capital = saldo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            intereses = (pago_mensual - capital).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if intereses < 0:
                intereses = Decimal('0.00')

        # Calcular fecha de vencimiento
        try:
            fecha_venc = fecha_base + relativedelta(months=i)
            target_day = int(desembolso.dia_cobro)
            fecha_venc = fecha_venc.replace(day=min(target_day, 28)) if target_day > 28 else fecha_venc.replace(day=target_day)
        except Exception:
            # Fallback: add months only
            fecha_venc = fecha_base + relativedelta(months=i)

        results.append({
            'numero_cuota': numero,
            'capital': capital,
            'intereses': intereses,
            'fecha_vencimiento': fecha_venc,
            'seguro': Decimal(desembolso.valor_seguro_mes or 0),
            'gastos': Decimal('0.00'),
            'saldo_capital': Decimal('0.00'),
            'saldo_intereses': Decimal('0.00'),
            'saldo_seguro': Decimal('0.00'),
            'saldo_gastos': Decimal('0.00'),
        })
        saldo = (saldo - capital).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if saldo < 0:
            saldo = Decimal('0.00')

    return results
    

#----------------------------------------------------------------2025/11/26
class FechasSistemaHelper:  
    """
    Helper para acceder de forma segura y eficiente a la configuración global de fechas del sistema.
    Basado en el patrón Singleton (`Fechas_Sistema.load()`).
    """
    
    @staticmethod
    def get_fecha_proceso_actual():
        from .models import Fechas_Sistema
        return Fechas_Sistema.load().fecha_proceso_actual

    @staticmethod
    def get_fecha_proceso_anterior():
        from .models import Fechas_Sistema
        return Fechas_Sistema.load().fecha_proceso_anterior

    @staticmethod
    def get_fecha_proximo_proceso():
        from .models import Fechas_Sistema
        return Fechas_Sistema.load().fecha_proximo_proceso

    @staticmethod
    def get_estado_sistema():
        from .models import Fechas_Sistema
        return Fechas_Sistema.load().estado_sistema

    @staticmethod
    def get_modo_fecha_sistema():
        from .models import Fechas_Sistema
        return Fechas_Sistema.load().modo_fecha_sistema

    @staticmethod
    def sistema_esta_abierto():
        from .models import Fechas_Sistema
        return FechasSistemaHelper.get_estado_sistema() == 'ABIERTO'

    @staticmethod
    def fecha_proceso_es_hoy():
        from .models import Fechas_Sistema
        return FechasSistemaHelper.get_fecha_proceso_actual() == timezone.now().date()

    #Acceso grupal (para evitar múltiples llamadas a `load()`)
    @staticmethod
    def get_all():
        """
        Devuelve un dict con todos los valores actuales.
        Útil para optimizar cuando se necesitan varios campos.
        """
        
        from .models import Fechas_Sistema
        fs = Fechas_Sistema.load()
        return {
            'fecha_proceso_actual': fs.fecha_proceso_actual,
            'fecha_proceso_anterior': fs.fecha_proceso_anterior,
            'fecha_proximo_proceso': fs.fecha_proximo_proceso,
            'estado_sistema': fs.estado_sistema,
            'modo_fecha_sistema': fs.modo_fecha_sistema,
        }

#Fin Fechas del Sistema


#=========================================================================================
# InBox Pagos
#=========================================================================================
import io
import re
import pdfplumber
from django.utils import timezone
from typing import Literal
import os   # ← IMPORTANTE: evita el NameError

def InBox_Pagos(archivo_pagos, usuario, cabezal):
    #identificar automáticamente el formato del archvo
    formato=f_identificar_formato(cabezal.nombre_archivo_id)
    
    if formato == "1-FORMATO PSE":
        return inbox_formato_pse(
            xls_file=archivo_pagos,
            nombre_archivo_id=cabezal.nombre_archivo_id,
            user=usuario,
            cabezal=cabezal
        )
        return ok, msg

    elif formato == "2-FORMATO ESTANDAR":
        return False, "El Formato Estándar aún no está implementado."

    elif formato == "3-FORMATO EXTRACTO BANCOLOMBIA":
        return inbox_formato_bancolombia(
            pdf_file=archivo_pagos,
            nombre_archivo_id=cabezal.nombre_archivo_id,
            user=usuario,
            cabezal=cabezal
        )

    else:
        return False, "Formato desconocido."


#=========================================================================================
#leer extracto de Bancolombia
#=========================================================================================
def inbox_formato_bancolombia(pdf_file, nombre_archivo_id, user, cabezal):
    from .models import InBox_PagosDetalle
    cargados = 0
    valor_total = 0
    rechazados = 0

    try:
        pdf_bytes = io.BytesIO(pdf_file.read())
        texto = ""

        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto += t + "\n"

        lineas = texto.split("\n")

    except Exception as e:
        return False, f"Error leyendo PDF: {e}"

    for linea in lineas:
        reg = linea.strip()
        if len(reg) < 6:
            continue

        # MOVIMIENTOS (fecha YYYY/MM/DD)
        if reg[:4].isdigit() and reg[4] == "/":
            try:
                fecha_raw=safe(reg[0:10], 10)
                descripcion_raw=safe(clean_descripcion(reg),100)
                valor_raw = clean_money(reg)
                clase_movimiento_raw=clase_movimiento(descripcion_raw,Decimal(valor_raw)) 
                
                InBox_PagosDetalle.objects.create(
                    nombre_archivo_id_id=nombre_archivo_id,
                    banco_origen='BANCOLOMBIA',            
                    cuenta_bancaria = "03200001692",
                    tipo_cuenta_bancaria="AHORROS",
                    canal_red_pago="EXTRACTOBANCOLOMBIA",
                    #ref_bancaria=None,
                    #ref_red=None,
                    #ref_cliente_1=v_ref_1[0:11],
                    #ref_cliente_2=v_ref_2[0:11],
                    #ref_cliente_3=safe(v_descripcion, 100),
                    ref_cliente_3=descripcion_raw,
                    #estado_transaccion_reportado=None,
                    #cliente_id_reportado=None,
                    fecha_pago=datetime.strptime(fecha_raw, "%Y/%m/%d").date(),
                    estado_pago=f_estado_pago(clase_movimiento_raw),
                    #cliente_id_real=None, 
                    #prestamo_id_real=None,
                    #poliza_id_real=None,
                    estado_conciliacion=f_estado_conciliacion(clase_movimiento_raw),
                    clase_movimiento=clase_movimiento_raw, 
                    estado_fragmentacion="NO_REQUIERE",
                    valor_pago=Decimal(valor_raw),
                    creado_por=user,
                )

                cargados += 1
                valor_total += float(valor_raw)

            except Exception:
                rechazados += 1
                continue

    # ACTUALIZAR CABEZAL (fuera del for)
    cabezal.formato=f_identificar_formato(nombre_archivo_id)
    cabezal.valor_total = valor_total
    cabezal.registros_cargados = cargados
    cabezal.registros_rechazados = rechazados
    cabezal.estado_proceso_archivo = "RECIBIDO"
    cabezal.save()

    return True, f"{cargados} registros cargados, {rechazados} rechazados."



# ===========================================================
#  FORMATO 1: PSE
# ===========================================================
def inbox_formato_pse(xls_file, nombre_archivo_id, user, cabezal):
    import pandas as pd
    from decimal import Decimal
    from django.db import transaction
    from .models import InBox_PagosDetalle

    # -------------------------------------------------------
    # Cargar archivo Excel
    # -------------------------------------------------------
    try:
        df = pd.read_excel(xls_file, sheet_name="Facturas")
    except Exception as e:
        return False, f"Error leyendo archivo PSE: {e}"

    # -------------------------------------------------------
    # Validar columnas obligatorias
    # -------------------------------------------------------
    columnas = [
        "Modalidad de Pago",
        "Estado",
        "Valor Factura",
        "Valor pago",
        "CUS",
        "Fecha Pago",
        "Estado Transacción/Operación",
        "Nombre",
        "Referencia Externa",
        "Ramo",
        "Cédula"
    ]

    
    for c in columnas:
        if c not in df.columns:
            return False, f"Columna faltante en archivo PSE: {c}"

    # -------------------------------------------------------
    # Variables de control
    # -------------------------------------------------------
    cargados = 0
    rechazados = 0
    valor_total = Decimal("0.00")

    # -------------------------------------------------------
    # Transacción atómica
    # -------------------------------------------------------
    with transaction.atomic():
        for idx, row in df.iterrows():
            try:
                # -------------------------------------------------------
                # Fecha y hora
                # -------------------------------------------------------
                fecha_hora_str = str(row["Fecha Pago"])  # ej: "2025-01-05 13:24:59"
                fecha_pago = fecha_hora_str[:10]

                try:
                    hora_pago = pd.to_datetime(fecha_hora_str).time()
                except:
                    hora_pago = None

                # -------------------------------------------------------
                # Crear registro detalle pagos PSE
                # -------------------------------------------------------
                p = InBox_PagosDetalle(                  
                    nombre_archivo_id_id=nombre_archivo_id,
                    banco_origen="BANCOLOMBIA",            
                    cuenta_bancaria = "03200001692",
                    tipo_cuenta_bancaria="AHORROS",
                    canal_red_pago="PSE",
                    ref_bancaria=row["CUS"],
                    ref_red="",
                    ref_cliente_1=row["Nombre"],
                    ref_cliente_2=row["Referencia Externa"],
                    ref_cliente_3=row["Ramo"],
                    estado_transaccion_reportado=row["Estado"],
                    cliente_id_reportado=row["Cédula"],
                    estado_pago="RECIBIDO",
                    clase_movimiento="PAGO_PSE",   #pago pse 
                    estado_fragmentacion="NO_REQUIERE",
                    estado_conciliacion='NO',
                    valor_pago=Decimal(str(row["Valor pago"])),
                    fecha_pago=fecha_pago,
                    creado_por=user,
                    
                )

                p.save()

                cargados += 1
                valor_total += Decimal(str(row["Valor pago"]))

            except Exception:
                rechazados += 1
                continue

        # -------------------------------------------------------
        # Actualizar totales en el cabezal
        # -------------------------------------------------------
        cabezal.formato=f_identificar_formato(nombre_archivo_id)
        cabezal.valor_total = valor_total
        cabezal.registros_cargados = cargados
        cabezal.registros_rechazados = rechazados
        cabezal.estado_proceso_archivo = "RECIBIDO"
        cabezal.save()

    return True, f"Archivo procesado: {cargados} registros cargados, {rechazados} rechazados."

#-----------------------------

def safe(txt, maxlen):
    """Evita errores de overflow truncando cadenas."""
    if txt is None:
        return ""
    # Aseguramos que la entrada sea string antes de truncar y limpiar
    return str(txt).strip()[:maxlen]

#================
#Limpiar el valor
#================

def clean_money(valor_str):
    if not valor_str:
        return None        
    #limpio = str(valor_str).replace('$', '').replace(',', '').strip()
    limpio=valor_str[valor_str.rfind(" "):].replace(" ", "").replace(",", "")
    
    try:
        valor_numerico = float(limpio)
        
        return valor_numerico       
    except ValueError as e:
        # Maneja la excepción si la cadena limpia todavía no es un número válido.
        # print(f"Error de conversión en clean_money: {e} para cadena limpia '{limpio}'")
        return None


#================
#Limpiar descripción
#================
def clean_descripcion(reg: str) -> str:
    """
    Extrae la subcadena desde el inicio (pos 0) hasta justo antes 
    del primer número (0-9) o el signo de resta (-).
    """
    reg=reg[11:70]
    
    # 1. Definir el patrón de búsqueda: [0-9-] busca cualquier dígito o un guion.
    #patron = r'[0-9-]'
    patron = r'\d{2}|-'

    # 2. Buscar la primera coincidencia en la cadena 'reg'.
    match = re.search(patron, reg)

    if match:
        # Si hay una coincidencia, match.start() devuelve el índice de ese primer carácter.
        indice_fin = match.start()
        
        # 3. Recortar la subcadena desde el inicio hasta ese índice.
        # Se usa .rstrip() para quitar cualquier espacio sobrante al final de la descripción.
        return reg[:indice_fin].rstrip()
    else:
        # Si no se encuentra ningún número o signo, se devuelve la cadena completa.
        return reg.rstrip()

#================
#Excluir registros
#================
#from typing import Literal
def f_estado_pago(tipo_mov: str) -> Literal['EXCLUIDO', 'RECIBIDO']:
    if tipo_mov and tipo_mov.upper() == 'EXCLUIDO':
        return 'EXCLUIDO'
    else:
        return 'RECIBIDO'

#===================
#Estado conciliación
#===================
        
from typing import Literal, Union

def f_estado_conciliacion(p_clas_mov: str) -> Union[str, Literal['NO', 'SI']]:
    clasificacion = p_clas_mov.upper() if p_clas_mov else ""
    if clasificacion == 'ABONO_PSE' or clasificacion == 'PAGO_PSE':
        return 'NO'
    elif clasificacion == 'PAGO_BANCOL':
        return 'SI'
    # 3. Caso por defecto
    else:
        return ""

# ============================================================
# PROCESOS DE ESTADO
# ============================================================

from django.db import transaction

#===============
# ANULAR ARCHIVO
# ==============
def f_anular_archivo(cabezal: InBox_PagosCabezal, usuario):
    from .models import InBox_PagosCabezal, InBox_PagosDetalle
    try:
        with transaction.atomic():

            # 1. Validar que el cabezal esté en estado que permita anulación
            if cabezal.estado_proceso_archivo != "RECIBIDO":
                return False, "Solo se pueden ANULAR archivos en estado RECIBIDO."

            # 2. Actualizar CABEZAL
            cabezal.estado_proceso_archivo = "ANULADO"
            cabezal.save()

            # 3. Actualizar DETALLE pero **solo los que estén RECIBIDO**
            registros_actualizados = InBox_PagosDetalle.objects.filter(
                nombre_archivo_id=cabezal.nombre_archivo_id,
                estado_pago="RECIBIDO"          # ← condición solicitada
            ).update(
                estado_pago="ANULADO"
            )

        return True, (
            f"Archivo {cabezal.nombre_archivo_id} anulado correctamente. "
            f"({registros_actualizados} registros cambiados a ANULADO)"
        )

    except Exception as e:
        return False, f"Error al anular archivo: {str(e)}"


# ================
# PROCESAR ARCHIVO
# ================
def f_procesar_archivo(cabezal: InBox_PagosCabezal, usuario):
    from .models import InBox_PagosCabezal, InBox_PagosDetalle
    try:
        with transaction.atomic():

            # 1. Validar que el cabezal esté en estado que permita anulación
            if cabezal.estado_proceso_archivo != "RECIBIDO":
                return False, "Solo se pueden PROCESAR archivos en estado RECIBIDO."

            # 2. Actualizar CABEZAL
            cabezal.estado_proceso_archivo = "A_PROCESAR"
            cabezal.save()

            # 3. Actualizar DETALLE pero **solo los que estén RECIBIDO**
            registros_actualizados = InBox_PagosDetalle.objects.filter(
                nombre_archivo_id=cabezal.nombre_archivo_id,
                estado_pago="RECIBIDO"          # ← condición solicitada
            ).update(
                estado_pago="A_PROCESAR"
            )

        return True, (
            f"Archivo {cabezal.nombre_archivo_id} enviados a PROCESAR correctamente. "
            f"({registros_actualizados} registros enviados a PROCESAR)"
        )

    except Exception as e:
        return False, f"Error al envio a proceso archivo: {str(e)}"

#===============================
#Identificar formato del archivo
#===============================
def f_identificar_formato(nombre_archivo: str) -> Literal['1-FORMATO PSE', '3-FORMATO EXTRACTO BANCOLOMBIA', 'Error: Formato no soportado']:
    _, extension = os.path.splitext(nombre_archivo)
    
    # Normalizar la extensión a minúsculas para una comparación robusta
    extension = extension.lower()

    # 2. Lógica de clasificación
    if extension == ".xlsx":
        return '1-FORMATO PSE'

    elif extension == ".pdf":
        return '3-FORMATO EXTRACTO BANCOLOMBIA'

    # 3. Caso por defecto (error)
    else:
        return f'Error: La extensión "{extension}" no es válida. Tipos soportados: .xlsx, .pdf'


# ============================================================
# Obtener la clase de movimiento. aplica para el Extracto Bancolombia
# ============================================================
from decimal import Decimal
from typing import Optional # Para clarificar que el valor puede ser un Decimal o None

def clase_movimiento(reg: str, valor: Optional[Decimal]) -> str:
    
    # 1.Si el valor no existe (es None) o es negativo.
    if valor is None or valor < 0:
        return "EXCLUIDO"
        # Se sale de la función inmediatamente (Early exit)
    
    # a) PAGO VIRTUAL PSE
    if "PAGO VIRTUAL PSE" in reg:
        return "ABONO_PSE"

    # b) ABONO INTERESES AHORROS
    elif "ABONO INTERESES AHORROS" in reg:
        return "EXCLUIDO"
        # Se sale de la función inmediatamente

    # c) IMPTO GOBIERNO 4X1000
    elif "IMPTO GOBIERNO 4X1000" in reg:
        return "EXCLUIDO"
        # Se sale de la función inmediatamente
    
    # Si pasa todas las comprobaciones anteriores, se asigna la clasificación por defecto.
    return "PAGO_BANCOL"
    


#Fin cargar archivos InBox----------------------------------------------------------------