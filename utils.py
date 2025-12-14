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

#----------------------------------------------------------------2025/11/26
import pandas as pd
from django.utils import timezone
from django.db import transaction




#from .models import Pagos_Archivos, Pagos


# ===========================================================
# FUNCIÓN PRINCIPAL — Decide qué formato procesar
# ===========================================================
def cargar_archivo_pagos(pagos_archivo: 'Pagos_Archivos', archivo_subido, user):
    from .models import Pagos_Archivos
    formato = pagos_archivo.formato

    if formato == "1-FORMATO PSE":
        return procesar_formato_pse(pagos_archivo, archivo_subido, user)

    elif formato == "2-FORMATO ESTANDAR":
        return False, "El Formato Estándar aún no está implementado."

    elif formato == "3-FORMATO EXTRACTO BANCOLOMBIA":
        return False, "El Extracto Bancolombia aún no está implementado."

    return False, "Formato desconocido."


# ===========================================================
#  FORMATO 1: PSE
# ===========================================================
def procesar_formato_pse(pagos_archivo: 'Pagos_Archivos', archivo_subido, user):
    from .models import Pagos_Archivos, Pagos
    """
    Procesa un archivo PSE según la TABLA 1, TABLA 2 y TABLA 3.
    """

    try:
        df = pd.read_excel(archivo_subido, sheet_name="Facturas")
    except Exception as e:
        return False, f"Error leyendo archivo PSE: {e}"

    # -------------------------------------------------------
    # Validar que existan las columnas obligatorias
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
    valor_total = 0

    nombre_archivo = archivo_subido.name

    # Registrar nombre del archivo
    pagos_archivo.nombre_archivo_id = nombre_archivo
    
    print( "entro a hacer lectura del archivo: ", pagos_archivo.nombre_archivo_id)
    
    # Transacción atómica
    with transaction.atomic():

        for idx, row in df.iterrows():
            try:
                fecha_hora = str(row["Fecha Pago"])
                fecha_pago = fecha_hora[:10]
                hora_pago_str = fecha_hora[11:19]

                hora_pago = pd.to_datetime(hora_pago_str).time()
                
                print( "imprimo nombre cliente: ", row["Nombre"])
                print( "nombre archivo_pk : ", pagos_archivo.nombre_archivo_id)
                
                p = Pagos(
                    # Relación con archivo
                    nombre_archivo_id_id=pagos_archivo.nombre_archivo_id,
                    banco_origen='banco_origene-manual',            #pagos_archivo.banco_origen,
                    creado_por=user,

                    canal_red_pago=row["Modalidad de Pago"],
                    ref_bancaria=row["CUS"],
                    ref_red="",
                    ref_cliente_1=row["Nombre"],
                    ref_cliente_2=row["Referencia Externa"],
                    ref_cliente_3=row["Ramo"],

                    estado_transaccion_reportado=row["Estado"],
                    cliente_id_reportado=row["Cédula"],

                    fecha_pago=fecha_pago,
                    hora_pago=hora_pago,

                    valor_pago=row["Valor pago"],
                )

                p.save()

                cargados += 1
                valor_total += float(row["Valor pago"])

            except Exception as e:
                rechazados += 1
                continue  # continuar al siguiente registro

        # -------------------------------------------------------
        # Actualizar Pagos_Archivos
        # -------------------------------------------------------
        pagos_archivo.valor_total = valor_total
        pagos_archivo.registros_cargados = cargados
        pagos_archivo.registros_rechazados = rechazados
        pagos_archivo.estado_proceso_archivo = "RECIBIDO"
        pagos_archivo.save()

    return True, f"Archivo procesado: {cargados} registros cargados, {rechazados} rechazados."


#Fin cargar archivos PSE
#----------------------------------------------------------------2025/11/26
#Extracto Bancolombia
#–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
import pdfplumber
import io
from django.utils import timezone

def safe(txt, maxlen):
    """Evita errores de overflow truncando cadenas."""
    if txt is None:
        return ""
    return txt[:maxlen]


def leer_pagos_bancolombia(pdf_file, nombre_archivo_id):
    from .models import BancolombiaExtracto, BancolombiaMovimientos

    try:
        # ---------------------------------------------------
        # LEER PDF DESDE MEMORIA (SOLUCIÓN AL ERROR)
        # ---------------------------------------------------
        pdf_bytes = io.BytesIO(pdf_file.read())

        texto = ""
        with pdfplumber.open(pdf_bytes) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto += t + "\n"

        lineas = texto.split("\n")
       
       

    except Exception as e:
        raise Exception(f"Error leyendo el PDF: {e}")

    # ---------------------------------------------------
    # PROCESAR LÍNEA A LÍNEA
    # ---------------------------------------------------
    for linea in lineas:
        reg = linea.strip()
        print("PDF leído correctamente. Líneas:", reg)

        if len(reg) < 6:
            continue

        tipo_reg = reg[:5]
        #print("tipo Reg :", tipo_reg)
          
        # ==========================================
        # EMPRESA
        # ==========================================
        if tipo_reg == "Empre":
            #BancolombiaExtracto.objects.filter(pk=nombre_archivo_id).update(
            v_empresa=safe(reg[10:31].strip(), 30),
            v_numero_cuenta=safe(reg[50:61].strip(), 12),
            v_fecha_hora_actual=safe(reg[50:70].strip(), 20),
            v_registro_extracto=safe(reg, 149)
            #)

        # ==========================================
        # NIT
        # ==========================================
        elif tipo_reg[:4] == "NIT:":
            #BancolombiaExtracto.objects.filter(pk=nombre_archivo_id).update(
            v_nit=safe(reg[6:15].strip(), 16),
            v_tipo_cuenta=safe(reg[44:53].strip(), 20),
            v_fecha_hora_consulta=safe(reg[77:96].strip(), 20)
            #)

        # ==========================================
        # SALDOS
        # ==========================================
        elif tipo_reg == "Saldo":
            partes = [p for p in reg.split(" ") if "$" in p]
            if len(partes) >= 3:   
                BancolombiaExtracto.objects.filter(pk=nombre_archivo_id).update(
                    empresa					=	v_empresa,
                    numero_cuenta			=	"999999", #v_numero_cuenta[:10],
                    fecha_hora_actual		=	v_fecha_hora_actual,
                    nit						=	v_nit,
                    tipo_cuenta				=	v_tipo_cuenta,
                    fecha_hora_consulta		=	v_fecha_hora_consulta,
                    registro_extracto		=	reg[:149],
                    saldo_efectivo_actual	=	safe(partes[0], 20),
                    saldo_en_canje_actual	=	safe(partes[1], 20),
                    saldo_total_actual		=	safe(partes[2], 20),
                )
        # ==========================================
        # MOVIMIENTOS
        # Formato esperado: YYYY/MM/DD ...
        # ==========================================
       
        elif reg[:4].isdigit() and reg[4] == "/":
            print("tipo reg antes de grabar = :", tipo_reg)
            try:
                #fecha_raw = reg[0:10]
                #descripcion = reg[12: reg.rfind(" ")]
                #valor_raw = reg[reg.rfind(" "):].replace(" ", "").replace(",", "")
            
                '''
            	BancolombiaMovimientos.objects.create(
                	nombre_archivo_id_id	=	nombre_archivo_id,
                	fecha_movimiento		=	timezone.now(),
                	descripcion				=	"descripcion", #safe(descripcion, 70),
                	sucursal_canal 			=	"sucursal_canal",
                	referencia_1			= 	"ref_1",
                	referencia_2			=	"ref_2",
                	documento				= 	"documento",
                	valor					=	5697486, #valor_raw,
                	estado_movimiento		=	"RECBIDO",
                	clase_movimiento		= 	null,
                	cliente_id_real			=	null,
                	prestamo_id_real		= 	null,
                	registro_extracto		=	reg[:150]
                	)
                BancolombiaMovimientos.save()
             except Exception as e:
                print("Error creando movimiento:", e)
                continue
             ''' 

 				BancolombiaMovimientos(
                    # Relación con archivo
                    #nombre_archivo_id_id=pagos_archivo.nombre_archivo_id,
                    nombre_archivo_id_id	=	nombre_archivo_id,
                	fecha_movimiento		=	timezone.now(),
                	descripcion				=	"descripcion", #safe(descripcion, 70),
                	sucursal_canal 			=	"sucursal_canal",
                	referencia_1			= 	"ref_1",
                	referencia_2			=	"ref_2",
                	documento				= 	"documento",
                	valor					=	5697486, #valor_raw,
                	estado_movimiento		=	"RECBIDO",
                	clase_movimiento		= 	null,
                	cliente_id_real			=	null,
                	prestamo_id_real		= 	null,
                	registro_extracto		=	"Registro"
                )
                
                print("Nombre archivo en salvar = ", nombre_archivo_id )

                except Exception as e:
                    print("Error creando movimiento:", e)
                    continue

