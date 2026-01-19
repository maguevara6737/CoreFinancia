# appfinancia/services/financiacion_correo_aprobacion.py

import os
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from appfinancia.models import Financiacion


def f_correo_aprobacion(solicitud_id):
    """
    Envía correo de aprobación de financiación con:
    - Plantilla HTML + TXT
    - Adjuntos fijos
    - Plan de Pagos generado
    """

    try:
        financiacion = Financiacion.objects.get(solicitud_id=solicitud_id)
    except Financiacion.DoesNotExist:
        raise Exception("No existe la solicitud de financiación")

    # ================================
    # CONFIGURACIÓN DEL CORREO
    # ================================
    from_email = settings.EMAIL_HOST_USER

    to_email = [financiacion.correo_electronico]

    cc_emails = [
        financiacion.email_origen,
        "miguel.guevara.s@gmail.com",
        "financia.seguros.pruebas@gmail.com",
        #"renovaciones@tuseguroproteccion.com",
        #"ccastrillon@tuseguroproteccion.com",
    ]

    subject = (
        f"{financiacion.numero_poliza} - FINANCIACIÓN - "
        f"{financiacion.nombre_completo}"
    )

    # ================================
    # CONTEXTO PARA PLANTILLAS
    # ================================
    context = {
        "financiacion": financiacion
    }

    text_content = render_to_string(
        "emails/financiacion_aprobacion.txt",
        context
    )

    html_content = render_to_string(
        "emails/financiacion_aprobacion.html",
        context
    )

    # ================================
    # CREAR EMAIL
    # ================================
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=to_email,
        cc=cc_emails,
    )

    email.attach_alternative(html_content, "text/html")

    # ================================
    # ADJUNTOS FIJOS
    # ================================
    adjuntos_fijos = [
        "1. AUTORIZACIÓN TRATAMIENTO DE DATOS PERSONALES.pdf",
        "2. QR FINANCIA SEGURO SAS.pdf",
        "3. LLAVE BRE-B FINANCIA SEGURO SAS.pdf",
    ]

    ruta_base_adjuntos = os.path.join(
        settings.MEDIA_ROOT,
        "financiacion",
        "aprobacion"
    )

    for archivo in adjuntos_fijos:
        ruta = os.path.join(ruta_base_adjuntos, archivo)
        if os.path.exists(ruta):
            email.attach_file(ruta)

    # ================================
    # ADJUNTAR PLAN DE PAGOS
    # ================================
    nombre_plan = (
        f"PLAN DE PAGOS - {financiacion.nombre_completo}"
        f"-POLIZA-{financiacion.numero_poliza}.pdf"
    )

    ruta_plan = os.path.join(
        settings.MEDIA_ROOT,
        "financiacion",
        "aprobacion",
        nombre_plan
    )

    if os.path.exists(ruta_plan):
        email.attach_file(ruta_plan)
    else:
        print("⚠️ Plan de pagos no encontrado:", ruta_plan)

    # ================================
    # ENVIAR CORREO
    # ================================
    email.send(fail_silently=False)

    return True
