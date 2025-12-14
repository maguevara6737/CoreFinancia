# utils.py
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Sum
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
    return _increment_field('numerador_operacion')

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
from django.utils import timezone


def create_loan_payments(prestamo, desembolso, plan_pagos, user_name):
    """
    Guarda el plan de pagos generado por calculate_loan_schedule
    como registros en Historia_Prestamos, usando los conceptos adecuados.
    """
    from .models import Fechas_Sistema, Conceptos_Transacciones, Historia_Prestamos  # ✅ Corregido

    # Obtener el concepto "DES"
    concepto_des = Conceptos_Transacciones.objects.get(concepto_id="DES")
    fechas_sistema = Fechas_Sistema.load()
    # Registrar el desembolso como primer histórico
    Historia_Prestamos.objects.create(
        prestamo_id=prestamo,
        fecha_efectiva=desembolso.fecha_desembolso,
        fecha_proceso=fechas_sistema.fecha_proceso_actual,  # o timezone.now().date()
        ordinal_interno=1,
        numero_cuota=0,
        numero_operacion=0,
        concepto_id=concepto_des,
        fecha_vencimiento=desembolso.fecha_vencimiento,
        tasa=desembolso.tasa,
        monto_transaccion=desembolso.valor,
        estado="TRANSACCION ",  # ¡incluye el espacio como en tu ESTADO_CHOICES!
        usuario=user_name,
        # abono_capital, intrs_ctes, seguro, fee se dejan en 0 por defecto
    )
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
                fecha_efectiva=None,
                fecha_proceso=fechas_sistema.fecha_proceso_actual,
                ordinal_interno=300+created_count,
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
                fecha_efectiva=None,
                fecha_proceso=fechas_sistema.fecha_proceso_actual,
                ordinal_interno=300+created_count,
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
                fecha_efectiva=None,
                fecha_proceso=fechas_sistema.fecha_proceso_actual,
                ordinal_interno=300+created_count,
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
                fecha_efectiva=None,
                fecha_proceso=fechas_sistema.fecha_proceso_actual,
                ordinal_interno=300+created_count,
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
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

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
    
    ✅ Ajustado para ignorar valor_cuota_1 y calcular todas las cuotas sobre desembolso.valor
    """
    results = []
    monto = Decimal(desembolso.valor or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    plazo_total = int(desembolso.plazo_en_meses or 0)

    # Si no hay monto o plazo, retornar vacío
    if monto <= 0 or plazo_total <= 0:
        return results

    # tasa anual en porcentaje -> convertir a decimal mensual con 30/360
    tasa_pct = Decimal(desembolso.tasa or 0)
    tasa_mensual = (tasa_pct / Decimal('100')) * (Decimal('30') / Decimal('360'))

    # Calcular pago nivelado (anualidad) sobre 'monto' con 'plazo_total' periodos
    r = tasa_mensual
    n = plazo_total

    if r == 0:
        pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        one_plus_r = Decimal('1') + r
        denom = Decimal('1') - (one_plus_r ** (Decimal(-n)))
        if denom == 0 or denom < 0:
            pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            pago_mensual = (monto * r / denom).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    saldo = monto
    fecha_base = desembolso.fecha_desembolso

    # Generar todas las cuotas (1 a plazo_total)
    for i in range(plazo_total):
        numero = i + 1

        if r == 0:
            intereses = Decimal('0.00')
            capital = pago_mensual
        else:
            intereses = (saldo * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            capital = (pago_mensual - intereses).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # Ajuste en la última cuota para evitar residuos
        if numero == plazo_total:
            capital = saldo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            intereses = (pago_mensual - capital).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if intereses < 0:
                intereses = Decimal('0.00')

        # Calcular fecha de vencimiento
        try:
            fecha_venc = fecha_base + relativedelta(months=i)
            target_day = int(fecha_base.day)
            # Asegurar día válido (máx 28 para evitar errores en fechas como 31 de febrero)
            day_to_use = min(target_day, 28)
            fecha_venc = fecha_venc.replace(day=day_to_use)
        except Exception:
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
#-----------
#2025-11-25 6:52am traslado funcion pasar_a_desembolsado a utils.py
""" def pasar_a_desembolsado(self, request, queryset):
    updated = queryset.filter(estado='A_DESEMBOLSAR').update(estado='DESEMBOLSADO')
    self.message_user(request, f"{updated} desembolso(s) pasado(s) a DESEMBOLSADO.")
pasar_a_desembolsado.short_description = "Pasar a DESEMBOLSADO" 
 """


#---------------------------------------------------------------------------------------
#FUNCIÓN: Cerrar período de interés para calculo y causacion
# utils.py
# utils.py

def cerrar_periodo_interes(prestamo_id: int, fecha_corte: date, pago_referencia=None, numero_asiento_contable=None,  capital_aplicado=0):
    """
    Cierra el período de interés para un préstamo en una fecha específica. -v9- 
    Crea un registro de tipo 'CAUSAC' en Historia_Prestamos con el interés causado.
    Nota si modifica esta funcion, analice si debe modificar cerrar_todos_periodos_hasta
    """
    from decimal import Decimal
    from django.db.models import Sum
    from .models import Conceptos_Transacciones, Prestamos, Historia_Prestamos

    # Obtener el concepto de causación
    concepto_causacion = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
    
    # Obtener el préstamo (con bloqueo)
    prestamo = Prestamos.objects.select_for_update().get(prestamo_id=prestamo_id)

    # Evitar duplicados de causación en la misma fecha  2025-12-04 lo quito porque puede haber varios pagos el mismo dia...
    #if Historia_Prestamos.objects.filter(
    #    prestamo_id=prestamo_id,
    #    fecha_proceso=fecha_corte,         #
    #    concepto_id=concepto_causacion
    #).exists():
    #    return

    # === 1. Obtener el monto del desembolso (capital inicial) ===
    try:
        valor_desembolso = prestamo.prestamo_id.valor
    except (AttributeError, TypeError):
        valor_desembolso = Decimal('0')

    # === 2. Calcular total de abonos a capital ANTES de la fecha de corte ===
    abonos_result = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_efectiva__isnull=False, 
        fecha_efectiva__lte=fecha_corte,   # <= incluye el mismo día
        abono_capital__gt=0
    ).aggregate(total_abonos=Sum('abono_capital'))
    
    total_abonos = abonos_result['total_abonos'] or Decimal('0')
    saldo_capital = valor_desembolso - total_abonos
    if saldo_capital < 0:
        saldo_capital = Decimal('0')

    # === 3. Obtener intereses acumulados del último registro anterior ===
    ultimo_registro = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_proceso__lt=fecha_corte
    ).order_by('-fecha_proceso').first()
    
    intereses_acumulados = ultimo_registro.intrs_ctes or Decimal('0') if ultimo_registro else Decimal('0')

    # === 4. Calcular interés del día ===
    tasa_diaria = prestamo.tasa / Decimal('100') / Decimal('360')
    interes_diario = saldo_capital * tasa_diaria if saldo_capital > 0 else Decimal('0')
    nuevos_intereses = intereses_acumulados + interes_diario

    # === 5. Crear registro de causación (CAUSAC) ===
    Historia_Prestamos.objects.create(
        prestamo_id=prestamo,                # ✅ FK: usa 'prestamo_id', no 'prestamo'
        fecha_proceso=fecha_corte,           # ✅ obligatorio
        fecha_efectiva=None,                 # ✅ causación no tiene fecha efectiva
        concepto_id=concepto_causacion,      # ✅ FK al concepto
        monto_transaccion=interes_diario,    # ✅ interés causado HOY
        intrs_ctes=nuevos_intereses,         # ✅ total acumulado hasta HOY
        abono_capital=Decimal('0'),          # ✅ no es un abono
        seguro=Decimal('0'),                 # ✅ no causamos seguro aquí
        fee=Decimal('0'),                    # ✅ no causamos fee aquí
        tasa=prestamo.tasa,
        fecha_vencimiento=fecha_corte,       # ✅ opcional: puedes usar None si prefieres
        estado='TRANSACCION',
        usuario='sistema',                   # ✅ ajusta si tu app requiere otro valor
        numero_cuota=None,                   # ✅ no pertenece a una cuota
        ordinal_interno=10,                  #Ordinal interno debe ser 10
        numero_operacion=numero_asiento_contable,                   # ✅ asegúrate que no duplique unique_together
        capital_aplicado_periodo=capital_aplicado or 0,  
        numero_pago_referencia=pago_referencia or "",
        numero_asiento_contable=numero_asiento_contable or 0
    )
#-------------------------------------------------------------------------------------------------------
#   funciones para consulta de causacion - contabilidad
#----------------------------------------------------------------------------------------------------
# utils.py - NUEVA FUNCIÓN PARA CONSULTAS
def cerrar_todos_periodos_hasta(prestamo_id: int, fecha_corte: date):
    """
    Cierra TODOS los períodos de interés faltantes hasta fecha_corte.
    Crea registros CAUSAC para cada fecha de evento (desembolso, pagos) hasta fecha_corte.
    """
    from decimal import Decimal
    from django.db.models import Sum
    from .models import Conceptos_Transacciones, Prestamos, Historia_Prestamos, Pagos
    
    # Obtener el concepto de causación
    concepto_causacion = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
    
    # Obtener el préstamo
    prestamo = Prestamos.objects.select_for_update().get(prestamo_id=prestamo_id)
    
    # Obtener todas las fechas de eventos hasta fecha_corte
    fechas_eventos = set()
    
    # Agregar fecha de desembolso
    if prestamo.fecha_desembolso and prestamo.fecha_desembolso <= fecha_corte:
        fechas_eventos.add(prestamo.fecha_desembolso)
    
    # Agregar fechas de pagos aplicados
    pagos = Pagos.objects.filter(
        prestamo_id_real=prestamo_id,
        fecha_pago__lte=fecha_corte,
        estado_pago='aplicado'
    )
    for pago in pagos:
        fechas_eventos.add(pago.fecha_pago)
    
    # Si no hay eventos, al menos agregar la fecha_corte
    if not fechas_eventos:
        fechas_eventos.add(fecha_corte)
    
    # Ordenar fechas
    fechas_ordenadas = sorted(fechas_eventos)
    
    # Cerrar cada período faltante
    for fecha in fechas_ordenadas:
        # Verificar si ya existe registro para esta fecha
        if Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            fecha_proceso=fecha,
            concepto_id=concepto_causacion
        ).exists():
            continue
        
        # === Reutilizar la lógica de tu función original ===
        try:
            valor_desembolso = prestamo.prestamo_id.valor
        except (AttributeError, TypeError):
            valor_desembolso = Decimal('0')

        abonos_result = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            fecha_efectiva__isnull=False, 
            fecha_efectiva__lte=fecha,
            abono_capital__gt=0
        ).aggregate(total_abonos=Sum('abono_capital'))
        
        total_abonos = abonos_result['total_abonos'] or Decimal('0')
        saldo_capital = valor_desembolso - total_abonos
        if saldo_capital < 0:
            saldo_capital = Decimal('0')

        ultimo_registro = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            fecha_proceso__lt=fecha
        ).order_by('-fecha_proceso').first()
        
        intereses_acumulados = ultimo_registro.intrs_ctes or Decimal('0') if ultimo_registro else Decimal('0')

        tasa_diaria = prestamo.tasa / Decimal('100') / Decimal('360')
        interes_diario = saldo_capital * tasa_diaria if saldo_capital > 0 else Decimal('0')
        nuevos_intereses = intereses_acumulados + interes_diario

        Historia_Prestamos.objects.create(
            prestamo_id=prestamo,
            fecha_proceso=fecha,
            fecha_efectiva=None,
            concepto_id=concepto_causacion,
            monto_transaccion=interes_diario,
            intrs_ctes=nuevos_intereses,
            abono_capital=Decimal('0'),
            seguro=Decimal('0'),
            fee=Decimal('0'),
            tasa=prestamo.tasa,
            fecha_vencimiento=fecha,
            estado='TRANSACCION',
            usuario='sistema',
            numero_cuota=None,
            ordinal_interno=10,
            numero_operacion=1
        )
#_______________________________________________________
def obtener_tasa_prestamo(prestamo_id):
    """
    Obtiene la tasa anual del préstamo (como Decimal).
    La tasa se almacena en el campo 'tasa' del modelo Prestamos.
    
    Parámetros:
        prestamo_id: ID del préstamo (coincide con el ID del desembolso)
    
    Retorna:
        Decimal: tasa anual en formato decimal (ej: 0.25 para 25%)
    """
    try:
        prestamo = Prestamos.objects.get(prestamo_id=prestamo_id)
        # Asegurarse de que sea Decimal y no float
        return Decimal(str(prestamo.tasa))
    except Prestamos.DoesNotExist:
        raise ValueError(f"Préstamo con ID {prestamo_id} no encontrado.")
# En cualquier parte de tu código
#tasa = obtener_tasa_prestamo(38)  # préstamo ID 38
#print(tasa)  # Ej: Decimal('0.2500') si la tasa es 25%
#------------------------------------------------------------------------

# utils.py
# utils.py - Actualiza SOLO las funciones de consulta

def obtener_intereses_causados_a_fecha(prestamo_id, fecha_corte):
    """Calcula intereses causados hasta fecha_corte RECALCULANDO desde cero."""
    from decimal import Decimal
    from .models import Prestamos, Historia_Prestamos, Conceptos_Transacciones
    
    # ✅ Usar la NUEVA función para consultas
    cerrar_todos_periodos_hasta(prestamo_id, fecha_corte)
    
    concepto_causacion = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
    ultimo_registro = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        concepto_id=concepto_causacion,
        fecha_proceso__lte=fecha_corte
    ).order_by('-fecha_proceso').first()
    
    return ultimo_registro.intrs_ctes if ultimo_registro else Decimal('0.00')

#_____________________________________________
# utils.py
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta, date
from django.db.models import Sum
from .models import Historia_Prestamos, Conceptos_Transacciones, Prestamos, Fechas_Sistema


def total_intereses_por_periodo(fecha_inicio, fecha_fin):
    """
    Calcula intereses causados y ajustes por periodo.
    - interes_causado: solo intereses normales.
    - ajuste_intrs_causacion: suma de ajustes (AJUINT) en el periodo.
    """
    # === Validaciones y ajuste de fecha_fin ===
    if fecha_inicio < date(2020, 12, 31):
        raise ValueError("La fecha de inicio no puede ser anterior al 2020-12-31.")
    
    fechas_sistema = Fechas_Sistema.objects.first()
    if not fechas_sistema:
        raise ValueError("No se encontró la configuración de fechas del sistema.")
    fecha_proceso_actual = fechas_sistema.fecha_proceso_actual

    if fecha_fin > fecha_proceso_actual:
        raise ValueError(f"La fecha de fin no puede ser posterior a la fecha de proceso del sistema ({fecha_proceso_actual}).")

    if fecha_fin == fecha_proceso_actual:
        fecha_fin = fecha_proceso_actual - timedelta(days=1)
        if fecha_fin < fecha_inicio:
            return {
                'total_intereses': 0.0,
                'total_ajustes': 0.0,
                'detalle_por_prestamo': {}
            }

    # === Configuración de conceptos ===
    concepto_des = Conceptos_Transacciones.objects.get(concepto_id="DES")
    concepto_causac = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
    concepto_ajuint = Conceptos_Transacciones.objects.get(concepto_id="AJUINT")

    prestamos_activos = Prestamos.objects.filter(revocatoria='NO')
    total_intereses_general = Decimal('0.00')
    total_ajustes_general = Decimal('0.00')
    detalle_por_prestamo = {}

    for prestamo in prestamos_activos:
        # --- Desembolsos ---
        desembolsos = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo,
            concepto_id=concepto_des,
            fecha_efectiva__isnull=False,
            fecha_efectiva__lte=fecha_fin
        )
        total_desembolsado = sum((d.monto_transaccion for d in desembolsos), Decimal('0.00'))
        if total_desembolsado <= 0:
            continue

        primer_desembolso = desembolsos.order_by('fecha_efectiva').first()
        if not primer_desembolso:
            continue
        fecha_inicio_prestamo = primer_desembolso.fecha_efectiva
        if fecha_inicio_prestamo > fecha_fin:
            continue

        # --- Eventos CAUSAC y AJUINT ---
        eventos_causac_ajuint = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo,
            concepto_id__in=[concepto_causac, concepto_ajuint],
            fecha_proceso__lte= fecha_fin
        ).order_by('fecha_proceso', 'ordinal_interno', 'id')

        eventos = []
        for ev in eventos_causac_ajuint:
            eventos.append({
                'fecha': ev.fecha_proceso,
                'tipo': 'CAUSAC' if ev.concepto_id == concepto_causac else 'AJUINT',
                'capital_aplicado': ev.capital_aplicado_periodo if ev.concepto_id == concepto_causac else Decimal('0.00'),
                'monto_transaccion': ev.monto_transaccion,
                'tasa': ev.tasa
            })
        eventos.sort(key=lambda x: x['fecha'])

        # --- Inicialización ---
        saldo = total_desembolsado
        tasa = prestamo.tasa
        periodos = []
        total_intereses_prestamo = Decimal('0.00')
        total_ajustes_prestamo = Decimal('0.00')

        # --- Eventos antes de fecha_inicio ---
        for ev in eventos:
            if ev['fecha'] < fecha_inicio:
                if ev['tipo'] == 'CAUSAC':
                    saldo -= ev['capital_aplicado']
                    tasa = ev['tasa']
            else:
                break

        # --- Procesar rango ---
        fecha_actual = max(fecha_inicio, fecha_inicio_prestamo)
        eventos_en_rango = [ev for ev in eventos if fecha_inicio <= ev['fecha'] <= fecha_fin]

        for ev in eventos_en_rango:
            fecha_evento = ev['fecha']

            # Periodo normal (interés diario)
            if fecha_actual <= fecha_evento - timedelta(days=1):
                periodo_fin = fecha_evento - timedelta(days=1)
                dias = (periodo_fin - fecha_actual).days + 1
                interes_diario = (saldo * tasa / Decimal('100')) / Decimal('360')
                interes = (interes_diario * dias).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                periodos.append({
                    'periodo_inicio': fecha_actual,
                    'periodo_fin': periodo_fin,
                    'dias': dias,
                    'saldo_inicial': float(saldo),
                    'tasa': float(tasa),
                    'interes_causado': float(interes),
                    'ajuste_intrs_causacion': 0.0,
                    'tipo_evento': 'CAUSACION'
                })
                total_intereses_prestamo += interes
                total_intereses_general += interes

            # Evento en la fecha exacta
            if ev['tipo'] == 'CAUSAC':
                saldo -= ev['capital_aplicado']
                tasa = ev['tasa']
            elif ev['tipo'] == 'AJUINT':
                # Registrar ajuste como periodo de 1 día
                periodos.append({
                    'periodo_inicio': fecha_evento,
                    'periodo_fin': fecha_evento,
                    'dias': 1,
                    'saldo_inicial': float(saldo),
                    'tasa': float(tasa),
                    'interes_causado': 0.0,
                    'ajuste_intrs_causacion': float(ev['monto_transaccion']),
                    'tipo_evento': 'AJUSTE'
                })
                total_ajustes_prestamo += ev['monto_transaccion']
                total_ajustes_general += ev['monto_transaccion']

            fecha_actual = fecha_evento + timedelta(days=1)

        # --- Periodo final ---
        if fecha_actual <= fecha_fin:
            dias = (fecha_fin - fecha_actual).days + 1
            interes_diario = (saldo * tasa / Decimal('100')) / Decimal('360')
            interes = (interes_diario * dias).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            periodos.append({
                'periodo_inicio': fecha_actual,
                'periodo_fin': fecha_fin,
                'dias': dias,
                'saldo_inicial': float(saldo),
                'tasa': float(tasa),
                'interes_causado': float(interes),
                'ajuste_intrs_causacion': 0.0,
                'tipo_evento': 'CAUSACION'
            })
            total_intereses_prestamo += interes
            total_intereses_general += interes

        if periodos:
            detalle_por_prestamo[prestamo.prestamo_id] = periodos

    return {
        'total_intereses': float(total_intereses_general),
        'total_ajustes': float(total_ajustes_general),
        'detalle_por_prestamo': detalle_por_prestamo
    }

#___________________________________________________________________________
#------------------------------------------------------------------------
def aplicar_pago_cuota_inicial(desembolso, prestamo, usuario: str,  numero_asiento_contable=None):
    """
    Aplica el pago de la cuota #1 dentro del contexto de procesar_desembolsos_pendientes.
    Usa los campos numero_transaccion_cuota_1 y valor_cuota_1 del desembolso.
    Debe ejecutarse dentro de un bloque transaction.atomic() externo.
    """
    from decimal import Decimal, ROUND_HALF_UP
    from .models import Pagos, Fechas_Sistema, Conceptos_Transacciones, Historia_Prestamos, Detalle_Aplicacion_Pago
    from django.utils import timezone
    from django.db.models import Max

    # Validar campos obligatorios en desembolso
    if not desembolso.numero_transaccion_cuota_1:
        raise ValueError(f"Desembolso {desembolso.prestamo_id}: falta numero_transaccion_cuota_1")
    if desembolso.valor_cuota_1 is None:
        raise ValueError(f"Desembolso {desembolso.prestamo_id}: falta valor_cuota_1")

    pago_id = desembolso.numero_transaccion_cuota_1
    valor_esperado = Decimal(str(desembolso.valor_cuota_1)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Obtener el pago desde Pagos
    try:
        pago = Pagos.objects.select_for_update().get(ref_bancaria=pago_id)
    except Pagos.DoesNotExist:
        raise ValueError(f"El pago con ID {pago_id} vs {desembolso.numero_transaccion_cuota_1} (cuota inicial) no existe en la tabla Pagos.")

    # Validaciones de coherencia
    valor_pago = Decimal(str(pago.valor_pago)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if valor_pago != valor_esperado:
        raise ValueError(
            f"Inconsistencia en valor de cuota inicial. "
            f"Desembolso: {valor_esperado}, Pagos: {valor_pago}."
        )
    if pago.prestamo_id_real != desembolso.prestamo_id:
        raise ValueError(
            f"El pago {pago_id} no pertenece al préstamo {desembolso.prestamo_id}."
        )
    if pago.fecha_pago != desembolso.fecha_desembolso:
        raise ValueError(
            f"Fecha de pago ({pago.fecha_pago}) != fecha de desembolso ({desembolso.fecha_desembolso})."
        )

    # Si ya fue aplicado, omitir o fallar
    if pago.estado_pago == 'aplicado':
        raise ValueError(f"El pago de cuota inicial {pago_id} ya fue aplicado.")

    # Obtener fecha de proceso del sistema
    # Obtener fecha de proceso del sistema
    fechas_sistema = Fechas_Sistema.objects.first()
    if not fechas_sistema:
        raise ValueError("No se encontró ningún registro en Fechas_Sistema. Cree uno primero.")
    fecha_proceso_actual = fechas_sistema.fecha_proceso_actual

    # --- A partir de aquí, reutilizamos lógica de aplicar_pago (sin transacción) ---  ###################
    prestamo_id = pago.prestamo_id_real
    #monto_restante = valor_pago
    monto_restante = Decimal(str(pago.valor_pago)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


    # Conceptos
    concepto_cap = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
    concepto_int = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
    concepto_seg = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
    concepto_gto = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
    concepto_excedente = Conceptos_Transacciones.objects.get(concepto_id="PAGOEXC")

    # Registros pendientes
    registros_pendientes = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        concepto_id__in=[concepto_cap, concepto_int, concepto_seg, concepto_gto],
        estado="PENDIENTE"
    ).order_by('fecha_vencimiento', 'numero_cuota')

    prioridad = {concepto_cap.concepto_id: 1, concepto_int.concepto_id: 2, concepto_seg.concepto_id: 3, concepto_gto.concepto_id: 4}
    registros_pendientes = sorted(
        registros_pendientes,
        key=lambda r: (r.fecha_vencimiento, r.numero_cuota, prioridad.get(r.concepto_id_id, 99))
    )


    # Número de operación único
    ultimo_numero = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_proceso=fecha_proceso_actual
    ).aggregate(Max('numero_operacion'))['numero_operacion__max'] or 0
	
    numero_siguiente = ultimo_numero + 1

    # Acumulador específico para CAPITAL aplicado (solo PLANCAP)
    total_capital_aplicado = Decimal('0.00')


    # Aplicar pago a cada componente
    registros_creados = []

    for reg in registros_pendientes:
        if monto_restante <= 0:
            break

        if reg.concepto_id_id == concepto_cap.concepto_id:
            pagado = reg.abono_capital; campo_pago = 'abono_capital'; comp_nombre = 'CAPITAL'
        elif reg.concepto_id_id == concepto_int.concepto_id:
            pagado = reg.intrs_ctes; campo_pago = 'intrs_ctes'; comp_nombre = 'INTERES'
        elif reg.concepto_id_id == concepto_seg.concepto_id:
            pagado = reg.seguro; campo_pago = 'seguro'; comp_nombre = 'SEGURO'
        elif reg.concepto_id_id == concepto_gto.concepto_id:
            pagado = reg.fee; campo_pago = 'fee'; comp_nombre = 'GASTOS'
        else:
            continue

        saldo_pendiente = reg.monto_transaccion - pagado
        if saldo_pendiente <= 0:
            continue

        aplicado = min(monto_restante, saldo_pendiente)
        monto_restante -= aplicado

        setattr(reg, campo_pago, getattr(reg, campo_pago) + aplicado)
        if getattr(reg, campo_pago) >= reg.monto_transaccion:
            reg.estado = "PAGADA"
        if reg.fecha_efectiva is None:
            reg.fecha_efectiva = pago.fecha_pago
        reg.fecha_proceso = fecha_proceso_actual
        reg.usuario = usuario
        reg.numero_operacion = numero_siguiente
        reg.numero_asiento_contable = numero_asiento_contable
        reg.save()


        Detalle_Aplicacion_Pago.objects.create(
            pago=pago,
            historia_prestamo=reg,
            monto_aplicado=aplicado,
            componente=comp_nombre
        )
        numero_siguiente += 1

    # === Manejo de excedente ===
    if monto_restante > 0:
        siguiente_capital = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            concepto_id=concepto_cap,
            estado="PENDIENTE"
        ).order_by('fecha_vencimiento', 'numero_cuota').first()

        if siguiente_capital:
            monto_aplicar = min(monto_restante, siguiente_capital.monto_transaccion)
            siguiente_capital.abono_capital += monto_aplicar
            if siguiente_capital.abono_capital >= siguiente_capital.monto_transaccion:
                siguiente_capital.estado = "PAGADA"
            siguiente_capital.fecha_efectiva = pago.fecha_pago
            siguiente_capital.usuario = usuario
            siguiente_capital.fecha_proceso = fecha_proceso_actual
            siguiente_capital.numero_asiento_contable = numero_asiento_contable or 0
            siguiente_capital.save()

            registros_creados.append(siguiente_capital)

            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,
                historia_prestamo=siguiente_capital,
                monto_aplicado=monto_aplicar,
                componente='CAPITAL'
            )
            monto_restante -= monto_aplicar
            total_capital_aplicado += monto_aplicar  # ✅ ¡Incluir excedente aplicado a capital!

			 
        if monto_restante > 0:					  
            hist_excedente = Historia_Prestamos.objects.create(
                prestamo_id=prestamo_id,
                concepto_id=concepto_excedente,								   
                fecha_efectiva=pago.fecha_pago,							   
                fecha_proceso=fecha_proceso_actual,		   
                fecha_vencimiento=pago.fecha_pago,
                monto_transaccion=monto_restante,
                abono_capital=monto_restante,
                estado="TRANSACCION",
                numero_cuota=0,
                usuario=usuario,
                numero_operacion=pago.pago_id,
                ordinal_interno=20,												
                numero_asiento_contable=numero_asiento_contable or 0
            )
            registros_creados.append(hist_excedente)
				
            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,
                historia_prestamo=hist_excedente,
                monto_aplicado=monto_restante,
                componente='EXCEDENTE'
            )

    # === ✅ AHORA: Cerrar período de interés UNA SOLA VEZ, con el total de capital aplicado ===
    from .utils import cerrar_periodo_interes
    cerrar_periodo_interes(
        prestamo_id,
        pago.fecha_pago,
        pago_referencia=f"PAGO_{pago.pago_id}",
        numero_asiento_contable=numero_asiento_contable,
        capital_aplicado=total_capital_aplicado  # ✅ PASAR EL TOTAL ACUMULADO
    )


    # Finalizar pago
    pago.estado_pago = 'aplicado'
    pago.fecha_aplicacion_pago = timezone.now()
    pago.save()

    return {
        'status': 'success',
        'message': f'Pago {pago_id} aplicado exitosamente.',
        'pago_id': pago_id,
        'monto_aplicado': float(pago.valor_pago - (monto_restante)),
        'excedente': float(monto_restante),
    }


 #------------------------------------------------------------------------
# utils.py

def aplicar_pago(pago_id, usuario, asiento=None):
    """
    Aplica un pago conciliado a las cuotas pendientes del préstamo.
    - Usa siempre pago.fecha_pago como fecha de aplicación.
    - Si pago.fecha_pago < fecha_proceso_actual del sistema, se considera retroactivo
      y se genera un ajuste contable al final.
    - Cierra el período de intereses hasta la fecha del pago.
    - Crea registros en Historia_Prestamos y Detalle_Aplicacion_Pago.
    - Protege contra re-aplicación.
    - Debe ejecutarse dentro de transaction.atomic().
    """
    from decimal import Decimal, ROUND_HALF_UP
    from django.utils import timezone
    from django.db.models import Max
    from .models import (
        Pagos, Fechas_Sistema, Conceptos_Transacciones,
        Historia_Prestamos, Detalle_Aplicacion_Pago, Prestamos
    )

    # === FASE 0: Obtener pago y verificar estado ===
    pago = Pagos.objects.select_for_update().get(pago_id=pago_id)

    if pago.estado_pago == 'aplicado':
        registros_existentes = Historia_Prestamos.objects.filter(
            prestamo_id=pago.prestamo_id_real,
            fecha_proceso=pago.fecha_pago,
            numero_operacion=pago.pago_id
        ).exists()
        if registros_existentes:
            return {
                'status': 'success',
                'message': f'Pago {pago_id} ya fue aplicado anteriormente.',
                'pago_id': pago_id,
            }
        else:
            raise ValueError("El pago ya fue marcado como aplicado pero no hay registros en Historia_Prestamos.")

    if pago.estado_pago != 'conciliado':
        raise ValueError("El pago no está conciliado.")
    if pago.prestamo_id_real is None:
        raise ValueError("El pago no tiene un préstamo real asignado.")

    # === FASE 1: Obtener fechas del sistema ===
    fechas_sistema = Fechas_Sistema.objects.first()
    if not fechas_sistema:
        fechas_sistema = Fechas_Sistema.objects.order_by('-fecha_proceso_actual').first()
    if not fechas_sistema:
        raise ValueError("No se encontró una fecha de proceso del sistema válida.")
    fecha_proceso_sistema = fechas_sistema.fecha_proceso_actual

    # Usamos directamente la fecha del pago
    fecha_aplicacion = pago.fecha_pago
    prestamo_id = pago.prestamo_id_real

    # Validar que la fecha del pago no sea posterior al sistema (no permitir "futuro")
    if fecha_aplicacion > fecha_proceso_sistema:
        raise ValueError("La fecha del pago no puede ser posterior a la fecha de proceso actual del sistema.")

    # Validar que no sea anterior al desembolso
    prestamo = Prestamos.objects.get(prestamo_id=prestamo_id)
    if fecha_aplicacion < prestamo.fecha_desembolso:
        raise ValueError("La fecha del pago no puede ser anterior a la fecha de desembolso del préstamo.")

    # Determinar si es retroactivo
    es_retroactivo = fecha_aplicacion < fecha_proceso_sistema

    # === FASE 2: Aplicar el pago usando pago.fecha_pago como base ===
    monto_restante = Decimal(str(pago.valor_pago)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Conceptos
    concepto_cap = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
    concepto_int = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
    concepto_seg = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
    concepto_gto = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
    concepto_excedente = Conceptos_Transacciones.objects.get(concepto_id="PAGOEXC")

    # Registros pendientes con vencimiento <= fecha del pago
    registros_pendientes = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        concepto_id__in=[concepto_cap, concepto_int, concepto_seg, concepto_gto],
        estado="PENDIENTE",
        fecha_vencimiento__lte=fecha_aplicacion
    ).order_by('fecha_vencimiento', 'numero_cuota')

    prioridad = {
        concepto_cap.concepto_id: 1,
        concepto_int.concepto_id: 2,
        concepto_seg.concepto_id: 3,
        concepto_gto.concepto_id: 4,
    }
    registros_pendientes = sorted(
        registros_pendientes,
        key=lambda r: (r.fecha_vencimiento, r.numero_cuota, prioridad.get(r.concepto_id_id, 99))
    )

    # Número de operación único basado en la fecha de aplicación (pago.fecha_pago)
    ultimo_numero = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_proceso=fecha_aplicacion
    ).aggregate(Max('numero_operacion'))['numero_operacion__max'] or 0
    numero_siguiente = ultimo_numero + 1

    total_capital_aplicado = Decimal('0.00')
    registros_creados = []

    # Aplicar pago a cada componente
    for reg in registros_pendientes:
        if monto_restante <= 0:
            break

        if reg.concepto_id_id == concepto_cap.concepto_id:
            pagado = reg.abono_capital
            campo_pago = 'abono_capital'
            comp_nombre = 'CAPITAL'
        elif reg.concepto_id_id == concepto_int.concepto_id:
            pagado = reg.intrs_ctes
            campo_pago = 'intrs_ctes'
            comp_nombre = 'INTERES'
        elif reg.concepto_id_id == concepto_seg.concepto_id:
            pagado = reg.seguro
            campo_pago = 'seguro'
            comp_nombre = 'SEGURO'
        elif reg.concepto_id_id == concepto_gto.concepto_id:
            pagado = reg.fee
            campo_pago = 'fee'
            comp_nombre = 'GASTOS'
        else:
            continue

        saldo_pendiente = reg.monto_transaccion - pagado
        if saldo_pendiente <= 0:
            continue

        aplicado = min(monto_restante, saldo_pendiente)
        monto_restante -= aplicado

        # Actualizar registro
        setattr(reg, campo_pago, getattr(reg, campo_pago) + aplicado)
        if getattr(reg, campo_pago) >= reg.monto_transaccion:
            reg.estado = "PAGADA"
        if reg.fecha_efectiva is None:
            reg.fecha_efectiva = fecha_aplicacion
        reg.fecha_proceso = fecha_aplicacion
        reg.usuario = usuario
        reg.numero_operacion = numero_siguiente
        reg.ordinal_interno = 20
        reg.numero_asiento_contable = asiento or 0
        reg.save()

        registros_creados.append(reg)

        # Acumular por componente
        if comp_nombre == 'CAPITAL':
            total_capital_aplicado += aplicado


        Detalle_Aplicacion_Pago.objects.create(
            pago=pago,
            historia_prestamo=reg,
            monto_aplicado=aplicado,
            componente=comp_nombre
        )

        numero_siguiente += 1

    # === Manejo de excedente ===
    if monto_restante > 0:
        # Solo aplicar a cuotas con vencimiento >= fecha del pago
        siguiente_capital = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            concepto_id=concepto_cap,
            estado="PENDIENTE",
            fecha_vencimiento__gte=fecha_aplicacion
        ).order_by('fecha_vencimiento', 'numero_cuota').first()

        if siguiente_capital:
            monto_aplicar = min(monto_restante, siguiente_capital.monto_transaccion)
            siguiente_capital.abono_capital += monto_aplicar
            if siguiente_capital.abono_capital >= siguiente_capital.monto_transaccion:
                siguiente_capital.estado = "PAGADA"
            siguiente_capital.fecha_efectiva = fecha_aplicacion
            siguiente_capital.usuario = usuario
            siguiente_capital.fecha_proceso = fecha_aplicacion
            siguiente_capital.numero_asiento_contable = asiento or 0
            siguiente_capital.save()

            registros_creados.append(siguiente_capital)

            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,
                historia_prestamo=siguiente_capital,
                monto_aplicado=monto_aplicar,
                componente='CAPITAL'
            )
            monto_restante -= monto_aplicar
            total_capital_aplicado += monto_aplicar

        if monto_restante > 0:
            hist_excedente = Historia_Prestamos.objects.create(
                prestamo_id=prestamo_id,
                concepto_id=concepto_excedente,
                fecha_efectiva=fecha_aplicacion,
                fecha_proceso=fecha_aplicacion,
                fecha_vencimiento=fecha_aplicacion,
                monto_transaccion=monto_restante,
                abono_capital=monto_restante,
                estado="TRANSACCION",
                numero_cuota=0,
                usuario=usuario,
                numero_operacion=pago.pago_id,
                ordinal_interno=20,
                numero_asiento_contable=asiento or 0
            )
            registros_creados.append(hist_excedente)

            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,
                historia_prestamo=hist_excedente,
                monto_aplicado=monto_restante,
                componente='EXCEDENTE'
            )

    # === FASE 3: Cerrar período de interés hasta la fecha del pago ===
    from .utils import cerrar_periodo_interes
    cerrar_periodo_interes(
        prestamo_id,
        fecha_aplicacion,
        pago_referencia=f"PAGO_{pago.pago_id}",
        numero_asiento_contable=asiento,
        capital_aplicado=total_capital_aplicado
    )

    # === FASE 4: Marcar pago como aplicado ===
    pago.estado_pago = 'aplicado'
    pago.fecha_aplicacion_pago = timezone.now()
    pago.save()

    # === FASE 5: Crear ajuste retroactivo si aplica ===
    ajuste_id = None
    if es_retroactivo:
        from .utils import crear_ajuste_retroactivo
        ajuste = crear_ajuste_retroactivo(
            prestamo_id,
            fecha_aplicacion,
            fecha_proceso_sistema
        )
        ajuste_id = ajuste.id

    return {
        'status': 'success',
        'message': f'Pago {pago_id} aplicado exitosamente.' + (
            ' (ajuste retroactivo generado)' if es_retroactivo else ''
        ),
        'pago_id': pago_id,
        'monto_aplicado': float(pago.valor_pago - monto_restante),
        'excedente': float(monto_restante),
        'ajuste_id': ajuste_id
    } 
#--------------- Fin aplicar pago ------------

#

#----------------------------------------------------------------2025/11/26
# appfinancia/utils.py
#from .models import Fechas_Sistema
from django.utils import timezone
from datetime import date

def get_fecha_proceso_actual() -> date:
    """Devuelve la fecha de proceso actual (singleton seguro)"""
    from .models import Fechas_Sistema
    return Fechas_Sistema.load().fecha_proceso_actual

def get_fecha_proceso_anterior() -> date:
    from .models import Fechas_Sistema
    return Fechas_Sistema.load().fecha_proceso_anterior

def get_fecha_proximo_proceso() -> date:
    from .models import Fechas_Sistema
    return Fechas_Sistema.load().fecha_proximo_proceso

def get_estado_sistema() -> str:
    from .models import Fechas_Sistema
    return Fechas_Sistema.load().estado_sistema

def get_modo_fecha_sistema() -> str:
    from .models import Fechas_Sistema
    return Fechas_Sistema.load().modo_fecha_sistema

def sistema_esta_abierto() -> bool:
    #from .models import Fechas_Sistema
    return get_estado_sistema() == 'ABIERTO'

def fecha_proceso_es_hoy() -> bool:
    from .models import Fechas_Sistema
    return get_fecha_proceso_actual() == timezone.now().date()
    
if sistema_esta_abierto():
    hoy = get_fecha_proceso_actual()    
    

#------------ ***   para el Historial del prestamo a xls ******
# appfinancia/utils.py

# --- utils.py (AJUSTADO SIN MERGE) ---
import io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.cell.cell import MergedCell 
from decimal import Decimal
from django.db.models import Sum # Necesario para la agregación
from .models import (
    Historia_Prestamos, Detalle_Aplicacion_Pago, Fechas_Sistema, 
    Desembolsos, Prestamos, Clientes
)

def generar_reporte_excel_en_memoria(prestamo_id):
    """
    Genera un reporte Excel del historial de un préstamo y devuelve un BytesIO buffer.
    Implementa chequeos de MergedCell y salta la fila de Desembolso en el formato numérico.
    """
    # Obtener fecha de corte
    fecha_sistema = Fechas_Sistema.objects.first()
    if not fecha_sistema:
        raise Exception("No hay registro en Fechas_Sistema.")
    fecha_corte = fecha_sistema.fecha_proceso_actual

    # === Obtener información del préstamo y cliente ===
    prestamo = Prestamos.objects.select_related('cliente_id').get(prestamo_id=prestamo_id)
    cliente = prestamo.cliente_id
    nombre_completo = f"{cliente.nombre} {cliente.apellido}" if cliente else "Cliente no encontrado"

    # === Obtener desembolso ===
    try:
        desembolso = Desembolsos.objects.get(prestamo_id=prestamo_id)
        monto_desembolso = float(desembolso.valor)
        fecha_desembolso = desembolso.fecha_desembolso
        tasa_desembolso = float(prestamo.tasa)
    except Desembolsos.DoesNotExist:
        monto_desembolso = 0.0
        fecha_desembolso = "No encontrado"
        tasa_desembolso = 0.0

    # === Contar cuotas pagadas y pendientes ===
    cuotas_vencimiento = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_vencimiento__lte=fecha_corte
    ).exclude(concepto_id__concepto_id="CAUSAC").values_list('fecha_vencimiento', flat=True).distinct()

    cuotas_pagadas = 0
    cuotas_pendientes = 0
    
    for fecha_venc in cuotas_vencimiento:
        componentes_cuota = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo_id,
            fecha_vencimiento=fecha_venc,
            fecha_vencimiento__lte=fecha_corte
        ).exclude(concepto_id__concepto_id="CAUSAC")
        
        total_monto = componentes_cuota.aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0')
        total_pagado = 0
        
        for comp in componentes_cuota:
            detalles = Detalle_Aplicacion_Pago.objects.filter(historia_prestamo=comp)
            total_pagado += sum(d.monto_aplicado for d in detalles)
        
        if total_pagado >= total_monto - Decimal('0.01'):
            cuotas_pagadas += 1
        else:
            cuotas_pendientes += 1

    # === Agrupar cuotas ===
    from collections import defaultdict
    cuotas = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_vencimiento__lte=fecha_corte
    ).exclude(concepto_id__concepto_id="CAUSAC").order_by('fecha_vencimiento', 'numero_cuota')

    cuotas_agrupadas = defaultdict(lambda: {
        'registro': None, 'capital_prog': Decimal('0'), 'interes_prog': Decimal('0'), 
        'seguro_prog': Decimal('0'), 'fee_prog': Decimal('0'), 'capital_pag': Decimal('0'), 
        'interes_pag': Decimal('0'), 'seguro_pag': Decimal('0'), 'fee_pag': Decimal('0'), 
        'fecha_efectiva': None, 'fecha_proceso': None, 'fecha_vencimiento': None, 
        'tasa': Decimal('0'), 'fecha_pago': None, 'ref_bancaria': set(), 'estado': 'PENDIENTE'
    })

    concepto_a_tipo = {'PLANCAP': 'capital', 'PLANINT': 'interes', 'PLANSEG': 'seguro', 'PLANGTO': 'fee'}
    
    for reg in cuotas:
        num_cuota = reg.numero_cuota or 0
        tipo = concepto_a_tipo.get(reg.concepto_id.concepto_id)
        if tipo:
            if cuotas_agrupadas[num_cuota]['registro'] is None:
                cuotas_agrupadas[num_cuota]['registro'] = reg
                cuotas_agrupadas[num_cuota]['fecha_efectiva'] = reg.fecha_efectiva
                cuotas_agrupadas[num_cuota]['fecha_proceso'] = reg.fecha_proceso
                cuotas_agrupadas[num_cuota]['fecha_vencimiento'] = reg.fecha_vencimiento
                cuotas_agrupadas[num_cuota]['tasa'] = reg.tasa

            cuotas_agrupadas[num_cuota][f'{tipo}_prog'] += reg.monto_transaccion

            detalles = Detalle_Aplicacion_Pago.objects.filter(historia_prestamo=reg)
            total_pagado = sum(d.monto_aplicado for d in detalles)
            cuotas_agrupadas[num_cuota][f'{tipo}_pag'] += total_pagado

            if detalles.exists():
                fecha_pago_max = max(d.fecha_aplicacion.date() for d in detalles)
                if cuotas_agrupadas[num_cuota]['fecha_pago'] is None or fecha_pago_max > cuotas_agrupadas[num_cuota]['fecha_pago']:
                    cuotas_agrupadas[num_cuota]['fecha_pago'] = fecha_pago_max
                refs = {d.pago.ref_bancaria for d in detalles if d.pago.ref_bancaria}
                cuotas_agrupadas[num_cuota]['ref_bancaria'].update(refs)

            if total_pagado < reg.monto_transaccion:
                cuotas_agrupadas[num_cuota]['estado'] = 'PENDIENTE'
            else:
                cuotas_agrupadas[num_cuota]['estado'] = 'PAGADA'

    # === Preparar datos ===
    datos_excel = []
    # Fila 5: Datos de desembolso
    datos_excel.append([
        "Desembolso", "", fecha_desembolso, "", "", "", "", monto_desembolso, "", "", "", "", monto_desembolso, 0, "DESEMBOLSADO", "", "N/A", tasa_desembolso, "", ""
    ])

    total_pendiente_general = Decimal('0')
    for num_cuota in sorted(cuotas_agrupadas.keys()):
        c = cuotas_agrupadas[num_cuota]
        total_prog = c['capital_prog'] + c['interes_prog'] + c['seguro_prog'] + c['fee_prog']
        total_pag = c['capital_pag'] + c['interes_pag'] + c['seguro_pag'] + c['fee_pag']
        total_pend = total_prog - total_pag
        total_pendiente_general += total_pend
        estado_final = "PAGADA" if total_pend <= Decimal('0.01') else c['estado']

        datos_excel.append([
            "Cuota", num_cuota, 
            c['fecha_efectiva'] or c['registro'].fecha_vencimiento if c['registro'] else '',
            float(c['capital_prog']), float(c['interes_prog']), float(c['seguro_prog']), float(c['fee_prog']), float(total_prog),
            float(c['capital_pag']), float(c['interes_pag']), float(c['seguro_pag']), float(c['fee_pag']), float(total_pag), float(total_pend),
            estado_final, 
            c['fecha_pago'] or '',
            "; ".join(c['ref_bancaria']) if c['ref_bancaria'] else "N/A",
            float(c['tasa']) if c['tasa'] else 0.0,
            c['fecha_proceso'] or '',
            c['fecha_vencimiento'] or ''
        ])

    # === Crear Excel ===
    wb = Workbook()
    ws = wb.active
    ws.title = f"Préstamo {prestamo_id}"

    # TÍTULOS SIN MERGE (Fila 1 y 2)
    ws['A1'] = f"REPORTE HISTORIAL PRÉSTAMO {prestamo_id} - {nombre_completo}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal='left')

    ws['A2'] = f"Cuotas Pagadas: {cuotas_pagadas} | Cuotas Pendientes: {cuotas_pendientes}"
    ws['A2'].font = Font(bold=True, size=12)
    ws['A2'].alignment = Alignment(horizontal='left')

    # Encabezados de columnas (Fila 4)
    headers = [
        "Tipo", "Cuota", "Fecha Efectiva",
        "Capital Programado", "Interés Programado", "Seguro Programado", "Fee Programado", "Total Programado",
        "Capital Pagado", "Interés Pagado", "Seguro Pagado", "Fee Pagado", "Valor Transacción", "Total Pendiente",
        "Estado", "Fecha aplicacion pago", "Ref. Bancaria",
        "Tasa", "Fecha proceso", "Fecha Vencimiento"
    ]
    
    # Insertar headers en la fila 4
    for col, header in enumerate(headers, 1):
        ws.cell(row=4, column=col, value=header)
        ws.cell(row=4, column=col).font = Font(bold=True)
        ws.cell(row=4, column=col).fill = PatternFill("solid", fgColor="D9E2F3")

    # Insertar datos a partir de la fila 5
    for fila_datos in datos_excel:
        ws.append(fila_datos)

    # 🛑 Bloque de formato numérico: Empezar en la fila 6 (min_row=6) para saltar el Desembolso (Fila 5)
    
    # Aplicar formato de números (Columnas 4 a 14)
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row, min_col=4, max_col=14):
        for cell in row:
            if not isinstance(cell, MergedCell) and isinstance(cell.value, (int, float, Decimal)):
                cell.number_format = '#,##0.00'

    # Formato para la tasa (columna 18)
    for row in ws.iter_rows(min_row=6, max_row=ws.max_row, min_col=18, max_col=18):
        for cell in row:
            if not isinstance(cell, MergedCell) and isinstance(cell.value, (int, float, Decimal)):
                cell.number_format = '0.0000'

    # Agregar resumen al final
    ws.append([])
    resumen_row = ws.max_row + 1
    ws.cell(row=resumen_row, column=1, value="SALDO TOTAL PENDIENTE:")
    ws.cell(row=resumen_row, column=2, value=float(total_pendiente_general))
    ws.cell(resumen_row, column=2).number_format = '#,##0.00'
    ws.cell(resumen_row, column=1).font = Font(bold=True)
    ws.cell(resumen_row, column=2).font = Font(bold=True, color="FF0000")

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

#------------------- fin historial
def cerrar_periodo_interes_migracion(prestamo_id: int, fecha_corte: date, pago_referencia=None, numero_asiento_contable=None, capital_aplicado=0):
    """
    Cierra el período de interés para un préstamo en una fecha específica. 
    Versión especial para migración que recibe prestamo_id como entero y lo convierte a instancia.
    """
    from decimal import Decimal
    from django.db.models import Sum
    from .models import Conceptos_Transacciones, Prestamos, Historia_Prestamos

    concepto_causacion = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
    prestamo = Prestamos.objects.select_for_update().get(prestamo_id=prestamo_id)

    try:
        valor_desembolso = prestamo.prestamo_id.valor
    except (AttributeError, TypeError):
        valor_desembolso = Decimal('0')

    abonos_result = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_efectiva__isnull=False, 
        fecha_efectiva__lte=fecha_corte,
        abono_capital__gt=0
    ).aggregate(total_abonos=Sum('abono_capital'))
    
    total_abonos = abonos_result['total_abonos'] or Decimal('0')
    saldo_capital = valor_desembolso - total_abonos
    if saldo_capital < 0:
        saldo_capital = Decimal('0')

    ultimo_registro = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo_id,
        fecha_proceso__lt=fecha_corte
    ).order_by('-fecha_proceso').first()
    
    intereses_acumulados = ultimo_registro.intrs_ctes or Decimal('0') if ultimo_registro else Decimal('0')

    tasa_diaria = prestamo.tasa / Decimal('100') / Decimal('360')
    interes_diario = saldo_capital * tasa_diaria if saldo_capital > 0 else Decimal('0')
    nuevos_intereses = intereses_acumulados + interes_diario

    Historia_Prestamos.objects.create(
        prestamo_id=prestamo,
        fecha_proceso=fecha_corte,
        fecha_efectiva=None,
        concepto_id=concepto_causacion,
        monto_transaccion=interes_diario,
        intrs_ctes=nuevos_intereses,
        abono_capital=Decimal('0'),
        seguro=Decimal('0'),
        fee=Decimal('0'),
        tasa=prestamo.tasa,
        fecha_vencimiento=fecha_corte,
        estado='TRANSACCION',
        usuario='sistema',
        numero_cuota=None,
        ordinal_interno=10,
        numero_operacion=numero_asiento_contable,
        capital_aplicado_periodo=capital_aplicado or 0,
        numero_pago_referencia=pago_referencia or "",
        numero_asiento_contable=numero_asiento_contable or 0
    )
#------------- ini aplicar pago migra --------
def aplicar_pago_migracion(pago_id: int, usuario: str = "sistema", asiento=None):
    """
    Aplica un pago conciliado a las cuotas pendientes del préstamo.
    - Diseñado para migración histórica.
    - Usa siempre pago.fecha_pago como fecha de aplicación.
    - No valida que la fecha de pago sea posterior al desembolso (permitido en migración).
    - Cierra el período de intereses hasta la fecha del pago.
    - Crea registros en Historia_Prestamos y Detalle_Aplicacion_Pago.
    - Asigna ordinal_interno único por componente para evitar duplicados.
    - Debe ejecutarse dentro de transaction.atomic().
    """
    from decimal import Decimal, ROUND_HALF_UP
    from django.utils import timezone
    from .models import (
        Pagos, Conceptos_Transacciones,
        Historia_Prestamos, Detalle_Aplicacion_Pago, Prestamos
    )

    # === Obtener pago ===
    pago = Pagos.objects.select_for_update().get(pago_id=pago_id)

    if pago.estado_pago != 'conciliado':
        if pago.estado_pago == 'aplicado':
            return {
                'status': 'success',
                'message': f'Pago {pago_id} ya marcado como aplicado.',
                'pago_id': pago_id,
            }
        else:
            raise ValueError("El pago no está conciliado ni aplicado.")

    if pago.prestamo_id_real is None:
        raise ValueError("El pago no tiene un préstamo real asignado.")

    # === Obtener instancia del préstamo CORRECTAMENTE ===
    try:
        prestamo = Prestamos.objects.select_related('prestamo_id').get(
            prestamo_id__prestamo_id=pago.prestamo_id_real
        )
    except Prestamos.DoesNotExist:
        raise ValueError(f"No existe un préstamo asociado al número de crédito {pago.prestamo_id_real}.")

    fecha_aplicacion = pago.fecha_pago

    # ⚠️ Para migración histórica, permitimos fechas anteriores al desembolso
    if fecha_aplicacion < prestamo.fecha_desembolso:
         fecha_aplicacion = prestamo.fecha_desembolso

    # Determinar si es retroactivo (placeholder; ajustar según lógica real si es necesario)
    es_retroactivo = False  # Simplificado para migración

    # === FASE 2: Aplicar el pago usando pago.fecha_pago como base ===
    monto_restante = Decimal(str(pago.valor_pago)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Conceptos
    concepto_cap = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
    concepto_int = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
    concepto_seg = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
    concepto_gto = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
    concepto_excedente = Conceptos_Transacciones.objects.get(concepto_id="PAGOEXC")

    # Registros pendientes: ✅ Usar INSTANCIA de Prestamos en prestamo_id
    registros_pendientes = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,  # ✅ Correcto: instancia de Prestamos
        concepto_id__in=[concepto_cap, concepto_int, concepto_seg, concepto_gto],
        estado="PENDIENTE",
        fecha_vencimiento__lte=fecha_aplicacion
    ).order_by('fecha_vencimiento', 'numero_cuota')

    prioridad = {
        concepto_cap.concepto_id: 1,
        concepto_int.concepto_id: 2,
        concepto_seg.concepto_id: 3,
        concepto_gto.concepto_id: 4,
    }
    registros_pendientes = sorted(
        registros_pendientes,
        key=lambda r: (r.fecha_vencimiento, r.numero_cuota, prioridad.get(r.concepto_id_id, 99))
    )

    # ✅ numero_operacion como ENTERO
    numero_operacion_base = pago.pago_id

    total_capital_aplicado = Decimal('0.00')
    registros_creados = []
    ordinal_offset = 0  # 🔑 Contador para hacer único el ordinal_interno por componente

    # Aplicar pago a cada componente
    for reg in registros_pendientes:
        if monto_restante <= 0:
            break

        if reg.concepto_id_id == concepto_cap.concepto_id:
            pagado = reg.abono_capital
            campo_pago = 'abono_capital'
            comp_nombre = 'CAPITAL'
        elif reg.concepto_id_id == concepto_int.concepto_id:
            pagado = reg.intrs_ctes
            campo_pago = 'intrs_ctes'
            comp_nombre = 'INTERES'
        elif reg.concepto_id_id == concepto_seg.concepto_id:
            pagado = reg.seguro
            campo_pago = 'seguro'
            comp_nombre = 'SEGURO'
        elif reg.concepto_id_id == concepto_gto.concepto_id:
            pagado = reg.fee
            campo_pago = 'fee'
            comp_nombre = 'GASTOS'
        else:
            continue

        saldo_pendiente = reg.monto_transaccion - pagado
        if saldo_pendiente <= 0:
            continue

        aplicado = min(monto_restante, saldo_pendiente)
        monto_restante -= aplicado

        # Actualizar registro
        setattr(reg, campo_pago, getattr(reg, campo_pago) + aplicado)
        if getattr(reg, campo_pago) >= reg.monto_transaccion:
            reg.estado = "PAGADA"
        if reg.fecha_efectiva is None:
            reg.fecha_efectiva = fecha_aplicacion
        reg.fecha_proceso = fecha_aplicacion
        reg.usuario = usuario
        reg.numero_operacion = numero_operacion_base
        reg.ordinal_interno = 20 + ordinal_offset  # ✅ ÚNICO por componente
        reg.numero_asiento_contable = asiento or 0
        reg.save()

        registros_creados.append(reg)

        if comp_nombre == 'CAPITAL':
            total_capital_aplicado += aplicado

        Detalle_Aplicacion_Pago.objects.create(
            pago=pago,  # ✅ Instancia de Pagos
            historia_prestamo=reg,
            monto_aplicado=aplicado,
            componente=comp_nombre
        )
        
        ordinal_offset += 1  # ✅ Incrementar para el siguiente componente

    # === Manejo de excedente ===
    if monto_restante > 0:
        siguiente_capital = Historia_Prestamos.objects.filter(
            prestamo_id=prestamo,  # ✅ Instancia
            concepto_id=concepto_cap,
            estado="PENDIENTE",
            fecha_vencimiento__gte=fecha_aplicacion
        ).order_by('fecha_vencimiento', 'numero_cuota').first()

        if siguiente_capital:
            monto_aplicar = min(monto_restante, siguiente_capital.monto_transaccion)
            siguiente_capital.abono_capital += monto_aplicar
            if siguiente_capital.abono_capital >= siguiente_capital.monto_transaccion:
                siguiente_capital.estado = "PAGADA"
            siguiente_capital.fecha_efectiva = fecha_aplicacion
            siguiente_capital.usuario = usuario
            siguiente_capital.fecha_proceso = fecha_aplicacion
            siguiente_capital.numero_asiento_contable = asiento or 0
            siguiente_capital.numero_operacion = numero_operacion_base
            siguiente_capital.ordinal_interno = 20 + ordinal_offset  # ✅ Único
            siguiente_capital.save()
            registros_creados.append(siguiente_capital)

            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,  # ✅ Instancia
                historia_prestamo=siguiente_capital,
                monto_aplicado=monto_aplicar,
                componente='CAPITAL'
            )
            monto_restante -= monto_aplicar
            total_capital_aplicado += monto_aplicar
            ordinal_offset += 1  # ✅ Incrementar

        if monto_restante > 0:
            hist_excedente = Historia_Prestamos.objects.create(
                prestamo_id=prestamo,  # ✅ Instancia
                concepto_id=concepto_excedente,
                fecha_efectiva=fecha_aplicacion,
                fecha_proceso=fecha_aplicacion,
                fecha_vencimiento=fecha_aplicacion,
                monto_transaccion=monto_restante,
                abono_capital=monto_restante,
                estado="TRANSACCION",
                numero_cuota=0,
                usuario=usuario,
                numero_operacion=numero_operacion_base,
                ordinal_interno=20 + ordinal_offset,  # ✅ Único
                numero_asiento_contable=asiento or 0
            )
            registros_creados.append(hist_excedente)

            Detalle_Aplicacion_Pago.objects.create(
                pago=pago,  # ✅ Instancia
                historia_prestamo=hist_excedente,
                monto_aplicado=monto_restante,
                componente='EXCEDENTE'
            )

    # === FASE 3: Cerrar período de interés hasta la fecha del pago ===
    from .utils import cerrar_periodo_interes_migracion
    cerrar_periodo_interes_migracion(
        prestamo_id=prestamo.prestamo_id.prestamo_id,  # ID del desembolso (entero)
        fecha_corte=fecha_aplicacion,
        pago_referencia=f"PAGO_{pago.pago_id}",
        numero_asiento_contable=asiento,
        capital_aplicado=total_capital_aplicado
    )

    # === FASE 4: Marcar pago como aplicado ===
    pago.estado_pago = 'aplicado'
    pago.fecha_aplicacion_pago = timezone.now()
    pago.save()

    # === FASE 5: Ajuste retroactivo (opcional; desactivado para migración simple) ===
    ajuste_id = None
    # if es_retroactivo:
    #     from .utils import crear_ajuste_retroactivo
    #     ajuste = crear_ajuste_retroactivo(
    #         prestamo.prestamo_id.prestamo_id,
    #         fecha_aplicacion,
    #         fecha_aplicacion
    #     )
    #     ajuste_id = ajuste.id

    return {
        'status': 'success',
        'message': f'Pago {pago_id} aplicado exitosamente.',
        'pago_id': pago_id,
        'monto_aplicado': float(pago.valor_pago - monto_restante),
        'excedente': float(monto_restante),
        'ajuste_id': ajuste_id
    }
#--------------- Fin aplicar pago migracion------------



