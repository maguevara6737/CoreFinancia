from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP
import os

from appfinancia.models import (
    Financiacion_PlanPago,
    Financiacion_DetallePlanPago
)


def f_generar_pdf_plan_pagos(solicitud_id):

    plan = Financiacion_PlanPago.objects.get(
        financiacion=solicitud_id
    )

    detalle = (
        Financiacion_DetallePlanPago.objects
        .filter(plan_pago=plan)
        .order_by("numero_cuota")
    )

    carpeta = os.path.join(
        settings.MEDIA_ROOT,
        "financiacion/aprobacion"
    )
    os.makedirs(carpeta, exist_ok=True)

    nombre_archivo = (
        f"PLAN DE PAGOS - {plan.cliente}"
        f"-POLIZA-{plan.poliza}.pdf"
    )

    ruta = os.path.join(carpeta, nombre_archivo)

    c = canvas.Canvas(ruta, pagesize=LETTER)
    width, height = LETTER
    y = height - 50

    # =============================
    # ENCABEZADO
    # =============================
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "PLAN DE PAGOS")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Cliente")
    c.drawString(120, y, f": {plan.cliente} ({plan.cliente_id})")
    y -= 15

    c.drawString(50, y, f"Póliza")
    c.drawString(120, y, f": {plan.poliza}")
    y -= 15

    # =============================
    # DATOS FINANCIEROS
    # =============================
    c.setFont("Helvetica", 9)

    c.drawString(50, y, f"Valor póliza")
    c.drawString(120, y, f": {formato_moneda_2(plan.valor_poliza)}")
    y -= 12

    c.drawString(50, y, f"Cuota inicial")
    c.drawString(120, y, f": {formato_moneda_2(plan.valor_cuota_0)}")
    y -= 12

    c.drawString(50, y, f"Seguro de vida")
    c.drawString(120, y, f": {formato_moneda_2(plan.valor_seguro_vida)}")
    y -= 12

    c.drawString(50, y, f"Cuotas")
    c.drawString(120, y, f": {plan.plazo_meses} cuotas")
    y -= 20

    # =============================
    # ENCABEZADOS
    # =============================
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "N")
    c.drawRightString(140, y, "Cuota")
    c.drawRightString(240, y, "Abono Capital")
    c.drawRightString(340, y, "Intereses")
    c.drawRightString(450, y, "Saldo Capital")
    y -= 15

    c.setFont("Helvetica", 9)
    
    # Posiciones X (alineación derecha para números)
    COL_N = 60
    COL_CUOTA = 140
    COL_ABONO = 240
    COL_INTERES = 340
    COL_SALDO = 450


    for fila in detalle:
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
        
        '''
        c.drawString(50, y, str(fila.numero_cuota))
        c.drawRightString(130, y, f"{fila.valor_cuota}")
        c.drawRightString(240, y, f"{fila.abono_capital}")
        c.drawRightString(340, y, f"{fila.intereses}")
        c.drawRightString(450, y, f"{fila.saldo_capital}")
        '''
        
        # Valores monetarios alineados a la derecha
        c.drawString(50, y, str(fila.numero_cuota))
        c.drawRightString(COL_CUOTA, y, formato_moneda_2(fila.valor_cuota))
        c.drawRightString(COL_ABONO, y, formato_moneda_2(fila.abono_capital))
        c.drawRightString(COL_INTERES, y, formato_moneda_2(fila.intereses))
        c.drawRightString(COL_SALDO, y, formato_moneda_2(fila.saldo_capital))
        
        y -= 12

    c.save()

    return ruta
    
#Dar formato
def formato_moneda_2(valor):
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${valor:,.2f}"

