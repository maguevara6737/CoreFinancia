from django.http import HttpResponse
from openpyxl import Workbook
from decimal import Decimal


def generar_reporte_pagos_excel(queryset):
    """
    Genera un archivo Excel con los pagos seleccionados
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Pagos"

    # ==========================
    # ENCABEZADOS
    # ==========================
    headers = [
        "Pago ID",
        "Fecha Pago",
        "Cliente",
        "Préstamo",
        "Valor Pago",
        "Estado Pago",
        "Conciliación",
        "Clase Movimiento",
        "Lote PSE",
    ]
    ws.append(headers)

    # ==========================
    # DATOS
    # ==========================
    for pago in queryset:
        ws.append([
            pago.pago_id,
            pago.fecha_pago.strftime("%Y-%m-%d") if pago.fecha_pago else "",
            str(pago.cliente_id_real or ""),
            str(pago.prestamo_id_real or ""),
            float(pago.valor_pago or Decimal("0")),
            pago.estado_pago,
            pago.estado_conciliacion,
            pago.clase_movimiento,
            pago.lote_pse,
        ])

    # ==========================
    # RESPUESTA HTTP
    # ==========================
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="reporte_pagos.xlsx"'

    wb.save(response)
    return response
