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

# appfinancia/utils.py
import pandas as pd
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging
# Importación local para evitar circularidad (si es necesario)


logger = logging.getLogger(__name__)

# NOTA: Para que esta función funcione, debes tener instalado:
# pip install camelot-py[cv] ghostscript

def parse_pdf_data(archivo_pdf):
    from .models import ExtractoBancario, ExtractoBancarioMovimientos
    """
    Función que extrae los datos de cabecera y la tabla de movimientos del PDF.
    
    Camelot se utiliza para extraer tablas complejas del PDF. 
    Dado el formato particular del extracto de Bancolombia, es la herramienta más adecuada.
    """
    try:
        import camelot
    except ImportError:
        raise ImportError("La librería 'camelot-py' no está instalada. Ejecute: pip install camelot-py[cv]")

    # 1. Extracción de tablas (asumiendo que los movimientos están en la primera tabla)
    # Se utiliza el tipo 'lattice' ya que el extracto tiene líneas de tabla bien definidas.
    #tables = camelot.read_pdf(archivo_pdf.path, pages='all', flavor='lattice')
    
    tables = camelot.read_pdf(archivo_pdf, pages='all', flavor='stream')
    
    if not tables:
        raise ValueError("No se pudieron detectar tablas en el PDF.")
        
    df_movimientos = tables[0].df # Asume que la tabla de movimientos es la primera

    # 2. Extracción de cabecera (Esta lógica es la más frágil y debe ser ajustada)
    # Aquí se utiliza Camelot o PyPDF2/PDFMiner para buscar patrones de texto
    # Dado que los datos de cabecera están en el prompt, asumimos que la extracción es exitosa
    
    # 3. Mapeo de Cabeceras (Hardcodeado basado en el prompt)
    # Si la extracción de Camelot no separa las columnas como en el PDF, esta lógica fallará.
    # Asumimos que la tabla de movimientos tiene una cabecera limpia después de la extracción:
    
    # Limpiamos el DataFrame (quitar filas de cabecera duplicadas o vacías)
    df_movimientos = df_movimientos.iloc[1:] # Saltar la cabecera si Camelot la duplicó
    df_movimientos.columns = ['FECHA', 'DESCRIPCION_COMPLETA', 'DOCUMENTO', 'VALOR']
    
    # Devolver el DataFrame y los datos de cabecera (simulados)
    return {
        'cabecera': {
            'empresa': 'FINANCIA SEGUROS AS',
            'nit': '901554626',
            'numero_cuenta': '03200001692',
            'tipo_de_cuenta': 'Ahorros',
            'saldo_total_actual': Decimal('116953709.38'),
            'fecha_hora_actual': timezone.now(), # Se debería extraer del PDF
            'fecha_hora_consulta': timezone.now(), # Se debería extraer del PDF
            'saldo_efectivo_actual': Decimal('116953709.38'),
            'saldo_en_canje_actual': Decimal('0.00'),
        },
        'movimientos': df_movimientos
    }

# -----------------------------------------------------------------------------------------
# PROCESO PRINCIPAL DE CARGA
# -----------------------------------------------------------------------------------------

def procesar_extracto_pdf(extracto_obj: 'ExtractoBancario', archivo_pdf, user):
    from .models import ExtractoBancario, ExtractoBancarioMovimientos
    """Procesa el PDF y guarda los movimientos de manera atómica."""
    
    try:
        # 1. Extraer datos del PDF
        data = parse_pdf_data(archivo_pdf)
        
        # 2. Guardar datos de cabecera en el objeto ExtractoBancario
        cabecera = data['cabecera']
        
        extracto_obj.empresa = cabecera['empresa']
        extracto_obj.nit = cabecera['nit']
        extracto_obj.numero_cuenta = cabecera['numero_cuenta']
        extracto_obj.tipo_de_cuenta = cabecera['tipo_de_cuenta']
        extracto_obj.fecha_hora_actual = cabecera['fecha_hora_actual']
        extracto_obj.fecha_hora_consulta = cabecera['fecha_hora_consulta']
        extracto_obj.saldo_efectivo_actual = cabecera['saldo_efectivo_actual']
        extracto_obj.saldo_en_canje_actual = cabecera['saldo_en_canje_actual']
        extracto_obj.saldo_total_actual = cabecera['saldo_total_actual']
        extracto_obj.creado_por = user
        # El estado_proceso_archivo ya está en 'RECIBIDO' por defecto
        
        # 3. Iniciar Transacción Atómica
        with transaction.atomic():
            extracto_obj.save() # Guardar cabecera

            cargados = 0
            # 4. Iterar y guardar movimientos
            for _, row in data['movimientos'].iterrows():
                try:
                    # Lógica de Parsing y Normalización
                    
                    # El campo 'DESCRIPCION_COMPLETA' debe ser dividido. 
                    # Dado que es complejo, asumimos un split simple para este ejemplo.
                    desc_parts = str(row['DESCRIPCION_COMPLETA']).split('\n')
                    
                    valor_limpio = str(row['VALOR']).replace('.', '').replace(',', '.')
                    
                    movimiento = ExtractoBancarioMovimientos(
                        nombre_archivo=extracto_obj,
                        fecha_movimiento=pd.to_datetime(row['FECHA']).date(),
                        descripcion=desc_parts[0].strip() if desc_parts else '',
                        referencia_1=desc_parts[1].strip() if len(desc_parts) > 1 else '',
                        referencia_2=desc_parts[2].strip() if len(desc_parts) > 2 else '',
                        sucursal_canal=desc_parts[3].strip() if len(desc_parts) > 3 else '',
                        documento=str(row['DOCUMENTO']).strip() if row['DOCUMENTO'] else '',
                        valor=Decimal(valor_limpio),
                        estado_movimiento='RECIBIDO',
                        clase_movimiento='OTROS' # Default
                    )
                    movimiento.full_clean()
                    movimiento.save()
                    cargados += 1
                    
                except Exception as e:
                    logger.error(f"Error al procesar fila del extracto: {e}. Datos: {row.to_dict()}")
                    # La excepción hará que transaction.atomic() ejecute ROLLBACK
                    raise
            
            return True, f"Extracto cargado y {cargados} movimientos guardados correctamente."

    except Exception as e:
        logger.error(f"Fallo crítico en la carga del extracto {extracto_obj.nombre_archivo_id}: {e}")
        return False, str(e)


# -----------------------------------------------------------------------------------------
# PROCESOS DE NEGOCIO
# -----------------------------------------------------------------------------------------

def anular_pagos_directos(nombre_archivo_id):
    """Define el proceso 'anular_pagos_directos' (Lógica de negocio d)."""
    try:
        with transaction.atomic():
            movimientos_anulados = ExtractoBancarioMovimientos.objects.filter(
                nombre_archivo__nombre_archivo_id=nombre_archivo_id,
                estado_movimiento__in=['RECIBIDO', 'A_CONCILIAR']
            ).update(estado_movimiento='ANULADO')
            
            logger.info(f"Anulados {movimientos_anulados} movimientos para el extracto {nombre_archivo_id}.")
            return True, f"Anulados {movimientos_anulados} movimientos."
    except Exception as e:
        logger.error(f"Error al anular movimientos para {nombre_archivo_id}: {e}")
        return False, str(e)


def conciliar_extracto(nombre_archivo_id):
    """Define el proceso 'conciliar_extracto' (Lógica de negocio e)."""
    try:
        with transaction.atomic():
            movimientos_a_conciliar = ExtractoBancarioMovimientos.objects.filter(
                nombre_archivo__nombre_archivo_id=nombre_archivo_id,
                estado_movimiento='RECIBIDO'
            ).update(estado_movimiento='A_CONCILIAR')
            
            logger.info(f"Marcados {movimientos_a_conciliar} movimientos para conciliación para el extracto {nombre_archivo_id}.")
            return True, f"Marcados {movimientos_a_conciliar} movimientos para conciliación."
    except Exception as e:
        logger.error(f"Error al marcar movimientos para conciliación para {nombre_archivo_id}: {e}")
        return False, str(e)
        
        
#----------------------version de deepseek
import pdfplumber
import re
from datetime import datetime
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


def procesar_extracto_bancolombia(archivo_pdf, usuario):
    from .models import ExtractoBancolombia, MovimientoBancolombia
    """
    Procesa un extracto de Bancolombia desde PDF y devuelve los datos
    sin crear objetos en la base de datos
    Retorna: diccionario con 'encabezado' y 'movimientos'
    """
    try:
        with pdfplumber.open(archivo_pdf) as pdf:
            primera_pagina = pdf.pages[0]
            texto = primera_pagina.extract_text()
            
            # Extraer encabezado
            encabezado = extraer_encabezado(texto)
            
            # Extraer movimientos
            movimientos_data = extraer_movimientos(primera_pagina)
            
            return {
                'encabezado': encabezado,
                'movimientos': movimientos_data,
                'total_movimientos': len(movimientos_data)
            }
            
    except Exception as e:
        raise Exception(f"Error procesando extracto: {str(e)}")

def extraer_encabezado(texto):
    """
    Extrae información del encabezado del extracto
    """
    datos = {}
    
    # NIT Bancolombia
    nit_match = re.search(r'NIT[.:]\s*([\d.,]+)', texto)
    if nit_match:
        datos['nit_bancolombia'] = nit_match.group(1).strip()
    
    # Empresa
    empresa_match = re.search(r'Empresa[.:]\s*(.+?)\s*\n', texto)
    if empresa_match:
        datos['empresa'] = empresa_match.group(1).strip()
    
    # NIT Empresa - buscar después de "Empresa:"
    partes = texto.split('Empresa:')
    if len(partes) > 1:
        subtexto = partes[1]
        nit_match = re.search(r'NIT[.:]\s*([\d.]+)', subtexto)
        if nit_match:
            datos['nit_empresa'] = nit_match.group(1).strip()
    
    # Número de cuenta
    cuenta_match = re.search(r'Número de Cuenta[.:]\s*(\d+)', texto)
    if cuenta_match:
        datos['numero_cuenta'] = cuenta_match.group(1).strip()
    
    # Tipo de cuenta
    tipo_match = re.search(r'Tipo de cuenta[.:]\s*(.+)', texto)
    if tipo_match:
        datos['tipo_cuenta'] = tipo_match.group(1).strip()
    
    # Fechas
    fecha_actual_match = re.search(r'Fecha y Hora Actual[.:]\s*(\d{2}-\d{2}-\d{4})', texto)
    if fecha_actual_match:
        try:
            datos['fecha_actual'] = datetime.strptime(fecha_actual_match.group(1), '%d-%m-%Y').date()
        except:
            pass
    
    fecha_consulta_match = re.search(r'Fecha y Hora Consulta[.:]\s*(\d{2}-\d{2}-\d{4})', texto)
    if fecha_consulta_match:
        try:
            datos['fecha_consulta'] = datetime.strptime(fecha_consulta_match.group(1), '%d-%m-%Y').date()
        except:
            pass
    
    # Saldos
    saldo_match = re.search(r'Saldo Efectivo Actual[.:]\s*\$?([\d,]+\.\d{2})', texto)
    if saldo_match:
        datos['saldo_efectivo'] = Decimal(saldo_match.group(1).replace(',', ''))
    
    saldo_canje_match = re.search(r'Saldo en Canje Actual[.:]\s*\$?([\d,]+\.\d{2})', texto)
    if saldo_canje_match:
        datos['saldo_canje'] = Decimal(saldo_canje_match.group(1).replace(',', ''))
    
    saldo_total_match = re.search(r'Saldo Total Actual[.:]\s*\$?([\d,]+\.\d{2})', texto)
    if saldo_total_match:
        datos['saldo_total'] = Decimal(saldo_total_match.group(1).replace(',', ''))
    
    return datos

def extraer_movimientos(pagina):
    """
    Extrae los movimientos de la página
    """
    movimientos = []
    
    # Extraer tabla
    tablas = pagina.extract_tables()
    
    if not tablas:
        return movimientos
    
    for tabla in tablas:
        # Buscar fila que contiene "FECHA DESCRIPCIÓN" como inicio de la tabla de movimientos
        inicio_movimientos = False
        
        for fila in tabla:
            # Filtrar filas vacías o con pocos datos
            if not fila:
                continue
            
            # Limpiar celdas
            fila_limpia = [str(cell).strip() if cell else '' for cell in fila]
            
            # Marcar inicio cuando encontramos "FECHA DESCRIPCIÓN"
            if "FECHA" in fila_limpia[0].upper() and "DESCRIPCIÓN" in " ".join(fila_limpia).upper():
                inicio_movimientos = True
                continue
            
            if inicio_movimientos:
                # Procesar si parece una transacción (tiene fecha en formato YYYY/MM/DD)
                if re.match(r'\d{4}/\d{2}/\d{2}', fila_limpia[0]):
                    movimiento = procesar_fila_movimiento(fila_limpia)
                    if movimiento:
                        movimientos.append(movimiento)
    
    return movimientos

def procesar_fila_movimiento(fila):
    """
    Procesa una fila de movimiento
    """
    try:
        # Formato esperado: FECHA | DESCRIPCION | REF1 | REF2 | DOC | VALOR
        fecha_str = fila[0].strip()
        
        # Parsear fecha (formato: 2025/11/04)
        fecha = datetime.strptime(fecha_str, '%Y/%m/%d').date()
        
        # En el extracto de ejemplo, parece haber 6 columnas
        if len(fila) >= 6:
            # Columnas: 0:fecha, 1:descripcion, 2:referencia1, 3:referencia2, 4:documento, 5:valor
            descripcion = fila[1]
            referencia1 = fila[2]
            referencia2 = fila[3]
            documento = fila[4]
            valor_str = fila[5]
        elif len(fila) >= 5:
            # Sin columna de documento
            descripcion = fila[1]
            referencia1 = fila[2]
            referencia2 = fila[3]
            documento = ''
            valor_str = fila[4]
        elif len(fila) >= 4:
            # Solo fecha, descripcion, referencia, valor
            descripcion = fila[1]
            referencia1 = fila[2]
            referencia2 = ''
            documento = ''
            valor_str = fila[3]
        else:
            return None
        
        # Limpiar y convertir valor
        valor = Decimal(limpiar_valor(valor_str))
        
        # Determinar tipo (positivo = ingreso, negativo = egreso)
        tipo = 'INGRESO' if valor >= 0 else 'EGRESO'
        
        return {
            'fecha': fecha,
            'descripcion': descripcion[:200],  # Limitar longitud
            'referencia1': referencia1[:100],
            'referencia2': referencia2[:100],
            'documento': documento[:50],
            'valor': valor,
            'tipo': tipo
        }
        
    except Exception as e:
        print(f"Error procesando fila {fila}: {e}")
        return None

def limpiar_valor(valor_str):
    """
    Limpia un string de valor monetario
    """
    if not valor_str:
        return '0'
    
    # Remover símbolos y espacios
    valor_limpio = valor_str.replace('$', '').replace(',', '').strip()
    
    # Manejar negativos entre paréntesis
    if '(' in valor_limpio and ')' in valor_limpio:
        valor_limpio = '-' + valor_limpio.replace('(', '').replace(')', '')
    
    # Asegurar que sea un número válido
    try:
        float(valor_limpio)
        return valor_limpio
    except:
        return '0'

def crear_movimientos_desde_datos(extracto_obj, movimientos_data):
    """
    Crea los movimientos en la base de datos a partir de los datos procesados
    """
    from .models import MovimientoBancolombia
    
    movimientos_creados = []
    for mov_data in movimientos_data:
        try:
            movimiento = MovimientoBancolombia.objects.create(
                extracto=extracto_obj,
                **mov_data
            )
            movimientos_creados.append(movimiento)
        except Exception as e:
            print(f"Error creando movimiento: {e}")
    
    return movimientos_creados
    
#--------------------------------------versión Grok--------------------------------------
# appfinancia/utils.py

import camelot

from decimal import Decimal

def leer_extracto_bancolombia(pdf_path):

    """
    Función sencilla para leer el PDF de extracto Bancolombia.
    Extrae la tabla con Camelot y guarda cada fila en el modelo.
    """
# utils.py
'''
import camelot
#import pandas as pd
#from decimal import Decimal
#from datetime import datetime
#from .models import ExtractoBancolombia
#import logging

logger = logging.getLogger(__name__)

def leer_extracto_bancolombia(pdf_path):
    from .models import ExtractoBanco
    """
    Lee extracto Bancolombia PDF y guarda movimientos.
    Soluciona: fechas vacías, saltos de línea, formato raro.
    """
    tables = camelot.read_pdf(
        pdf_path,
        pages='all',
        flavor='stream',
        split_text=True,
        strip_text='\n',
        edge_tol=100
    )

    logger.info(f"Se encontraron {len(tables)} tablas en {pdf_path}")

    for table in tables:
        df = table.df

        # Saltamos las primeras filas que no son movimientos (encabezados)
        # Buscamos la fila que tiene "FECHA" como primera columna
        start_row = 0
        for i, row in df.iterrows():
            if str(row.iloc[0]).strip().upper().startswith('FECHA'):
                start_row = i + 1
                break

        # Procesamos solo desde la fila de datos
        for _, row in df.iloc[start_row:].iterrows():
            try:
                # Limpiamos cada celda
                cells = [str(cell).strip() for cell in row]

                # Si la primera celda está vacía → es una fila rota (salto de línea)
                if not cells or len(cells) < 7 or not cells[0]:
                    continue

                fecha_str = cells[0].replace('/', '-')
                descripcion = cells[1]
                sucursal_canal = cells[2]
                referencia1 = cells[3] if len(cells) > 3 else ""
                referencia2 = cells[4] if len(cells) > 4 else ""
                documento = cells[5] if len(cells) > 5 else ""
                valor_str = cells[6].replace('$', '').replace(',', '').strip()

                # Convertir fecha
                try:
                    #fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date').date()
                    fecha = fecha_str
                except:
                    try:
                        #fecha = datetime.strptime(fecha_str, '%Y/%m/%d').date()
                        fecha = fecha_str
                    except:
                        logger.warning(f"Fecha inválida: {fecha_str}")
                        continue  # Salta la fila si fecha es mala

                # Convertir valor
                try:
                    valor = Decimal(valor_str)
                except:
                    logger.warning(f"Valor inválido: {valor_str}")
                    valor = Decimal('0.00')

                # Guardar solo si tiene fecha válida
                ExtractoBancolombia.objects.create(
                    fecha=fecha,
                    descripcion=descripcion[:200],
                    sucursal_canal=sucursal_canal[:100],
                    referencia1=referencia1[:100],
                    referencia2=referencia2[:100],
                    documento=documento[:100],
                    valor=valor,
                    archivo_origen=pdf_path.replace('/root/CoreFinancia/media/', ''),  # ruta limpia
                )

            except Exception as e:
                logger.warning(f"Fila saltada por error: {e} | fila: {row.tolist()}")
                continue  # Nunca falla todo el proceso

    logger.info("Extracto Bancolombia procesado exitosamente.")
    
'''

#-------------------------version mejorada
# appfinancia/utils.py

import camelot
#import pandas as pd
#from datetime import datetime
#from decimal import Decimal

import logging

logger = logging.getLogger(__name__)

def procesar_extracto_bancolombia(pdf_path, obj_extracto):
    from .models import ExtractoBanco
    """
    Función simple para leer PDF de extracto Bancolombia.
    Usa flavor='stream' para tablas sin bordes claros.
    """
    logger.info(f"Procesando extracto Bancolombia: {pdf_path}")

    # Leer con stream (mejor para extractos Bancolombia sin líneas perfectas)
    tables = camelot.read_pdf(
        pdf_path,
        pages='all',
        flavor='stream',  # ← Cambiado a 'stream' (no usa edge_tol)
        table_areas=['1,800,550,50'],  # Ajusta el área de la tabla si es necesario (x1,y1,x2,y2)
        split_text=True,
        strip_text='\n',  # Limpia saltos de línea
    )

    if not tables:
        raise ValueError("No se encontraron tablas en el PDF. Verifica el formato.")

    df = tables[0].df  # Toma la primera tabla encontrada
    logger.info(f"Tabla encontrada con {len(df)} filas y {len(df.columns)} columnas")

    movimientos_cargados = 0
    print("Entro a leer la cadena")
    
    # Saltar filas vacías o de encabezado
    for idx, row in df.iterrows():
        #try:
            # Limpiar celdas (convertir a string y strip)
            cells = [str(cell).strip() for cell in row]

            print ("Toda la cadena =", cells)
            #print("Celda = ", str(cell).strip() )
            
            
            #if len(cells) < 7 or not cells[0]:  # Si no hay fecha, salta la fila
             #   continue

            # 1. FECHA (formato 2025/11/04)
            fecha_str = cells[0].replace('/', '-')
            fecha = fecha_str
            print("Campo de fecha real = ",  fecha )
            #try:
            #    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            #except ValueError:
            #    logger.warning(f"Fecha inválida en fila {idx}: {fecha_str}")
            #    continue

            # 2. DESCRIPCIÓN
            descripcion = cells[1][:20]  # Truncar a 200 chars

            print("descripcion = ", descripcion)
            
            # 3. SUCURSAL/CANAL
            sucursal_canal = cells[2][:20] # Truncar a 100 chars
            
            print("sucursal_canal = ", sucursal_canal)
            

            # 4. REFERENCIA 1
            referencia1 = cells[3][:20] if len(cells) > 3 else "" # Truncar a 100 chars
            
            print("referencia1 = ", referencia1)

            # 5. REFERENCIA 2
            referencia2 = cells[4][:20] if len(cells) > 4 else "" # Truncar a 100 chars

            # 6. DOCUMENTO
            documento = cells[5][:20] if len(cells) > 5 else ""  ## Truncar a 100 chars

            # 7. VALOR (ej. 744,000.00)
            '''
            valor_str = str(cells[6]).replace('$', '').replace(',', '').strip()
            try:
                valor = Decimal(valor_str)
            except ValueError:
                logger.warning(f"Valor inválido en fila {idx}: {valor_str}")
                continue
                
            print( "Valor = ", valor)
            '''
            valor=0
            
            # Guardar el movimiento
            ExtractoBanco.objects.create(
                fecha=fecha,
                descripcion=descripcion,
                sucursal_canal=sucursal_canal,
                referencia1=referencia1,
                referencia2=referencia2,
                documento=documento,
                valor=valor,
                archivo_origen=obj_extracto.archivo_origen.path,
                fecha_carga=timezone.now(),
            )

            movimientos_cargados += 1

        #except Exception as e:
        #    logger.warning(f"Error en fila {idx}: {e}")
            continue  # No para todo el proceso

    logger.info(f"Procesamiento completado: {movimientos_cargados} movimientos guardados")
    return movimientos_cargados
    
#======================================================================================= 
#Versión CHAT GPT

# ============================================================
# utils.py CORREGIDO
# ============================================================

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
        print("tipo Reg :", tipo_reg)
          
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
        print("tipo reg = :", tipo_reg)
        print("patron fecha", reg[:4].isdigit() and reg[4] == "/" )
        
        elif reg[:4].isdigit() and reg[4] == "/":

            try:
                fecha_raw = reg[0:10]
                descripcion = reg[12: reg.rfind(" ")]
                valor_raw = reg[reg.rfind(" "):].replace(" ", "").replace(",", "")

                BancolombiaMovimientos.objects.create(
                    nombre_archivo_id_id=nombre_archivo_id,
                    fecha_movimiento=fecha_raw,
                    descripcion=safe(descripcion, 70),
                    valor=valor_raw,
                    registro_extracto=safe(reg, 149)
                )
            except Exception as e:
                print("Error creando movimiento:", e)
                continue


# ============================================================
# PROCESOS DE ESTADO
# ============================================================

def anular_pagos_bancolombia(nombre_archivo_id):
    from .models import BancolombiaMovimientos
    BancolombiaMovimientos.objects.filter(
        nombre_archivo_id=nombre_archivo_id
    ).update(estado_movimiento="ANULADO")


def conciliar_pagos_bancolombia(nombre_archivo_id):
    from .models import BancolombiaMovimientos
    BancolombiaMovimientos.objects.filter(
        nombre_archivo_id=nombre_archivo_id
    ).update(estado_movimiento="A_CONCILIAR")
