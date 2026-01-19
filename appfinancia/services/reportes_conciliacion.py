from openpyxl import Workbook
from django.http import HttpResponse
from appfinancia.models import InBox_PagosDetalle
from django.utils.timezone import is_aware, make_naive


def excel_datetime(value):
    """
    Convierte datetime con timezone a naive (Excel-safe)
    """
    if value and is_aware(value):
        return make_naive(value)
    return value


def generar_reporte_conciliacion_excel(request):
    qs = InBox_PagosDetalle.objects.exclude(
        clase_movimiento="EXCLUIDO"
    )

    # 🔎 Filtros permitidos
    filtros = {}

    if request.GET.get("nombre_archivo_id"):
        filtros["nombre_archivo_id"] = request.GET["nombre_archivo_id"]

    if request.GET.get("lote_pse"):
        filtros["lote_pse"] = request.GET["lote_pse"]

    if request.GET.get("pago_id"):
        filtros["pago_id"] = request.GET["pago_id"]

    if request.GET.get("fecha_carga_archivo__gte"):
        filtros["fecha_carga_archivo__gte"] = request.GET["fecha_carga_archivo__gte"]

    if request.GET.get("fecha_carga_archivo__lte"):
        filtros["fecha_carga_archivo__lte"] = request.GET["fecha_carga_archivo__lte"]

    qs = qs.filter(**filtros).order_by(
        "conciliacion_id",
        "lote_pse",
        "pago_id",
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Conciliación"

    headers = [
        "Num Conciliacion",
        "Fecha Conciliación",
        "Estado Conciliación",
        "Archivo",
        "Fecha Carga",
        "Lote PSE",
        "Pago ID",
        "Valor Pago",
        "Clase Movimiento",
        "Fecha Pago",
        "Estado Pago",
        "Cliente",
        "Préstamo",
        "Fragmento de",
        "Estado Fragmentación",
        "Ref Bancaria",
        "Ref Cliente 1",
        "Ref Cliente 2",
        "Ref Cliente 3",
    ]
    ws.append(headers)

    for p in qs:
        ws.append([
            p.conciliacion_id,
            excel_datetime(p.fecha_conciliacion),
            p.estado_conciliacion,
            str(p.nombre_archivo_id),
            excel_datetime(p.fecha_carga_archivo),
            p.lote_pse,
            p.pago_id,
            p.valor_pago,
            p.clase_movimiento,
            excel_datetime(p.fecha_pago),          # ✅ CORREGIDO
            p.estado_pago,
            p.cliente_id_real_id,
            p.prestamo_id_real_id,
            p.fragmento_de,
            p.estado_fragmentacion,
            p.ref_bancaria,
            p.ref_cliente_1,
            p.ref_cliente_2,
            p.ref_cliente_3,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = "attachment; filename=reporte_conciliacion.xlsx"
    wb.save(response)

    return response
