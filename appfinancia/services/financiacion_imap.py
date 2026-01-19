# financiacion_imap.py
'''
import imaplib
from django.conf import settings

import email
from email.header import decode_header
from datetime import datetime
from django.utils import timezone

from appfinancia.models import Financiacion
from bs4 import BeautifulSoup
'''

import imaplib
import email
from email.header import decode_header
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
from bs4 import BeautifulSoup

from appfinancia.models import Financiacion

'''
from appfinancia.services.financiacion_utils import (
    parsear_cuerpo,
    generar_financiacion_id,
    extraer_adjuntos,
    clasificar_adjunto,
    f_buscar_cliente,
)
'''


'''
# ================================
# CONFIGURACIÓN DEL CORREO - Código movido al settings.py
# ================================
IMAP_HOST = "imap.gmail.com"
EMAIL_USER = "financia.seguros.pruebas@gmail.com"
EMAIL_PASSWORD = "vbxstaiyahvelaxw"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "financia.seguros.pruebas@gmail.com"
EMAIL_HOST_PASSWORD = "CLAVE_DE_APLICACION_GMAIL"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
'''



def procesar_emails():
    """
    Conecta al correo, lee emails no procesados
    y crea registros en la tabla Financiacion
    """

    print("📨 Conectando al servidor IMAP...")

    # ================================
    # CONEXIÓN IMAP (DESDE settings.py)
    # ================================
    
    mail = imaplib.IMAP4_SSL(settings.IMAP_HOST)
    mail.login(
        settings.EMAIL_HOST_USER,
        settings.EMAIL_HOST_PASSWORD
    )
    mail.select("inbox")


    # ================================
    # BUSCAR CORREOS NO LEÍDOS
    # ================================
    status, messages = mail.search(None, "(UNSEEN)")

    if status != "OK":
        print("❌ No se pudieron leer los correos")
        mail.logout()
        return

    email_ids = messages[0].split()

    # ✅ Evitar errores cuando no hay correos
    if not email_ids:
        print("📭 No hay correos nuevos para procesar")
        mail.logout()
        print("✔ Proceso de correos finalizado (sin novedades)")
        return

    print(f"📬 Correos encontrados: {len(email_ids)}")

    # ================================
    # PROCESAR CADA CORREO
    # ================================
    for email_id in email_ids:
        _, msg_data = mail.fetch(email_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # ----------------
        # DATOS DEL CORREO
        # ----------------
        message_id = msg.get("Message-ID")

        # Evitar duplicados
        if Financiacion.objects.filter(message_id=message_id).exists():
            print("⚠️ Correo ya procesado, se omite")
            continue

        subject, encoding = decode_header(msg.get("Subject"))[0]
        asunto = subject.decode(encoding) if isinstance(subject, bytes) else subject

        from_email = msg.get("From")
        fecha_email = msg.get("Date")

        try:
            fecha_solicitud = email.utils.parsedate_to_datetime(fecha_email)
        except Exception:
            fecha_solicitud = timezone.now()

        # ----------------
        # CUERPO DEL MENSAJE
        # ----------------
        cuerpo = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                cuerpo = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8",
                    errors="ignore"
                )
                break

            elif content_type == "text/html" and not cuerpo:
                html = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8",
                    errors="ignore"
                )
                soup = BeautifulSoup(html, "html.parser")
                cuerpo = soup.get_text(separator="\n")

        datos = parsear_cuerpo(cuerpo)

        if not datos:
            print("⚠️ No se pudo parsear el cuerpo del correo, se omite")
            continue

        print("📄 DATOS PARSEADOS:", datos)
        print(cuerpo[:1000])  # primeros 1000 caracteres

        # ----------------
        # VALIDACIONES CLIENTE
        # ----------------
        v_numero_documento = datos.get("numero_documento", "").strip()
        v_cliente_nuevo, v_cliente_vetado = f_buscar_cliente(v_numero_documento)

        # ----------------
        # CREAR FINANCIACIÓN
        # ----------------
        financiacion = Financiacion.objects.create(
            message_id=message_id,
            financiacion_id=generar_financiacion_id(asunto),
            email_origen=from_email,
            asunto=asunto,
            fecha_solicitud=fecha_solicitud,

            nombre_completo=datos.get("nombre_completo", ""),
            tipo_documento=datos.get("tipo_documento", ""),
            numero_documento=v_numero_documento,
            telefono=datos.get("telefono", ""),
            correo_electronico="financia.seguros.pruebas@gmail.com",
            asesor=datos.get("asesor", ""),
            agencia=datos.get("agencia", ""),
            numero_cuotas=datos.get("numero_cuotas", ""),

            cliente_nuevo=v_cliente_nuevo,
            cliente_vetado=v_cliente_vetado,
        )

        # ----------------
        # ADJUNTOS
        # ----------------
        adjuntos = extraer_adjuntos(msg)

        for filename, contenido in adjuntos:
            tipo = clasificar_adjunto(filename)

            if tipo == "cedula":
                financiacion.adjunta_cedula.save(
                    filename,
                    ContentFile(contenido),
                    save=False
                )
                financiacion.adjunta_documento_identificacion = True

            elif tipo == "poliza":
                financiacion.adjunta_poliza.save(
                    filename,
                    ContentFile(contenido),
                    save=False
                )
                financiacion.adjunta_poliza_seguro = True

            elif tipo == "segurovida":
                financiacion.adjunta_segurovida.save(
                    filename,
                    ContentFile(contenido),
                    save=False
                )
                financiacion.adjunta_seguro_vida = True

        # Guardar una sola vez
        financiacion.save()
        print(f"✅ Solicitud creada: {datos.get('nombre_completo')}")

    mail.logout()
    print("✔ Proceso de correos finalizado")


# ================================
# FUNCIONES AUXILIARES
# ================================
import re

def generar_financiacion_id(asunto):
    """
    Extrae el número de solicitud desde el asunto del correo.
    Ejemplo:
    'Nueva solicitud de crédito @2376 para Financia Seguros'
    => FIN-2376
    """

    if not asunto:
        return None

    # Busca patrón @NUMERO
    match = re.search(r'@(\d+)', asunto)

    if match:
        numero = match.group(1)
        return f"FIN-{numero}"

    # Fallback seguro si no viene el número
    return f"FIN-{int(datetime.now().timestamp())}"


import re


def parsear_cuerpo(texto):
    """
    Parsea correos con estructura:
    Etiqueta
    VALOR
    """
    datos = {}

    if not texto:
        return datos

    # Normalizar líneas: quitar vacías
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    mapa = {
        "nombre completo": "nombre_completo",
        "tipo de documento": "tipo_documento",
        "número de documento": "numero_documento",
        "numero de documento": "numero_documento",
        "número de contacto": "telefono",
        "asesor": "asesor",
        "agencia": "agencia",
        "correo electrónico": "correo_electronico",
        "correo electronico": "correo_electronico",
        "número de cuotas": "numero_cuotas",
        "adjunta cédula": "adjunta_cedula",
        "adjunta cedula": "adjunta_cedula",
        "adjunta póliza": "adjunta_poliza",
        "adjunta poliza": "adjunta_poliza",
    }

    i = 0
    while i < len(lineas) - 1:
        linea = lineas[i]

        # 1. Quitar numeración: "1. ", "10. ", etc
        linea = re.sub(r'^\d+\.\s*', '', linea)

        # 2. Quitar paréntesis: "(.pdf)"
        linea_limpia = re.sub(r'\(.*?\)', '', linea)

        # 3. Normalizar
        linea_key = linea_limpia.lower().strip()

        for etiqueta, campo in mapa.items():
            if etiqueta in linea_key:
                valor = lineas[i + 1].strip()

                # Limpiar correo tipo markdown
                if campo == "correo_electronico":
                    match = re.search(r'[\w\.-]+@[\w\.-]+', valor)
                    valor = match.group(0) if match else valor

                datos[campo] = valor
                i += 2
                break
        else:
            i += 1

    return datos


# ================================
# Buscar el cliente
# ================================
from appfinancia.models import Clientes


def f_buscar_cliente(p_cliente_id):
    cliente_nuevo = "SI"
    cliente_vetado = "NO"

    if not p_cliente_id:
        return cliente_nuevo, cliente_vetado

    cliente = Clientes.objects.filter(cliente_id=p_cliente_id).first()

    if cliente:
        cliente_nuevo = "SI"

        if cliente.estado == "DESHABILITADO":
            cliente_vetado = "SI"

    return cliente_nuevo, cliente_vetado


# ================================
# procesar adjuntos
# ================================
from django.core.files.base import ContentFile
import os


def clasificar_adjunto(filename):
    """
    Retorna: 'cedula' | 'poliza' | 'segurovida' | None
    """
    if not filename:
        return None

    name = filename.lower()

    if any(k in name for k in ["cedula", "cédula", "cc", "documento", "identificacion"]):
        return "cedula"

    if any(k in name for k in ["poliza", "póliza", "seguro"]):
        return "poliza"

    if any(k in name for k in ["vida", "segurovida", "life"]):
        return "segurovida"

    return None

def extraer_adjuntos(msg):
    """
    Retorna lista de tuplas:
    [(filename, content_bytes)]
    """
    adjuntos = []

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))

        if "attachment" in content_disposition:
            filename = part.get_filename()

            if filename:
                payload = part.get_payload(decode=True)
                adjuntos.append((filename, payload))

    return adjuntos
