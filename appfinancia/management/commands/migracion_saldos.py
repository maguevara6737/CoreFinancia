import os
import logging
import unicodedata
from datetime import datetime, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from dateutil.relativedelta import relativedelta

from appfinancia.models import (
    Clientes, Desembolsos, Prestamos, Migrados, Bitacora,
    Asesores, Aseguradoras, Vendedores, Historia_Prestamos,
    Conceptos_Transacciones, Fechas_Sistema, Tipos_Identificacion,
    Departamentos, Municipios
)
from appfinancia.utils import (
    create_movimiento,
    cerrar_periodo_interes_migracion,
    get_next_asientos_id
)

User = get_user_model()

# --- FUNCIONES DE SOPORTE SOLICITADAS ---

def obtener_prestamo_unico(cliente_id):
    """
    Retorna el ID del préstamo y si es cuota inicial ('SI'/'NO').
    Basado en el estado del desembolso relacionado.
    """
    prestamos = Prestamos.objects.filter(cliente_id_id=cliente_id)
    if prestamos.count() == 1:
        prestamo_obj = prestamos.first()
        desembolso = prestamo_obj.prestamo_id
        # Lógica solicitada: Si estado != 'DESEMBOLSADO' es cuota inicial
        es_cuota_inicial = 'SI' if desembolso.estado != 'DESEMBOLSADO' else 'NO'
        return prestamo_obj.pk, es_cuota_inicial
    return None, None

def safe_decimal(value, default='0.00'):
    if pd.isna(value) or value in (None, '', '0', 0, '#REF!'):
        return Decimal(default)
    try:
        s = str(value).replace('$', '').replace(',', '').strip()
        return Decimal(s).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return Decimal(default)

def excel_serial_to_date(value):
    if pd.isna(value) or value in (None, '', 0, '0'): return None
    if isinstance(value, (int, float)):
        return pd.to_datetime(value, unit='D', origin='1899-12-30').date()
    elif isinstance(value, (pd.Timestamp, datetime)):
        return value.date()
    try:
        return pd.to_datetime(str(value), dayfirst=True).date()
    except:
        return None

# --- COMANDO DE MIGRACIÓN ---

class Command(BaseCommand):
    help = 'Migración de Cartera NOV-30-2025: Cruce Maestro vs Saldos Reales'

    def handle(self, *args, **options):
        # 1. Configuración Inicial
        FECHA_CORTE = date(2025, 11, 30)     # <============================OJO GRABAR DIA DE CORTE MIGRACION 
        path_ares = 'appfinancia/entradas/aresmig.xlsx'
        path_saldos = 'appfinancia/entradas/saldos_cartera.xlsx'
        
        logger = logging.getLogger(__name__)
        usuario_sistema, _ = User.objects.get_or_create(username='sistema')
        fechas_sis = Fechas_Sistema.load()

        if not os.path.exists(path_ares) or not os.path.exists(path_saldos):
            self.stdout.write(self.style.ERROR("❌ Error: Faltan archivos .xlsx en entradas/"))
            return

        # 2. Cargar Diccionario de Saldos Reales (Match por NUMERO DE CREDITO)
        logger.info(">>> Sincronizando con saldos_cartera.xlsx...")
        df_cartera = pd.read_excel(path_saldos)
        df_cartera.columns = [str(c).upper().replace(' ', '_') for c in df_cartera.columns]
        mapa_saldos = df_cartera.set_index('NUMERO_DE_CREDITO').to_dict('index')

        # 3. Cargar Maestro de Créditos
        df_list = []
        for h in ["Creditos", "Creditos Nuevos"]:
            temp = pd.read_excel(path_ares, sheet_name=h)
            temp.columns = ["".join(c for c in unicodedata.normalize('NFD', str(col)) if unicodedata.category(c) != 'Mn').upper().strip() for col in temp.columns]
            df_list.append(temp)
        df_maestro = pd.concat(df_list, ignore_index=True)

        logger.info(f"=== Iniciando procesamiento de {len(df_maestro)} registros ===")

        for _, row in df_maestro.iterrows():
            id_credito = row['NUMERO DE CREDITO']
            if id_credito not in mapa_saldos:
                continue

            s_row = mapa_saldos[id_credito]
            
            try:
                with transaction.atomic():
                    # --- DATOS DEL MAESTRO (ARES) ---
                    tasa_mes_pct = safe_decimal(row.get('TASA', 0)) * 100 # ej: 0.017 -> 1.70
                    plazo_total = int(row.get('PLAZO', 0))
                    cuota_calc_maestro = safe_decimal(row.get('VALOR DE CUOTA CALCULADA'))
                    f_desem = excel_serial_to_date(row.get('FECHA DESEMBOLSO')) or excel_serial_to_date(row.get('FECHA INICIO VIGENCIA'))
                    
                    # --- DATOS DE SALDOS REALES ---
                    capital_real = safe_decimal(s_row.get('SALDO_CAPITAL'))
                    interes_causado = safe_decimal(s_row.get('SALDO_INTERESES'))
                    seguro_mes = safe_decimal(s_row.get('SALDO_SEGURO_DE_VIDA_FINAL'))
                    
                    # Cálculo Vencimiento Final (Meses de 30 días)
                    f_vencimiento_final = f_desem + relativedelta(months=plazo_total)

                    # --- CREAR DESEMBOLSO Y PRÉSTAMO ---
                    desem = Desembolsos.objects.create(
                        prestamo_id=id_credito,
                        cliente_id_id=int(row['ID CLIENTE']),
                        valor=capital_real,
                        tasa=tasa_mes_pct * 12, # Anualizada para el modelo
                        plazo_en_meses=plazo_total,
                        fecha_desembolso=f_desem,
                        fecha_vencimiento=f_vencimiento_final,
                        estado='MIGRACION' # Temporal
                    )

                    prestamo_obj = Prestamos.objects.create(
                        prestamo_id=desem,
                        cliente_id_id=desem.cliente_id_id,
                        valor=capital_real,
                        estado='ACTIVO'
                    )

                    # 1. Grabar registro "DES" en Historia
                    Historia_Prestamos.objects.create(
                        prestamo_id=prestamo_obj,
                        fecha_efectiva=f_desem,
                        fecha_proceso=fechas_sis.fecha_proceso_actual,
                        ordinal_interno=1,
                        concepto_id=Conceptos_Transacciones.objects.get(concepto_id="DES"),
                        monto_transaccion=float(capital_real),
                        tasa=desem.tasa,
                        estado="TRANSACCION ",
                        usuario='sistema'
                    )

                    # --- LÓGICA DE CASOS ---
                    if f_vencimiento_final <= FECHA_CORTE:
                        # CASO 1: VENCIDO (Cuota única final)
                        self.grabar_cuota_vencida(prestamo_obj, capital_real, interes_causado, seguro_mes, FECHA_CORTE, plazo_total, fechas_sis)
                    else:
                        # CASO 2: NORMAL (Proyectar cuotas restantes)
                        self.proyectar_cuotas_restantes(prestamo_obj, capital_real, interes_causado, seguro_mes, cuota_calc_maestro, tasa_mes_pct, FECHA_CORTE, plazo_total, f_vencimiento_final, fechas_sis)

                    # Finalizar proceso para este crédito
                    cerrar_periodo_interes_migracion(prestamo_obj.pk, FECHA_CORTE, f"MIG_{id_credito}", 1)
                    Desembolsos.objects.filter(pk=desem.pk).update(estado='DESEMBOLSADO')

            except Exception as e:
                logger.error(f"❌ Error en Crédito {id_credito}: {e}")

        self.stdout.write(self.style.SUCCESS(f"✅ Migración finalizada al corte {FECHA_CORTE}"))

    # --- FUNCIONES DE GRABACIÓN DE HISTORIA ---

    def grabar_cuota_vencida(self, p, cap, inte, seg, f_venc, num_c, f_sis):
        """Graba el bloque PLANCAP, PLANINT, PLANSEG para créditos ya vencidos."""
        conceptos = [("PLANCAP", cap), ("PLANINT", inte), ("PLANSEG", seg)]
        for i, (cid, valor) in enumerate(conceptos):
            if valor > 0 or cid == "PLANCAP":
                Historia_Prestamos.objects.create(
                    prestamo_id=p,
                    fecha_proceso=f_sis.fecha_proceso_actual,
                    ordinal_interno=300 + i,
                    concepto_id=Conceptos_Transacciones.objects.get(concepto_id=cid),
                    monto_transaccion=float(valor),
                    fecha_vencimiento=f_venc,
                    estado="PENDIENTE",
                    numero_cuota=num_c,
                    usuario='sistema'
                )
def proyectar_cuotas_restantes(self, p, saldo_cap, inte_acumulado, seg_mes, cuota_fija, tasa_mes, f_corte, plazo_total, f_fin, f_sis, f_desem_original):
        """
        MIGRACIÓN FINAL:
        1. Respeta el DÍA de desembolso para todos los vencimientos.
        2. Camino A: Intereses pendientes cargados en Cuota 1 (mes sigte a migracion).
        3. Ajuste de centavos en la última cuota.
        """
        # Extraemos el día original de cobro
        dia_cobro = f_desem_original.day
        
        # Calcular cuotas faltantes desde el corte
        delta = relativedelta(f_fin, f_corte)
        cuotas_faltantes = (delta.years * 12) + delta.months
        if cuotas_faltantes <= 0: cuotas_faltantes = 1

        saldo_vivo = saldo_cap
        r = tasa_mes / 100
        logger = logging.getLogger(__name__)

        for n in range(1, cuotas_faltantes + 1):
            # Determinamos el mes de vencimiento (proximo mes al migracion es n=1)
            mes_venc = f_corte + relativedelta(months=n)
            
            # Ajustamos al día de cobro original (manejando meses de 28, 29, 30 días)
            try:
                f_venc = mes_venc.replace(day=dia_cobro)
            except ValueError:
                # Si el día no existe (ej. 31 de Febrero), se asigna el último día del mes
                f_venc = mes_venc + relativedelta(day=31)

            num_c = (plazo_total - cuotas_faltantes) + n
            
            # --- CÁLCULO DE INTERÉS ---
            i_cuota = (saldo_vivo * r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            if n == 1:
                # Cargamos los intereses que el Excel reporta como pendientes
                i_cuota += inte_acumulado
            
            # --- CÁLCULO DE CAPITAL ---
            if n == cuotas_faltantes:
                # Última cuota: Liquidamos el saldo vivo restante
                cap_cuota = saldo_vivo
            else:
                # Cuotas normales: Cuota Fija - Interés - Seguro
                cap_cuota = cuota_fija - i_cuota - seg_mes
                
                # Validaciones de seguridad
                if cap_cuota > saldo_vivo: cap_cuota = saldo_vivo
                if cap_cuota < 0: cap_cuota = Decimal('0.00')

            # --- GRABACIÓN ---
            self.grabar_cuota_vencida(p, cap_cuota, i_cuota, seg_mes, f_venc, num_c, f_sis)
            
            # Actualización de saldo
            saldo_vivo -= cap_cuota
            
            if saldo_vivo <= 0:
                break