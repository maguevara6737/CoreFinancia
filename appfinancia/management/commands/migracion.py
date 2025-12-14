import os
import logging
import unicodedata
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from appfinancia.models import (
    Clientes, Desembolsos, Prestamos, Pagos, Bitacora,
    Tipos_Identificacion, Departamentos, Municipios, Migrados,
    Asesores, Aseguradoras, Vendedores
)
from appfinancia.utils import (
    create_movimiento,
    calculate_loan_schedule,
    create_loan_payments,
    cerrar_periodo_interes_migracion,
    aplicar_pago_migracion,
    get_next_asientos_id
)

User = get_user_model()

NOMBRES_COMPUESTOS = {
    'DE LOS ANGELES', 'DE LAS MERCEDES', 'DE LOS REYES',
    'DEL CARMEN', 'DEL SOCORRO', 'DEL PILAR', 'DEL SOL'
}

APELLIDOS_COMPUESTOS = {
    'DE LA ESPRIELLA', 'DE LOS RIOS', 'DE LA TORRE', 'DE LA RUE', 'DE LA VEGA',
    'DE BRIGARD', 'DEL MAR', 'DE LA HOZ', 'DE LA CRUZ', 'DE LA OSSA'
}

def generar_id_corto(nombre: str, max_len=15) -> str:
    if not nombre or not nombre.strip():
        return "MIGRACION"
    limpio = "".join(c for c in nombre if c.isalnum())[:max_len]
    return limpio.upper() or "MIGRACION"

def excel_serial_to_date(value):
    if pd.isna(value) or value in (None, '', 0, '0'):
        return None
    if isinstance(value, (int, float)):
        return pd.to_datetime(value, unit='D', origin='1899-12-30').date()
    elif isinstance(value, pd.Timestamp):
        return value.date()
    elif isinstance(value, datetime):
        return value.date()
    else:
        try:
            return pd.to_datetime(str(value)).date()
        except Exception:
            return None

def safe_decimal(value, default='0.00', decimal_places=2):
    if pd.isna(value) or value in (None, '', '0', 0):
        num = Decimal(default)
    else:
        try:
            num = Decimal(str(value).strip())
        except (InvalidOperation, ValueError, TypeError):
            num = Decimal(default)
    quant = Decimal('0.' + '0' * decimal_places) if decimal_places > 0 else Decimal('1')
    return num.quantize(quant)

def separar_nombre_apellido_cc(nombre_completo: str) -> tuple[str, str]:
    if not nombre_completo or not nombre_completo.strip():
        return "", ""
    texto = nombre_completo.strip().upper()
    palabras = texto.split()
    n = len(palabras)
    for i in range(n):
        for j in range(i + 1, n + 1):
            fragmento = " ".join(palabras[i:j])
            if fragmento in NOMBRES_COMPUESTOS:
                nombre = " ".join(palabras[:j])
                apellido = " ".join(palabras[j:]) if j < n else ""
                return nombre[:40], apellido[:40]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            fragmento = " ".join(palabras[i:j+1])
            if fragmento in APELLIDOS_COMPUESTOS:
                nombre = " ".join(palabras[:i]) if i > 0 else ""
                apellido = " ".join(palabras[i:])
                return nombre[:40], apellido[:40]
    if n == 1:
        return palabras[0][:40], ""
    elif n == 2:
        return palabras[0][:40], palabras[1][:40]
    elif n == 3:
        return palabras[0][:40], " ".join(palabras[1:])[:40]
    else:
        return " ".join(palabras[:2])[:40], " ".join(palabras[2:])[:40]

class Command(BaseCommand):
    help = 'Migración de préstamos desde Excel (aresmig.xlsx)'

    def handle(self, *args, **options):
        archivo_excel = 'appfinancia/entradas/aresmig.xlsx'
        if not os.path.exists(archivo_excel):
            self.stdout.write(self.style.ERROR(f"❌ Archivo no encontrado: {archivo_excel}"))
            return

        log_filename = f"migracion_{datetime.now().strftime('%Y%m%d%H%M')}.log"
        log_path = os.path.join('appfinancia/logs', log_filename)
        os.makedirs('appfinancia/logs', exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info("=== INICIANDO MIGRACIÓN ===")

        # === USUARIO 'sistema' ===
        try:
            usuario_sistema = User.objects.get(username='sistema')
        except User.DoesNotExist:
            usuario_sistema = User.objects.create_user(
                username='sistema',
                email='sistema@corefinancia.local',
                password='Migra2025!'
            )
            logger.info("✅ Usuario 'sistema' creado.")

        # === REGISTROS 'MIGRACION' ===
        asesor_migracion, _ = Asesores.objects.get_or_create(
            asesor_id='MIGRACION',
            defaults={'asesor_nombre': 'MIGRACION', 'asesor_estado': 'HABILITADO'}
        )
        aseguradora_migracion, _ = Aseguradoras.objects.get_or_create(
            aseguradora_id='MIGRACION',
            defaults={'aseguradora_nombre': 'MIGRACION', 'aseguradora_estado': 'HABILITADO'}
        )
        vendedor_migracion, _ = Vendedores.objects.get_or_create(
            cod_venta_id='MIGRACION',
            defaults={'cod_venta_nombre': 'MIGRACION', 'estado': 'HABILITADO'}
        )

        # === CARGA DE CLIENTES ===
        logger.info("=== CARGANDO CLIENTES ===")
        df_clientes = pd.read_excel(archivo_excel, sheet_name='Datos Clientes')
        clientes_procesados = 0
        clientes_error = 0

        tipo_cc = Tipos_Identificacion.objects.get(tipo_id='CC')
        tipo_nit = Tipos_Identificacion.objects.get(tipo_id='NIT')

        depto_bogota, _ = Departamentos.objects.get_or_create(
            departamento_id=11,
            defaults={'departamento_nombre': 'CUNDINAMARCA'}
        )
        mun_bogota, _ = Municipios.objects.get_or_create(
            municipio_id=11001,
            departamento=depto_bogota,
            defaults={'municipio_nombre': 'BOGOTÁ D.C.'}
        )

        for idx, row in df_clientes.iterrows():
            try:
                raw_id = row['IDENTIFICACION']
                if pd.isna(raw_id):
                    raise ValueError("IDENTIFICACION vacía")
                cliente_id = int(float(raw_id))

                if 8000000000 < cliente_id < 9029999999:
                    tipo_id_obj = tipo_nit
                    nombre_raw = str(row['NOMBRE']).strip() if pd.notna(row['NOMBRE']) else ''
                    if len(nombre_raw) > 40:
                        nombre_nuevo = nombre_raw[:40]
                        apellido_nuevo = nombre_raw[40:80]
                    else:
                        nombre_nuevo = nombre_raw
                        apellido_nuevo = ""
                else:
                    tipo_id_obj = tipo_cc
                    nombre_raw = str(row['NOMBRE']).strip() if pd.notna(row['NOMBRE']) else ''
                    nombre_nuevo, apellido_nuevo = separar_nombre_apellido_cc(nombre_raw)

                raw_telefono = str(row['Telefono']) if pd.notna(row['Telefono']) else ''
                digitos = ''.join(filter(str.isdigit, raw_telefono))
                telefono_nuevo = int(digitos[:10]) if digitos else 0

                raw_direccion = str(row['Direccion']).strip() if pd.notna(row['Direccion']) else ''
                direccion_nueva = raw_direccion[:120]

                email_nuevo = str(row['Correo']).strip()[:120] if pd.notna(row['Correo']) else ''

                observaciones_nuevas = raw_telefono[:200]

                direccion_upper = raw_direccion.upper() if raw_direccion else ''
                palabras_dir = direccion_upper.split()
                municipio_asignado = None
                for palabra in reversed(palabras_dir):
                    candidato = Municipios.objects.filter(municipio_nombre__icontains=palabra).first()
                    if candidato:
                        municipio_asignado = candidato
                        break

                if municipio_asignado:
                    depto_final = municipio_asignado.departamento
                    mun_final = municipio_asignado
                else:
                    depto_final = depto_bogota
                    mun_final = mun_bogota

                cliente, creado = Clientes.objects.get_or_create(
                    cliente_id=cliente_id,
                    defaults={
                        'tipo_id': tipo_id_obj,
                        'nombre': nombre_nuevo.upper() if nombre_nuevo else "",
                        'apellido': apellido_nuevo[:40].upper() if apellido_nuevo else "",
                        'fecha_nacimiento': date(1900, 1, 1),
                        'telefono': telefono_nuevo,
                        'direccion': direccion_nueva.upper() if direccion_nueva else "",
                        'departamento': depto_final,
                        'municipio': mun_final,
                        'email': email_nuevo,
                        'estado': 'HABILITADO'
                    }
                )

                if not creado:
                    actualizado = False
                    if cliente.tipo_id != tipo_id_obj:
                        cliente.tipo_id = tipo_id_obj
                        actualizado = True
                    if nombre_nuevo and nombre_nuevo.strip():
                        cliente.nombre = nombre_nuevo[:40].upper()
                        actualizado = True
                    if apellido_nuevo and apellido_nuevo.strip():
                        cliente.apellido = apellido_nuevo[:40].upper()
                        actualizado = True
                    if telefono_nuevo != 0:
                        cliente.telefono = telefono_nuevo
                        actualizado = True
                    if direccion_nueva and direccion_nueva.strip():
                        cliente.direccion = direccion_nueva.upper()
                        actualizado = True
                    if email_nuevo and email_nuevo.strip():
                        cliente.email = email_nuevo
                        actualizado = True
                    if cliente.departamento != depto_final or cliente.municipio != mun_final:
                        cliente.departamento = depto_final
                        cliente.municipio = mun_final
                        actualizado = True
                    if actualizado:
                        cliente.save()

                clientes_procesados += 1
            except Exception as e:
                logger.error(f"Error en cliente fila {idx+2} (ID={raw_id}): {e}")
                clientes_error += 1

        logger.info(f"Clientes: {clientes_procesados} procesados, {clientes_error} errores")

        # === CARGA DE PRÉSTAMOS ===
        logger.info("=== CARGANDO PRÉSTAMOS ===")
        hojas_creditos = ["Creditos", "Creditos Nuevos"]
        df_list = []
        for hoja in hojas_creditos:
            df_temp = pd.read_excel(archivo_excel, sheet_name=hoja)
            nuevos_nombres = []
            for col in df_temp.columns:
                nombre_limpio = unicodedata.normalize('NFD', str(col))
                nombre_limpio = ''.join(c for c in nombre_limpio if unicodedata.category(c) != 'Mn')
                nombre_limpio = nombre_limpio.upper().strip()
                nombre_limpio = ''.join(c if c.isalnum() or c == ' ' else '' for c in nombre_limpio)
                nombre_limpio = ' '.join(nombre_limpio.split())
                nuevos_nombres.append(nombre_limpio)
            df_temp.columns = nuevos_nombres
            df_list.append(df_temp)
        df_creditos = pd.concat(df_list, ignore_index=True)

        if 'NUMERO DE CREDITO' not in df_creditos.columns:
            raise KeyError(f"Columna 'NUMERO DE CREDITO' no encontrada. Columnas: {list(df_creditos.columns)}")

        df_creditos['clave'] = df_creditos['NUMERO DE CREDITO'].astype(str)
        grupos = df_creditos.groupby('clave')

        estadisticas = {
            'prestamos_leidos': len(df_creditos),
            'prestamos_grabados': 0,
            'prestamos_error': 0,
            'monto_total_leido': Decimal('0.00'),
            'monto_total_grabado': Decimal('0.00'),
            'monto_total_error': Decimal('0.00'),
        }

        for clave, grupo in grupos:
            if len(grupo) != 1:
                logger.warning(f"Clave duplicada: {clave}. Se procesará solo la primera.")
            row = grupo.iloc[0]

            try:
                cliente_id = int(row['ID CLIENTE'])
                if not Clientes.objects.filter(cliente_id=cliente_id).exists():
                    raise ValueError(f"Cliente {cliente_id} no existe")

                prestamo_id = int(row['NUMERO DE CREDITO'])
                valor = safe_decimal(row['VR DESEMBOLSO'], '0.00', 2)
                estadisticas['monto_total_leido'] += valor

                fecha_desembolso = excel_serial_to_date(row['FECHA DESEMBOLSO'])
                if fecha_desembolso is None:
                    fecha_desembolso = excel_serial_to_date(row['FECHA INICIO VIGENCIA'])
                if fecha_desembolso is None:
                    raise ValueError("No se pudo determinar la fecha de desembolso.")

                # --- ASESOR ---
                asesor_nombre = str(row['ASESOR']).strip() if pd.notna(row['ASESOR']) else ''
                if not asesor_nombre:
                    asesor_obj = asesor_migracion
                else:
                    asesor_id_corto = generar_id_corto(asesor_nombre, 15)
                    asesor_obj, _ = Asesores.objects.get_or_create(
                        asesor_id=asesor_id_corto,
                        defaults={'asesor_nombre': asesor_nombre[:30], 'asesor_estado': 'HABILITADO'}
                    )

                # --- ASEGURADORA ---
                aseguradora_nombre = str(row['ASEGURADORA']).strip() if pd.notna(row['ASEGURADORA']) else ''
                if not aseguradora_nombre:
                    aseguradora_obj = aseguradora_migracion
                else:
                    aseguradora_id_corto = generar_id_corto(aseguradora_nombre, 15)
                    aseguradora_obj, _ = Aseguradoras.objects.get_or_create(
                        aseguradora_id=aseguradora_id_corto,
                        defaults={'aseguradora_nombre': aseguradora_nombre[:30], 'aseguradora_estado': 'HABILITADO'}
                    )

                vendedor_obj = vendedor_migracion

                valor_cuota_1 = safe_decimal(row.get('VALOR DE CUOTA INICIAL', 0), '0.00', 2)
                valor_seguro = safe_decimal(row.get('SEGURO DE VIDA MENSUAL', 0), '0.00', 2)
                tipo_tasa = 'CON SEGURO' if valor_seguro > Decimal('0.00') else 'SIN SEGURO'
                tasa = safe_decimal(row['TASA'] * 12 * 100, '0.00', 2)
                valor_cuota_mensual = safe_decimal(row['VALOR DE CUOTA'], '0.00', 2)
                tiene_fee = str(row.get('Tiene FEE', 'NO')).strip().upper() if pd.notna(row.get('Tiene FEE')) else 'NO'
                plazo_en_meses = int(row['TOTAL CUOTAS']) if pd.notna(row['TOTAL CUOTAS']) else 12
                valor = valor  # este es el monto sobre el cual se calculan las cuotas (sin incluir valor_cuota_1)

                with transaction.atomic():
                    desembolso = Desembolsos.objects.create(
                        cliente_id_id=cliente_id,
                        prestamo_id=prestamo_id,
                        asesor_id=asesor_obj,
                        aseguradora_id=aseguradora_obj,
                        vendedor_id=vendedor_obj,
                        tipo_tasa_id=tipo_tasa,
                        tasa=tasa,
                        valor=valor,
                        valor_cuota_1=valor_cuota_1,
                        numero_transaccion_cuota_1='0',
                        valor_cuota_mensual=valor_cuota_mensual,
                        valor_seguro_mes=valor_seguro,
                        tiene_fee=tiene_fee,
                        plazo_en_meses=plazo_en_meses,
                        fecha_desembolso=fecha_desembolso,
                        estado='DESEMBOLSADO',
                        dia_cobro=fecha_desembolso.day
                    )
                    desembolso.fecha_vencimiento = desembolso.fecha_desembolso + pd.DateOffset(months=desembolso.plazo_en_meses)
                    desembolso.save(update_fields=['fecha_vencimiento'])

                    Prestamos.objects.create(
                        prestamo_id=desembolso,
                        cliente_id_id=cliente_id,
                        asesor_id=asesor_obj,
                        aseguradora_id=aseguradora_obj,
                        vendedor_id=vendedor_obj,
                        tipo_tasa_id=desembolso.tipo_tasa_id,
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
                        revocatoria='NO'
                    )

                    create_movimiento(desembolso)

                    Migrados.objects.create(
                        prestamo_id=prestamo_id,
                        origen_migracion='aresmig.xlsx'
                    )

                    estadisticas['prestamos_grabados'] += 1
                    estadisticas['monto_total_grabado'] += valor

            except Exception as e:
                logger.error(f"Error en préstamo {clave}: {e}")
                estadisticas['prestamos_error'] += 1
                estadisticas['monto_total_error'] += safe_decimal(row['VR DESEMBOLSO'], '0.00', 2)

        # === CARGA DE PAGOS ===
        logger.info("=== CARGANDO PAGOS ===")
        df_pagos = pd.read_excel(archivo_excel, sheet_name='PAGOS HIST')
        for idx, row in df_pagos.iterrows():
            try:
                prestamo_id_real = int(row['NUMERO DE CREDITO'])
                fecha_pago = excel_serial_to_date(row['FECHA'])
                if fecha_pago is None:
                    raise ValueError(f"Fecha de pago inválida en fila {idx+2}")

                valor_pago = safe_decimal(row['VAL PAGO'], '0.00', 2)

                # ✅ Verificar que exista el desembolso
                try:
                    desembolso = Desembolsos.objects.get(prestamo_id=prestamo_id_real)
                except Desembolsos.DoesNotExist:
                    logger.warning(
                        f"_pago ignorado: no existe desembolso para préstamo {prestamo_id_real} (fila {idx+2}). "
                        f"Posible pago huérfano o crédito fuera del alcance de la migración._"
                    )
                    continue  # ← ¡IGNORAR pago sin desembolso!

                # ✅ Comparar con valor_cuota_1
                if desembolso.valor_cuota_1 is not None and valor_pago == desembolso.valor_cuota_1:
                    logger.info(
                        f"_pago ignorado por ser igual a la cuota 1 - Préstamo {prestamo_id_real}, "
                        f"Fecha {fecha_pago}, Valor Pago {valor_pago}, Cuota 1 {desembolso.valor_cuota_1}_"
                    )
                    continue  # ← ¡IGNORAR pago de cuota inicial!

                # ✅ Crear el pago (solo si pasa ambas validaciones)
                cliente_id_real = desembolso.cliente_id.cliente_id if desembolso.cliente_id else None
                Pagos.objects.create(
                    prestamo_id_real=prestamo_id_real,
                    cliente_id_real=cliente_id_real,
                    fecha_pago=fecha_pago,
                    hora_pago='00:00:00',
                    fecha_aplicacion_pago=None,
                    fecha_conciliacion=None,
                    nombre_archivo_id='MIGRACION',
                    creado_por=usuario_sistema,
                    estado_pago='conciliado',
                    valor_pago=valor_pago
                )

            except Exception as e:
                logger.error(f"Error en pago fila {idx+2}: {e}")

        # === GENERAR HISTORIA_PRESTAMOS (solo migrados y ≥2025-01-01) ===
        logger.info("=== GENERANDO HISTORIA PRESTAMOS ===")
        prestamos_migrados_ids = list(Migrados.objects.values_list('prestamo_id', flat=True))
        if prestamos_migrados_ids:
            desembolsos_a_proyectar = Desembolsos.objects.filter(
                prestamo_id__in=prestamos_migrados_ids,
                fecha_desembolso__gte=date(2025, 1, 1),
                estado='DESEMBOLSADO'
            )
            for desembolso in desembolsos_a_proyectar:
                try:
                    with transaction.atomic():
                        prestamo = desembolso.prestamos
                        plan = calculate_loan_schedule(desembolso)
                        create_loan_payments(prestamo, desembolso, plan, usuario_sistema.username)
                        # ✅ Usar función de migración (evita error de instancia)
                        cerrar_periodo_interes_migracion(
                            prestamo_id=desembolso.prestamo_id,
                            fecha_corte=desembolso.fecha_desembolso,
                            pago_referencia=f"DESEMBOLSO_{desembolso.prestamo_id}",
                            numero_asiento_contable=1
                        )
                except Prestamos.DoesNotExist:
                    logger.error(f"El desembolso {desembolso.prestamo_id} no tiene un préstamo asociado.")
                except Exception as e:
                    logger.error(f"Error al generar plan para préstamo {desembolso.prestamo_id}: {e}")
        else:
            logger.info("No hay préstamos migrados para generar historial.")

        # === APLICAR PAGOS (solo de préstamos migrados Y que existan en Prestamos) ===
        logger.info("=== APLICANDO PAGOS MIGRADOS  ===")
        if prestamos_migrados_ids:
            pagos_a_aplicar = Pagos.objects.filter(
                estado_pago='conciliado',
                prestamo_id_real__in=prestamos_migrados_ids
            )
            for pago in pagos_a_aplicar:
                # ✅ Verificación crítica: el préstamo debe existir en Prestamos
                if not Prestamos.objects.filter(prestamo_id=pago.prestamo_id_real).exists():
                    logger.warning(
                        f"El préstamo {pago.prestamo_id_real} no existe en Prestamos. Pago {pago.pago_id} omitido."
                    )
                    continue
                try:
                    with transaction.atomic():
                        asiento = get_next_asientos_id()
                        aplicar_pago_migracion(pago.pago_id, usuario_sistema.username, asiento)
                except Exception as e:
                    logger.error(f"Error al aplicar pago {pago.pago_id}: {e}")
        else:
            logger.info("No hay pagos de préstamos migrados para aplicar.")

        # === REGISTRO EN BITÁCORA ===
        resumen = (
            f"Clientes: procesados={clientes_procesados}, errores={clientes_error}\n"
            f"Préstamos: leídos={estadisticas['prestamos_leidos']}, "
            f"grabados={estadisticas['prestamos_grabados']}, errores={estadisticas['prestamos_error']}\n"
            f"Montos: leído=${estadisticas['monto_total_leido']:,.2f}, "
            f"grabado=${estadisticas['monto_total_grabado']:,.2f}, errores=${estadisticas['monto_total_error']:,.2f}"
        )
        logger.info("=== RESUMEN FINAL ===\n" + resumen)

        Bitacora.objects.create(
            fecha_proceso=timezone.now().date(),
            user_name=usuario_sistema.username,
            evento_realizado='MIGRACION_EXCEL',
            proceso='EXITO',
            resultado=resumen
        )

        self.stdout.write(self.style.SUCCESS("✅ Migración completada."))
#--- fin