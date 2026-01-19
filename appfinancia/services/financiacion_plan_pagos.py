'''
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
# Asegúrate de importar tus modelos correctamente
# from appfinancia.models import Financiacion, Financiacion_PlanPago, Financiacion_DetallePlanPago

# 1. Importaciones necesarias
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction

# 2. IMPORTANTE: Importa tus modelos (ajusta el nombre de la app si es necesario)
from appfinancia.models import Financiacion, Financiacion_PlanPago, Financiacion_DetallePlanPago
'''

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import os

from django.conf import settings
from django.db import transaction

from appfinancia.models import (
    Financiacion,
    Financiacion_PlanPago,
    Financiacion_DetallePlanPago,
)

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def f_plan_pagos_cuota_fija(solicitud_id):
    financiacion = Financiacion.objects.get(solicitud_id=solicitud_id)

    # 1️⃣ Extracción de datos
    valor_poliza = Decimal(str(financiacion.valor_prestamo or 0))
    valor_cuota_0 = Decimal(str(financiacion.valor_cuota_inicial or 0))
    valor_seguro_vida = Decimal(str(financiacion.valor_seguro_vida or 0))
    tasa = Decimal(str(financiacion.tasa or 0)) / Decimal("100")
    plazo = int(financiacion.numero_cuotas or 0)

    # 2️⃣ Cálculo Financiero
    saldo = valor_poliza - valor_cuota_0
    plan = []

    # Cuota 0 (La inicial que paga el cliente)
    plan.append({
        "n": 0,
        "cuota": valor_cuota_0 + valor_seguro_vida,
        "abono_capital": valor_cuota_0,
        "intereses": Decimal("0"),
        "saldo_capital": saldo
    })

    # Cálculo de la cuota base francesa sobre el saldo restante
    if saldo > 0 and tasa > 0 and plazo > 0:
        # FÓRMULA: R = (P * i) / (1 - (1 + i)^-n)
        cuota_base = (saldo * tasa) / (1 - (1 + tasa) ** (-plazo))
        cuota_base = cuota_base.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    else:
        cuota_base = Decimal("0")

    # Ciclo de amortización
    for n in range(1, plazo + 1):
        intereses = (saldo * tasa).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        abono_capital = cuota_base - intereses
        saldo -= abono_capital

        # Ajuste de última cuota por redondeo
        if n == plazo or saldo < 0:
            abono_capital += saldo
            saldo = Decimal("0")

        plan.append({
            "n": n,
            "cuota": cuota_base + valor_seguro_vida,
            "abono_capital": abono_capital,
            "intereses": intereses,
            "saldo_capital": saldo
        })

    resultado_plan = {
        "cliente": financiacion.nombre_completo,
        "cliente_id": financiacion.numero_documento,
        "poliza": financiacion.numero_poliza,
        "valor_poliza": valor_poliza,
        "valor_cuota_0": valor_cuota_0,
        "valor_seguro_vida": valor_seguro_vida,
        "plazo_meses": plazo,
        "plan": plan
    }

    return guardar_plan_pagos(financiacion, resultado_plan)

def guardar_plan_pagos(financiacion, resultado_plan):
    with transaction.atomic():
        # 🔥 CAMBIO CLAVE: Si ya existe un plan, lo borramos para generar el nuevo
        # Esto permite que si el usuario cambia el monto o la tasa, el plan se actualice
        Financiacion_PlanPago.objects.filter(financiacion=financiacion).delete()

        plan = Financiacion_PlanPago.objects.create(
            financiacion=financiacion,
            cliente=resultado_plan["cliente"],
            cliente_id=resultado_plan["cliente_id"],
            poliza=resultado_plan["poliza"],
            valor_poliza=resultado_plan["valor_poliza"],
            valor_cuota_0=resultado_plan["valor_cuota_0"],
            valor_seguro_vida=resultado_plan["valor_seguro_vida"],
            tasa_mensual=financiacion.tasa,
            plazo_meses=resultado_plan["plazo_meses"],
            aprobado=False
        )

        detalles = [
            Financiacion_DetallePlanPago(
                plan_pago=plan,
                numero_cuota=fila["n"],
                valor_cuota=fila["cuota"],
                abono_capital=fila["abono_capital"],
                intereses=fila["intereses"],
                saldo_capital=fila["saldo_capital"]
            )
            for fila in resultado_plan["plan"]
        ]

        Financiacion_DetallePlanPago.objects.bulk_create(detalles)
        return plan