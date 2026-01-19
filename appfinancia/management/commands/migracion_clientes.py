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
    Clientes, Bitacora, Tipos_Identificacion, 
    Departamentos, Municipios, Asesores, Aseguradoras, Vendedores
)

User = get_user_model()

# Constantes para limpieza de nombres
NOMBRES_COMPUESTOS = {'DE LOS ANGELES', 'DE LAS MERCEDES', 'DE LOS REYES', 'DEL CARMEN', 'DEL SOCORRO', 'DEL PILAR', 'DEL SOL'}
APELLIDOS_COMPUESTOS = {'DE LA ESPRIELLA', 'DE LOS RIOS', 'DE LA TORRE', 'DE LA RUE', 'DE LA VEGA', 'DE BRIGARD', 'DEL MAR', 'DE LA HOZ', 'DE LA CRUZ', 'DE LA OSSA'}

def generar_id_corto(nombre: str, max_len=15) -> str:
    if not nombre or not nombre.strip():
        return "MIGRACION"
    limpio = "".join(c for c in nombre if c.isalnum())[:max_len]
    return limpio.upper() or "MIGRACION"

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
    if n == 1: return palabras[0][:40], ""
    elif n == 2: return palabras[0][:40], palabras[1][:40]
    elif n == 3: return palabras[0][:40], " ".join(palabras[1:])[:40]
    else: return " ".join(palabras[:2])[:40], " ".join(palabras[2:])[:40]

class Command(BaseCommand):
    help = 'PASO 1: Migración de Clientes y Tablas Maestras (Asesores, Aseguradoras, Vendedores)'

    def handle(self, *args, **options):
        archivo_excel = 'appfinancia/entradas/aresmig.xlsx'
        if not os.path.exists(archivo_excel):
            self.stdout.write(self.style.ERROR(f"❌ Archivo no encontrado: {archivo_excel}"))
            return

        os.makedirs('appfinancia/logs', exist_ok=True)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        logger = logging.getLogger(__name__)

        # === USUARIO SISTEMA Y REGISTROS BASE ===
        usuario_sistema, _ = User.objects.get_or_create(username='sistema', defaults={'email': 'sistema@corefinancia.local'})
        
        # Crear registros por defecto para evitar errores de llave foránea
        Asesores.objects.get_or_create(asesor_id='MIGRACION', defaults={'asesor_nombre': 'MIGRACION', 'asesor_estado': 'HABILITADO'})
        Aseguradoras.objects.get_or_create(aseguradora_id='MIGRACION', defaults={'aseguradora_nombre': 'MIGRACION', 'aseguradora_estado': 'HABILITADO'})
        Vendedores.objects.get_or_create(cod_venta_id='MIGRACION', defaults={'cod_venta_nombre': 'MIGRACION', 'estado': 'HABILITADO'})

        # === CARGA DE CLIENTES ===
        logger.info("=== CARGANDO CLIENTES ===")
        df_clientes = pd.read_excel(archivo_excel, sheet_name='Datos Clientes')
        
        # Cache de objetos geográficos
        tipo_cc = Tipos_Identificacion.objects.get(tipo_id='CC')
        tipo_nit = Tipos_Identificacion.objects.get(tipo_id='NIT')
        depto_bogota, _ = Departamentos.objects.get_or_create(departamento_id=11, defaults={'departamento_nombre': 'CUNDINAMARCA'})
        mun_bogota, _ = Municipios.objects.get_or_create(municipio_id=11001, departamento=depto_bogota, defaults={'municipio_nombre': 'BOGOTÁ D.C.'})

        c_proc, c_err = 0, 0
        for idx, row in df_clientes.iterrows():
            try:
                with transaction.atomic():
                    raw_id = row['IDENTIFICACION']
                    if pd.isna(raw_id): continue
                    cliente_id = int(float(raw_id))

                    # Lógica de nombres y tipos
                    nombre_raw = str(row.get('NOMBRE', '')).strip()
                    if 8000000000 < cliente_id < 9029999999:
                        t_obj = tipo_nit
                        n_nuevo, a_nuevo = nombre_raw[:40], nombre_raw[40:80]
                    else:
                        t_obj = tipo_cc
                        n_nuevo, a_nuevo = separar_nombre_apellido_cc(nombre_raw)

                    # Crear o Actualizar Cliente
                    Clientes.objects.update_or_create(
                        cliente_id=cliente_id,
                        defaults={
                            'tipo_id': t_obj,
                            'nombre': n_nuevo.upper(),
                            'apellido': a_nuevo.upper(),
                            'fecha_nacimiento': date(1900, 1, 1),
                            'telefono': str(row.get('Telefono', ''))[:10],
                            'direccion': str(row.get('Direccion', ''))[:120].upper(),
                            'departamento': depto_bogota,
                            'municipio': mun_bogota,
                            'email': str(row.get('Correo', ''))[:120],
                            'estado': 'HABILITADO'
                        }
                    )
                    c_proc += 1
            except Exception as e:
                logger.error(f"Error cliente ID {row.get('IDENTIFICACION')}: {e}")
                c_err += 1

        # === CARGA DE MAESTROS DESDE HOJAS DE CRÉDITOS ===
        # Leemos las hojas de créditos solo para extraer Asesores y Aseguradoras únicos
        logger.info("=== CARGANDO MAESTROS (ASESORES/ASEGURADORAS) ===")
        for hoja in ["Creditos", "Creditos Nuevos"]:
            df_m = pd.read_excel(archivo_excel, sheet_name=hoja)
            df_m.columns = [str(c).upper().strip() for c in df_m.columns] # Normalizar columnas para el match
            
            # Extraer Asesores únicos
            if 'ASESOR' in df_m.columns:
                for nom in df_m['ASESOR'].dropna().unique():
                    Asesores.objects.get_or_create(asesor_id=generar_id_corto(str(nom)), defaults={'asesor_nombre': str(nom)[:30], 'asesor_estado': 'HABILITADO'})
            
            # Extraer Aseguradoras únicas
            if 'ASEGURADORA' in df_m.columns:
                for nom in df_m['ASEGURADORA'].dropna().unique():
                    Aseguradoras.objects.get_or_create(aseguradora_id=generar_id_corto(str(nom)), defaults={'aseguradora_nombre': str(nom)[:30], 'aseguradora_estado': 'HABILITADO'})

        logger.info(f"=== MIGRACIÓN DE MAESTROS FINALIZADA: {c_proc} clientes procesados ===")