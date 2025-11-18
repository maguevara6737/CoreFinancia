# utils.py
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



def copy_common_fields_from_instance(src_instance, target_model, exclude=None):
    """
    Construye kwargs copiando los campos en común entre src_instance y target_model.
    exclude: lista de nombres de campos a excluir.
    """
    if exclude is None:
        exclude = []
    kwargs = {}
    src_fields = {f.name for f in src_instance._meta.fields}
    for f in target_model._meta.fields:
        if f.name in exclude:
            continue
        # No copiar auto fields primarios si target model los maneja
        if getattr(f, 'auto_created', False) or f.primary_key and f.auto_created:
            continue
        if f.name in src_fields:
            kwargs[f.name] = getattr(src_instance, f.name)
    return kwargs



def obtener_descripcion_concepto(llave_concepto):
    try:
        concepto = Conceptos_Transacciones.objects.get(pk=llave_concepto)
        return getattr(concepto, 'descripcion', None)
    except ObjectDoesNotExist:
        return None


def obtener_user_name_from_django_user(user_obj):
    """
    Recibe request.user y retorna su username o str(user_obj) si no tiene atributo.
    """
    try:
        return user_obj.username
    except Exception:
        return str(user_obj)


def calcular_plan_cuotas(desembolso_obj):
    from .models import  Desembolsos
    """
    Calcula el plan de pagos a partir del objeto Desembolsos.
    Devuelve una lista de dicts con: numero_cuota, capital, intereses, fecha_vencimiento, seguro, gastos...
    Reglas:
     - cuota 1: se graba con intereses = 0, capital = valor_cuota_1 y fecha = fecha_desembolso
     - monto a financiar = valor - valor_cuota_1
     - tasa mensual (según regla 30/360) = tasa (%) * 30 / 360 -> tasa/12 en decimal
     - resto de cuotas = plazo_en_meses - 1
     - para el resto (si quedan cuotas) se calcula una cuota nivelada (anualidad) sobre el monto restante.
    """
    results = []
    valor = Decimal(desembolso_obj.valor or 0)
    valor_cuota_1 = Decimal(desembolso_obj.valor_cuota_1 or 0)
    monto = (valor - valor_cuota_1).quantize(Decimal('0.01'), rounding=ROUND)
    plazo_total = int(desembolso_obj.plazo_en_meses or 0)

    # tasa anual en porcentaje -> convertir a decimal mensual con 30/360
    tasa_pct = Decimal(desembolso_obj.tasa or 0)
    # tasa_mensual_decimal = tasa_pct/100 * 30/360 == (tasa_pct/100)/12
    tasa_mensual = (tasa_pct / Decimal('100')) * (Decimal('30') / Decimal('360'))

    # Cuota 1
    if plazo_total >= 1:
        results.append({
            'numero_cuota': 1,
            'capital': valor_cuota_1.quantize(Decimal('0.01'), rounding=ROUND),
            'intereses': Decimal('0.00'),
            'fecha_vencimiento': desembolso_obj.fecha_desembolso,
            'seguro': Decimal(desembolso_obj.valor_seguro_mes or 0),
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
        pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND)
    else:
        # pago = monto * r / (1 - (1+r) ** -n)
        # usar Decimal pow: (1 + r) ** -n
        one_plus_r = (Decimal('1') + r)
        denom = (Decimal('1') - (one_plus_r ** (Decimal(-n))))
        if denom == 0:
            pago_mensual = (monto / n).quantize(Decimal('0.01'), rounding=ROUND)
        else:
            pago_mensual = (monto * r / denom).quantize(Decimal('0.01'), rounding=ROUND)

    saldo = monto
    # Fecha de la primera cuota nivelada: generalmente un mes después del desembolso,
    # pero como dia de cobro es dia_cobro, usaremos fecha_desembolso + 1 month manteniendo dia_cobro.
    # Para simplificar, sumamos meses consecutivos desde fecha_desembolso.
    fecha_base = desembolso_obj.fecha_desembolso

    for i in range(1, cuotas_restantes + 1):
        # número de cuota global será (i+1) porque la 1 ya fue guardada
        numero = i + 1
        if r == 0:
            intereses = Decimal('0.00')
            capital = pago_mensual
        else:
            intereses = (saldo * r).quantize(Decimal('0.01'), rounding=ROUND)
            capital = (pago_mensual - intereses).quantize(Decimal('0.01'), rounding=ROUND)

        # Si es la última cuota, ajustar capital para evitar residuos por redondeo
        if i == cuotas_restantes:
            # Ajuste final: capital = saldo, intereses = pago - capital (o recalc)
            capital = saldo.quantize(Decimal('0.01'), rounding=ROUND)
            intereses = (pago_mensual - capital).quantize(Decimal('0.01'), rounding=ROUND)
            # Si intereses negativo (por redondeo), forzarlo a 0
            if intereses < 0:
                intereses = Decimal('0.00')

        fecha_venc = (fecha_base + relativedelta(months=i)).replace(day=min(desembolso_obj.dia_cobro, 28 if fecha_base.day>28 else desembolso_obj.dia_cobro))
        # safer: if dia_cobro > 28, limit handling to avoid invalid dates
        try:
            fecha_venc = fecha_base + relativedelta(months=i)
            # force day to dia_cobro if possible
            target_day = int(desembolso_obj.dia_cobro)
            fecha_venc = fecha_venc.replace(day=min(target_day, 28)) if target_day > 28 else fecha_venc.replace(day=target_day)
        except Exception:
            # Fallback: add months only
            fecha_venc = fecha_base + relativedelta(months=i)

        results.append({
            'numero_cuota': numero,
            'capital': capital,
            'intereses': intereses,
            'fecha_vencimiento': fecha_venc,
            'seguro': Decimal(desembolso_obj.valor_seguro_mes or 0),
            'gastos': Decimal('0.00'),
            'saldo_capital': Decimal('0.00'),
            'saldo_intereses': Decimal('0.00'),
            'saldo_seguro': Decimal('0.00'),
            'saldo_gastos': Decimal('0.00'),
        })
        saldo = (saldo - capital).quantize(Decimal('0.01'), rounding=ROUND)
        if saldo < 0:
            saldo = Decimal('0.00')

    return results


def procesar_desembolsos_a_prestamos(desembolsos_qs, request, fecha_proceso, proceso_codigo, asiento, concepto_id, usuario):

    from .models import Prestamos, Historia_Prestamos, Movimientos, Bitacora, Conceptos_Transacciones

    resultados = {
        'ok': True,
        'insertados': {'prestamos': 0, 'historia': 0, 'plan_pagos': 0, 'movimientos': 0, 'bitacora': 0},
        'mensajes': [],
        'errores': [],
        'prestamo_ids': [],
    }

    numerador_val = asiento
    user_name = usuario

    try:
        with transaction.atomic():
            prestamos_created = []
            historia_to_create = []
            plan_pagos_to_create = []
            movimientos_to_create = []

            # Asegúrate de tener el objeto Conceptos_Transacciones
            concepto_obj = Conceptos_Transacciones.objects.get(pk=concepto_id)

            for d in desembolsos_qs:
                if getattr(d, 'estado', None) not in ('PENDIENTE'):
                    continue

                # -----------------------
                # 1. Crear Prestamo
                # -----------------------
                prestamo = Prestamos(
                    prestamo_id=d,  # ✅ objeto Desembolsos (FK)
                    cliente_id=d.cliente_id,
                    asesor=d.asesor_id,
                    aseguradora=d.aseguradora_id,
                    vendedor=d.vendedor_id,
                    tipo_tasa=d.tipo_tasa,
                    tasa=d.tasa,
                    valor=d.valor,
                    valor_cuota_1=d.valor_cuota_1,
                    valor_cuota_mensual=d.valor_cuota_mensual,
                    valor_seguro_mes=d.valor_seguro_mes,
                    tiene_fee=d.tiene_fee,
                    dia_cobro=d.dia_cobro,
                    plazo_en_meses=d.plazo_en_meses,
                    fecha_desembolso=d.fecha_desembolso,
                    fecha_vencimiento=d.fecha_vencimiento,
                    suspender_causacion='NO',
                    fecha_suspension_causacion=d.fecha_desembolso,
                    revocatoria='NO',
                    fecha_revocatoria=d.fecha_desembolso,
                )
                prestamo.save()  # ✅ Guardar inmediatamente para tener ID
                prestamos_created.append(prestamo)
                resultados['prestamo_ids'].append(d.prestamo_id)

                # -----------------------
                # 2. Crear Historia_Prestamos
                # -----------------------
                historia = Historia_Prestamos(
                    prestamo_id=prestamo,  # ✅ objeto Prestamos recién creado
                    fecha_efectiva=d.fecha_desembolso,
                    fecha_proceso=fecha_proceso,
                    ordinal_interno=1,
                    numero_operacion=1,
                    concepto_id=concepto_obj,
                    fecha_vencimiento=d.fecha_vencimiento,
                    tasa=d.tasa,
                    monto_transaccion=d.valor,
                    saldo_capital=d.valor,
                    abono_capital=Decimal('0.00'),
                    intrs_ctes=Decimal('0.00'),
                    seguro=d.valor_seguro_mes or Decimal('0.00'),
                    fee=Decimal('0.00'),
                    ints_ctes=Decimal('0.00'),
                    usuario=user_name,
                    numerador_transaccion=numerador_val,
                    codigo_mov='03',
                )
                historia_to_create.append(historia)

                # -----------------------
                # 3. Crear Movimientos
                # -----------------------
                movimiento = Movimientos(
                    cliente_id=d.cliente_id,
                    asesor_id=d.asesor_id,
                    valor_movimiento=d.valor,
                    fecha_valor_mvto=timezone.now().date(),
                )
                movimientos_to_create.append(movimiento)

                # -----------------------
                # 4. Crear Plan_Pagos
                # -----------------------
                plan_items = calcular_plan_cuotas(d)
                for item in plan_items:
                    plan_pago = Plan_Pagos(
                        prestamo=prestamo,  # ✅ objeto Prestamos
                        cuota_id=item['numero_cuota'],
                        fecha_valor_inicial=d.fecha_desembolso,
                        fecha_de_vcto_cuota=item['fecha_vencimiento'],
                        tipo_de_cuota='N',  # asumimos 'Normal'
                        monto_capital=item['capital'],
                        monto_interes=item['intereses'],
                        monto_seguro=item['seguro'],
                        monto_gastos=item['gastos'],
                        saldo_capital=item['saldo_capital'],
                        saldo_interes=item['saldo_intereses'],
                        saldo_seguro=item['saldo_seguro'],
                        saldo_gastos=item['saldo_gastos'],
                    )
                    plan_pagos_to_create.append(plan_pago)

            # Guardar el resto con bulk_create (ya tienen FK válidas)
            if historia_to_create:
                Historia_Prestamos.objects.bulk_create(historia_to_create)
                resultados['insertados']['historia'] = len(historia_to_create)

            if movimientos_to_create:
                Movimientos.objects.bulk_create(movimientos_to_create)
                resultados['insertados']['movimientos'] = len(movimientos_to_create)

            if plan_pagos_to_create:
                Plan_Pagos.objects.bulk_create(plan_pagos_to_create)
                resultados['insertados']['plan_pagos'] = len(plan_pagos_to_create)

            resultados['insertados']['prestamos'] = len(prestamos_created)

            # Bitácora
            evento = f"Desembolsos de créditos {resultados['prestamo_ids']}"
            Bitacora.objects.bulk_create([
                Bitacora(
                    fecha_proceso=fecha_proceso,
                    user_name=user_name,
                    evento_realizado=f"Inicia proceso: {evento}"[:30],
                    proceso=proceso_codigo[:10],
                    resultado="inicio"
                ),
                Bitacora(
                    fecha_proceso=fecha_proceso,
                    user_name=user_name,
                    evento_realizado=f"Fin proceso: {evento}"[:30],
                    proceso=proceso_codigo[:10],
                    resultado="fin ok"
                )
            ])
            resultados['insertados']['bitacora'] = 2

            resultados['mensajes'].append(f"Proceso completado. Préstamos creados: {len(prestamos_created)}.")
            return resultados

    except Exception as e:
        # Registrar error
        try:
            Bitacora.objects.create(
                fecha_proceso=fecha_proceso,
                user_name=user_name,
                evento_realizado=f"Error proceso"[:30],
                proceso=proceso_codigo[:10],
                resultado=f"error {str(e)}"[:100]
            )
        except:
            pass
        resultados['ok'] = False
        resultados['errores'].append(str(e))
        resultados['mensajes'].append(f"Error: {e}")
        return resultados
   

#---------------------- desembolso func
from datetime import date


def create_prestamo(desembolso):
    from  .models import Prestamos
    """
    Creates a Prestamo record based on a Desembolso instance.
    Uses default values for optional fields if not provided.
    """
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


def create_loan_payments(prestamo, desembolso, plan_pagos, user_name):
    """
    Guarda el plan de pagos generado por calculate_loan_schedule
    como registros en Historia_Prestamos, usando los conceptos adecuados.
    """
    from . import ConceptosTransacciones, Historia_Prestamos

    concepto_capital = ConceptosTransacciones.objects.get(nombre="Amortización de Capital")
    concepto_interes = ConceptosTransacciones.objects.get(nombre="Interés Corriente")
    concepto_seguro = ConceptosTransacciones.objects.get(nombre="Seguro")
    concepto_gastos = ConceptosTransacciones.objects.get(nombre="Gastos")

    created_count = 0

    for cuota in plan_pagos:
        numero_cuota = cuota['numero_cuota']
        fecha_vencimiento = cuota['fecha_vencimiento']

        # Crear registro para capital
        if cuota['capital'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo.id,
                concepto_id=concepto_capital.id,
                monto_transaccion=float(cuota['capital']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
            )
            created_count += 1

        # Crear registro para intereses
        if cuota['intereses'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo.id,
                concepto_id=concepto_interes.id,
                monto_transaccion=float(cuota['intereses']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
            )
            created_count += 1

        # Crear registro para seguro
        if cuota['seguro'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo.id,
                concepto_id=concepto_seguro.id,
                monto_transaccion=float(cuota['seguro']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
            )
            created_count += 1

        # Crear registro para gastos
        if cuota['gastos'] > 0:
            Historia_Prestamos.objects.create(
                prestamo_id=prestamo.id,
                concepto_id=concepto_gastos.id,
                monto_transaccion=float(cuota['gastos']),
                fecha_vencimiento=fecha_vencimiento,
                estado="PENDIENTE",
                numero_cuota=numero_cuota,
            )
            created_count += 1

    return created_count
    
