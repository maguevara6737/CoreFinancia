#from django.shortcuts import render
#----------------------------------------------------


#--------------------------------------------------------------
# Create your views here.
# En views.py de tu app
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpRequest

def login_view(request: HttpRequest):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html', {'usuario': request.user})


#2025/11/17 para ventana emergente a comentarios
# appfinancia/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import permission_required, user_passes_test
from .models import Desembolsos, Comentarios_Prestamos, Comentarios
from django.http import HttpResponse

###@csrf_exempt <-- suspedido 2025-11-17
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET","POST"])
def add_comentario_prestamo(request, prestamo_id):
    try:
        desembolso = Desembolsos.objects.get(prestamo_id=prestamo_id)
        comentario_cat_id = request.POST.get('comentario_catalogo')

        if not comentario_cat_id:
            return JsonResponse({'error': 'Debe seleccionar un comentario del catálogo.'}, status=400)

        # Obtener comentario habilitado
        try:
            comentario_cat = Comentarios.objects.get(
                pk=comentario_cat_id,
                estado='HABILITADO'
            )
        except Comentarios.DoesNotExist:
            return JsonResponse({'error': 'Comentario no válido o no habilitado.'}, status=400)

        # Crear comentario
        comentario = Comentarios_Prestamos.objects.create(
            prestamo=desembolso,
            comentario_catalogo=comentario_cat,
            creado_por=request.user
            # ¡comentario="" por defecto (blank=True)!
        )

        return JsonResponse({
            'success': True,
            'comentario': {
                'id': comentario.numero_comentario,
                'catalogo': str(comentario_cat),
                'creado_por': str(comentario.creado_por),
                'fecha': comentario.fecha_comentario.strftime('%Y-%m-%d %H:%M')
            }
        })

    except Desembolsos.DoesNotExist:
        return JsonResponse({'error': 'Desembolso no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    #2025-11-18 - vista personalizada para plan pagos
    # appfinancia/views.py
# En appfinancia/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Prestamos, Historia_Prestamos, Desembolsos
from collections import defaultdict

# appfinancia/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.db.models import Max
from .models import Prestamos, Historia_Prestamos, Conceptos_Transacciones


@staff_member_required
def plan_de_pagos_view(request, prestamo_id):
    """
    Vista personalizada que muestra el plan de pagos de un préstamo en una sola página.
    - Filtra solo cuotas reales (numero_cuota > 0 y conceptos válidos).
    - Agrega datos clave en el contexto para el encabezado.
    """
    prestamo = get_object_or_404(Prestamos, prestamo_id=prestamo_id)

    # === 1. Obtener conceptos a EXCLUIR ===
    try:
        causac_concepto = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
        excedente_concepto = Conceptos_Transacciones.objects.get(concepto_id="PAGOEXC")
    except Conceptos_Transacciones.DoesNotExist:
        # Si no existen, usamos IDs inválidos para no excluir nada
        causac_concepto = excedente_concepto = None

    # === 2. Filtrar SOLO cuotas reales ===
    transacciones = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        numero_cuota__gt=0  # Solo cuotas con número > 0
    ).exclude(
        concepto_id__in=[causac_concepto, excedente_concepto]
    ).select_related(
        'concepto_id'
    ).order_by(
        'numero_cuota', 'fecha_vencimiento'
    )

    # === 3. Agrupar transacciones por cuota ===
    plan = []
    for t in transacciones:
        clave = (t.numero_cuota, t.fecha_vencimiento)
        concepto_real = t.concepto_id.concepto_id if t.concepto_id else None

        # Inicializar valores
        valor_capital = valor_intereses = valor_seguro = valor_fee = 0.0

        if concepto_real == "PLANCAP":
            valor_capital = float(t.monto_transaccion)
        elif concepto_real == "PLANINT":
            valor_intereses = float(t.monto_transaccion)
        elif concepto_real == "PLANSEG":
            valor_seguro = float(t.monto_transaccion)
        elif concepto_real == "PLANGTO":
            valor_fee = float(t.monto_transaccion)
        else:
            # Si es un concepto no manejado, omitir (no agregar ceros)
            continue

        # Buscar si ya existe la cuota en el plan
        encontrado = False
        for item in plan:
            if item['clave'] == clave:
                item['capital'] += valor_capital
                item['intereses'] += valor_intereses
                item['seguro'] += valor_seguro
                item['fee'] += valor_fee
                encontrado = True
                break

        if not encontrado:
            plan.append({
                'clave': clave,
                'cuota': t.numero_cuota,
                'fecha_vencimiento': t.fecha_vencimiento,
                'capital': valor_capital,
                'intereses': valor_intereses,
                'seguro': valor_seguro,
                'fee': valor_fee,
            })

    # Calcular total de cada cuota
    for item in plan:
        item['total_cuota'] = item['capital'] + item['intereses'] + item['seguro'] + item['fee']

    # === 4. Calcular datos para el encabezado ===
    # Fecha de vencimiento final
    fecha_vencimiento_final = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        numero_cuota__gt=0
    ).aggregate(Max('fecha_vencimiento'))['fecha_vencimiento__max']

    # Tasa mensual
    tasa_mensual = float(prestamo.tasa) / 12 if prestamo.tasa else 0.0

    # Saldo del préstamo (después de la cuota 1)
    saldo_prestamo = float(prestamo.valor - prestamo.valor_cuota_1)

    context = {
        'prestamo': prestamo,
        'plan': plan,
        'fecha_desembolso': prestamo.fecha_desembolso,
        'fecha_vencimiento_final': fecha_vencimiento_final,
        'tasa_mensual': tasa_mensual,
        'plazo_en_meses': prestamo.plazo_en_meses,
        'saldo_prestamo': saldo_prestamo,
    }
    return render(request, 'appfinancia/plan_de_pagos.html', context)

#__________________________________________________________________________________________________________________________
# appfinancia/views.py

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from decimal import Decimal
from .models import Prestamos, Historia_Prestamos, Conceptos_Transacciones


@staff_member_required
def exportar_historia_xlsx(request, prestamo_id):
    """
    Exporta el plan de pagos a Excel con el mismo formato y datos que la vista HTML.
    - Filtra solo cuotas reales (numero_cuota > 0, sin CAUSAC/PAGOEXC).
    - Incluye encabezado con datos clave del préstamo.
    """
    prestamo = get_object_or_404(Prestamos, prestamo_id=prestamo_id)

    # === 1. Obtener conceptos a EXCLUIR ===
    try:
        causac_concepto = Conceptos_Transacciones.objects.get(concepto_id="CAUSAC")
        excedente_concepto = Conceptos_Transacciones.objects.get(concepto_id="PAGOEXC")
    except Conceptos_Transacciones.DoesNotExist:
        causac_concepto = excedente_concepto = None

    # === 2. Filtrar SOLO cuotas reales ===
    transacciones = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        numero_cuota__gt=0
    ).exclude(
        concepto_id__in=[causac_concepto, excedente_concepto]
    ).select_related(
        'concepto_id'
    ).order_by(
        'numero_cuota', 'fecha_vencimiento'
    )

    # === 3. Agrupar transacciones (mismo lógica que la vista HTML) ===
    plan = {}
    for t in transacciones:
        clave = (t.numero_cuota, t.fecha_vencimiento)
        concepto_real = t.concepto_id.concepto_id if t.concepto_id else None

        if clave not in plan:
            plan[clave] = {
                'cuota': t.numero_cuota,
                'fecha_vencimiento': t.fecha_vencimiento,
                'capital': Decimal('0.00'),
                'intereses': Decimal('0.00'),
                'seguro': Decimal('0.00'),
                'fee': Decimal('0.00'),
            }

        if concepto_real == "PLANCAP":
            plan[clave]['capital'] += t.monto_transaccion
        elif concepto_real == "PLANINT":
            plan[clave]['intereses'] += t.monto_transaccion
        elif concepto_real == "PLANSEG":
            plan[clave]['seguro'] += t.monto_transaccion
        elif concepto_real == "PLANGTO":
            plan[clave]['fee'] += t.monto_transaccion

    # Convertir a lista ordenada
    plan_ordenado = sorted(plan.values(), key=lambda x: (x['fecha_vencimiento'], x['cuota']))

    # === 4. Datos para el encabezado ===
    fecha_vencimiento_final = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        numero_cuota__gt=0
    ).aggregate(Max('fecha_vencimiento'))['fecha_vencimiento__max']

    tasa_mensual = float(prestamo.tasa) / 12 if prestamo.tasa else 0.0
    saldo_prestamo = float(prestamo.valor - prestamo.valor_cuota_1)

    # === 5. Crear libro de Excel ===
    wb = Workbook()
    ws = wb.active
    ws.title = "Plan de Pagos"

    # Estilos
    bold_font = Font(bold=True)
    header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
    title_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
    white_font = Font(color="FFFFFF", bold=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal="center")

    # === ENCABEZADO ===
    row = 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    ws.cell(row=row, column=1, value="PLAN DE PAGOS").font = white_font
    ws.cell(row=row, column=1).fill = title_fill
    ws.cell(row=row, column=1).alignment = center_align
    row += 2

    # Datos del préstamo
    datos_prestamo = [
        ("Préstamo ID", f"{prestamo.prestamo_id.prestamo_id}"),
        ("Cliente", f"{prestamo.prestamo_id.cliente_id.nombre} {prestamo.prestamo_id.cliente_id.apellido}"),
        ("Desembolso", prestamo.fecha_desembolso.strftime("%Y-%m-%d") if prestamo.fecha_desembolso else "N/A"),
        ("Vencimiento Final", fecha_vencimiento_final.strftime("%Y-%m-%d") if fecha_vencimiento_final else "N/A"),
        ("Tasa Mensual", f"{tasa_mensual:.4f}%"),
        ("Plazo (meses)", prestamo.plazo_en_meses),
        ("Saldo Préstamo", f"${saldo_prestamo:,.2f}"),
    ]

    for label, value in datos_prestamo:
        ws.cell(row=row, column=1, value=label).font = bold_font
        ws.cell(row=row, column=2, value=value)
        row += 1

    row += 1

    # === ENCABEZADO DE LA TABLA ===
    headers = ["Cuota", "Fecha Venc.", "Total Cuota", "Capital", "Intereses", "Seguro", "Fee"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = white_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border

    # === DATOS DE LA TABLA ===
    row += 1
    for item in plan_ordenado:
        total = item['capital'] + item['intereses'] + item['seguro'] + item['fee']
        ws.cell(row=row, column=1, value=item['cuota'])
        ws.cell(row=row, column=2, value=item['fecha_vencimiento'].strftime("%Y-%m-%d"))
        ws.cell(row=row, column=3, value=float(total)).number_format = '#,##0.00'
        ws.cell(row=row, column=4, value=float(item['capital'])).number_format = '#,##0.00'
        ws.cell(row=row, column=5, value=float(item['intereses'])).number_format = '#,##0.00'
        ws.cell(row=row, column=6, value=float(item['seguro'])).number_format = '#,##0.00'
        ws.cell(row=row, column=7, value=float(item['fee'])).number_format = '#,##0.00'
        row += 1

    # Ajustar ancho de columnas
    for col in range(1, 8):
        ws.column_dimensions[chr(64 + col)].width = 15

    # === RESPUESTA HTTP ===
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=plan_pagos_prestamo_{prestamo.prestamo_id.prestamo_id}.xlsx'
    wb.save(response)
    return response

######################################
#Fragmentación de pagos
######################################
# appfinancia/views.py (añadir al final)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .forms import FragmentacionForm
from .models import InBox_PagosDetalle

def fragmentar_pago(request, pago_id):
    """
    Fragmenta un InBox_PagosDetalle (pago padre) en 2..6 hijos.
    """
    pago = get_object_or_404(InBox_PagosDetalle, pago_id=pago_id)

    # Opcional: exigir que esté en estado A_FRAMENTAR
    if pago.estado_fragmentacion != "A_FRAMENTAR":
        messages.warning(request, "El pago seleccionado no está marcado como 'A_FRAMENTAR'. Procediendo de todas formas.")

    if request.method == "POST":
        form = FragmentacionForm(request.POST, pago_padre=pago)
        if form.is_valid():
            data = form.cleaned_data
            hijos_creados = 0
            try:
                with transaction.atomic():
                    for letter in ("A","B","C","D","E","F"):
                        prest = data.get(f"prestamo_{letter}")
                        val = data.get(f"valor_{letter}")
                        if prest and val:
                            # crear hijo heredando campo a campo (los más importantes)
                            hijo = InBox_PagosDetalle(
                                nombre_archivo_id = pago.nombre_archivo_id,
                                fecha_carga_archivo = pago.fecha_carga_archivo,
                                banco_origen = pago.banco_origen,
                                cuenta_bancaria = pago.cuenta_bancaria,
                                tipo_cuenta_bancaria = pago.tipo_cuenta_bancaria,
                                canal_red_pago = pago.canal_red_pago,
                                ref_bancaria = pago.ref_bancaria,
                                ref_red = pago.ref_red,
                                ref_cliente_1 = pago.ref_cliente_1,
                                ref_cliente_2 = pago.ref_cliente_2,
                                ref_cliente_3 = pago.ref_cliente_3,
                                estado_transaccion_reportado = pago.estado_transaccion_reportado,
                                clase_movimiento = pago.clase_movimiento,
                                estado_fragmentacion = "FRAGMENTADO",
                                cliente_id_reportado = pago.cliente_id_reportado,
                                prestamo_id_reportado = pago.prestamo_id_reportado,
                                cliente_id_real = pago.cliente_id_real,
                                prestamo_id_real = prest,
                                fecha_pago = pago.fecha_pago,
                                fecha_conciliacion = pago.fecha_conciliacion,
                                estado_pago = pago.estado_pago,
                                estado_conciliacion = pago.estado_conciliacion,
                                valor_pago = Decimal(str(val)),
                                observaciones = f"Fragmentado de pago {pago.pago_id}",
                                creado_por = request.user,
                                fragmento_de = pago.pago_id,
                            )
                            hijo.save()
                            hijos_creados += 1

                    # actualizar estado del padre
                    pago.estado_fragmentacion = "FRAGMENTADO"
                    pago.save()

                messages.success(request, f"Fragmentación exitosa: {hijos_creados} pagos hijos creados.")
                return redirect("/admin/appfinancia/inbox_pagosdetalle/")

            except Exception as e:
                # Si algo falla dentro del atomic, todo se revierte
                messages.error(request, f"Error al crear fragmentos: {e}")
        else:
            # errores de validación: caerán en la plantilla mostrando form.errors
            messages.error(request, "Errores en el formulario. Corrija y vuelva a intentar.")
    else:
        form = FragmentacionForm(pago_padre=pago)

    # Preparar lista de campos para la plantilla (ordenada A-F)
    letras = ("A","B","C","D","E","F")
    campos = []
    for letter in letras:
        campos.append({
            "letter": letter,
            "prestamo": form[f"prestamo_{letter}"],
            "valor": form[f"valor_{letter}"],
        })

    context = {
        "pago": pago,
        "form": form,
        "campos": campos,
    }
    return render(request, "appfinancia/fragmentacion_form.html", context)



#====================
#Regularizar pagps
#====================
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from .models import InBox_PagosDetalle
from .forms import RegularizarPagoForm


@staff_member_required
def regularizar_pago_view(request, pago_id):
    pago = get_object_or_404(InBox_PagosDetalle, pago_id=pago_id)

    if request.method == "POST":
        form = RegularizarPagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago regularizado correctamente.")
            return redirect(
                f"/admin/appfinancia/inbox_pagosdetalle/{pago_id}/change/"
            )
    else:
        form = RegularizarPagoForm(instance=pago)

    context = {
        "title": "Regularizar Pagos",
        "pago": pago,
        "form": form,
    }

    return render(request, "appfinancia/regularizar_pago.html", context)


#-------------------------------------para el estado de cuenta -------------------
# appfinancia/views.py

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from decimal import Decimal
import io

from .models import Prestamos, Fechas_Sistema, Historia_Prestamos, Conceptos_Transacciones


def estado_cuenta_view(request, prestamo_id):
    prestamo = get_object_or_404(Prestamos, prestamo_id=prestamo_id)
    cliente = prestamo.cliente_id

    fecha_sistema = Fechas_Sistema.objects.first()
    if not fecha_sistema:
        return HttpResponse("Error: No hay fecha de proceso definida.", status=500)
    fecha_corte = fecha_sistema.fecha_proceso_actual

    try:
        cap_concepto = Conceptos_Transacciones.objects.get(concepto_id="PLANCAP")
        int_concepto = Conceptos_Transacciones.objects.get(concepto_id="PLANINT")
        seg_concepto = Conceptos_Transacciones.objects.get(concepto_id="PLANSEG")
        fee_concepto = Conceptos_Transacciones.objects.get(concepto_id="PLANGTO")
    except Conceptos_Transacciones.DoesNotExist:
        return HttpResponse("Error: Conceptos de transacción no encontrados.", status=500)

    saldo_capital = saldo_intereses = saldo_seguro = fee = Decimal('0.00')

    cuotas_programadas = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        fecha_vencimiento__lte=fecha_corte,
        concepto_id__in=[cap_concepto, int_concepto, seg_concepto, fee_concepto]
    )

    for cuota in cuotas_programadas:
        if cuota.concepto_id == cap_concepto:
            saldo_capital += cuota.monto_transaccion
        elif cuota.concepto_id == int_concepto:
            saldo_intereses += cuota.monto_transaccion
        elif cuota.concepto_id == seg_concepto:
            saldo_seguro += cuota.monto_transaccion
        elif cuota.concepto_id == fee_concepto:
            fee += cuota.monto_transaccion

    suma_total_corte = saldo_capital + saldo_intereses + saldo_seguro + fee

    cuotas_atrasadas = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo,
        fecha_vencimiento__lt=fecha_corte,
        estado="PENDIENTE"
    ).exclude(concepto_id__concepto_id="CAUSAC")

    cantidad_cuotas_atrasadas = cuotas_atrasadas.count()
    dias_mora = 0
    capital_atrasado = intereses_atrasados = seguro_atrasado = fee_atrasado = Decimal('0.00')

    if cantidad_cuotas_atrasadas > 0:
        ultima_vencida = cuotas_atrasadas.order_by('-fecha_vencimiento').first()
        dias_mora = (fecha_corte - ultima_vencida.fecha_vencimiento).days
        for cuota in cuotas_atrasadas:
            if cuota.concepto_id == cap_concepto:
                capital_atrasado += cuota.monto_transaccion
            elif cuota.concepto_id == int_concepto:
                intereses_atrasados += cuota.monto_transaccion
            elif cuota.concepto_id == seg_concepto:
                seguro_atrasado += cuota.monto_transaccion
            elif cuota.concepto_id == fee_concepto:
                fee_atrasado += cuota.monto_transaccion

    suma_total_atrasado = capital_atrasado + intereses_atrasados + seguro_atrasado + fee_atrasado

    context = {
        'prestamo': prestamo,
        'cliente': cliente,
        'fecha_corte': fecha_corte,
        'saldo_capital': saldo_capital,
        'saldo_intereses': saldo_intereses,
        'saldo_seguro': saldo_seguro,
        'fee': fee,
        'suma_total_corte': suma_total_corte,
        'cantidad_cuotas_atrasadas': cantidad_cuotas_atrasadas,
        'dias_mora': dias_mora,
        'capital_atrasado': capital_atrasado,
        'intereses_atrasados': intereses_atrasados,
        'seguro_atrasado': seguro_atrasado,
        'fee_atrasado': fee_atrasado,
        'suma_total_atrasado': suma_total_atrasado,
        'prestamo_id_valor': prestamo.prestamo_id_id,  # ← el ID numérico
    }

    if request.GET.get('format') == 'excel':
        return generar_excel_estado_cuenta(context)
    else:
        html_content = render_to_string('appfinancia/estado_cuenta.html', context)
        return HttpResponse(html_content)


def generar_excel_estado_cuenta(context):
    wb = Workbook()
    ws = wb.active
    ws.title = "Estado de Cuenta"

    bold_font = Font(bold=True)
    ws.cell(row=1, column=1, value="Estado de Cuenta").font = bold_font
    ws.merge_cells('A1:D1')
    ws.cell(row=2, column=1, value=f"Prestamo ID: {context['prestamo'].prestamo_id}")
    ws.cell(row=3, column=1, value=f"Cliente: {context['cliente'].nombre} {context['cliente'].apellido}")

    row_num = 5
    ws.cell(row=row_num, column=1, value="A la fecha de corte").font = bold_font
    row_num += 1

    data = [
        ("Saldo capital:", context['saldo_capital']),
        ("Saldo Intereses:", context['saldo_intereses']),
        ("Saldo Seguro de vida:", context['saldo_seguro']),
        ("Fee:", context['fee']),
        ("Saldo Total:", context['suma_total_corte']),
    ]

    for label, value in data:
        ws.cell(row=row_num, column=1, value=label)
        ws.cell(row=row_num, column=2, value=value).number_format = '#,##0.00'
        row_num += 1

    row_num += 1
    ws.cell(row=row_num, column=1, value="Atrasado").font = bold_font
    row_num += 1

    data_atrasado = [
        ("Cantidad de cuotas atrasadas:", context['cantidad_cuotas_atrasadas']),
        ("Días de mora:", context['dias_mora']),
        ("Monto capital atrasado:", context['capital_atrasado']),
        ("Intereses atrasados:", context['intereses_atrasados']),
        ("Seguro atrasado:", context['seguro_atrasado']),
        ("Fee atrasado:", context['fee_atrasado']),
        ("Suma total valores atrasados:", context['suma_total_atrasado']),
    ]

    for label, value in data_atrasado:
        ws.cell(row=row_num, column=1, value=label)
        ws.cell(row=row_num, column=2, value=value).number_format = '#,##0.00'
        row_num += 1

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=estado_cuenta_{context["prestamo"].prestamo_id}.xlsx'
    return response
# appfinancia/views.py

#-------------------------------------------------------------


# admin.py
# appfinancia/admin.py
# appfinancia/views.py

# appfinancia/views.py

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib import admin  # ← ¡Importante para site_title y site_header!
from django.contrib.auth.decorators import permission_required
import csv
from io import StringIO
from .forms import ConsultaCausacionForm
from .utils import total_intereses_por_periodo


@permission_required('appfinancia.puede_consultar_causacion', raise_exception=True)
def consulta_causacion_view(request):
    """
    Vista equivalente a la que tenías en el ModelAdmin, pero ahora en views.py.
    """

    # === FUNCIÓN EQUIVALENTE A get_context ===
    def get_context(form, extra_data=None):
        context = {
            'form': form,
            'title': 'Reporte de Causación por Período',
            'site_title': admin.site.site_title,      # ← igual que antes
            'site_header': admin.site.site_header,    # ← igual que antes
            'has_permission': True,                   # ← ¡clave para evitar "acceso denegado"!
        }
        if extra_data:
            context.update(extra_data)
        return context

    # === LÓGICA PRINCIPAL (igual que antes, pero sin self) ===
    if request.method == 'POST':
        form = ConsultaCausacionForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            tipo_reporte = form.cleaned_data['tipo_reporte']

            try:
                resultado = total_intereses_por_periodo(fecha_inicio, fecha_fin)
                total_intereses = resultado['total_intereses']
                total_ajustes = resultado['total_ajustes']
                detalle = resultado['detalle_por_prestamo']
                num_prestamos = len(detalle)

                def formatear_monto_para_pantalla(valor):
                    return f"{valor:,.2f}"

                if tipo_reporte == 'pantalla':
                    context = get_context(form, {
                        'resultado_pantalla': {
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin,
                            'total_intereses': formatear_monto_para_pantalla(total_intereses),
                            'total_ajustes': formatear_monto_para_pantalla(total_ajustes),
                            'num_prestamos': num_prestamos,
                        }
                    })
                    messages.success(request, "Totales calculados exitosamente.")
                    return render(request, 'admin/consulta_causacion.html', context)

                elif tipo_reporte == 'excel':
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        'prestamo_id',
                        'periodo_inicio',
                        'periodo_fin',
                        'dias',
                        'saldo_inicial',
                        'tasa',
                        'interes_causado',
                        'ajuste_intrs_causacion',
                        'tipo_evento'
                    ])
                    for prestamo_id, periodos in detalle.items():
                        for p in periodos:
                            writer.writerow([
                                prestamo_id,
                                p['periodo_inicio'].strftime('%Y-%m-%d'),
                                p['periodo_fin'].strftime('%Y-%m-%d'),
                                p['dias'],
                                f"{p['saldo_inicial']:.2f}",
                                f"{p['tasa']:.6f}",
                                f"{p['interes_causado']:.2f}",
                                f"{p['ajuste_intrs_causacion']:.2f}",
                                p['tipo_evento']
                            ])

                    csv_content = output.getvalue()
                    output.close()

                    response = HttpResponse(csv_content, content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="causacion_detalle_{fecha_inicio}_{fecha_fin}.csv"'
                    messages.success(request, f"Reporte generado. Fechas: {fecha_inicio} a {fecha_fin} | Préstamos: {num_prestamos}")
                    return response

            except Exception as e:
                messages.error(request, f"Error al procesar: {str(e)}")
                context = get_context(form, {'error': str(e)})
                return render(request, 'admin/consulta_causacion.html', context)
        else:
            # Formulario no válido
            context = get_context(form)
            return render(request, 'admin/consulta_causacion.html', context)

    else:
        # GET: mostrar formulario vacío
        form = ConsultaCausacionForm()
        context = get_context(form)
        return render(request, 'admin/consulta_causacion.html', context)
    
#-------------------------- Balance de Operaciones ----------
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib import admin  # ← ¡Importante para site_title y site_header!
from django.contrib.auth.decorators import permission_required
import csv
from io import StringIO
from .forms import ConsultaCausacionForm
from .utils import total_intereses_por_periodo


@permission_required('appfinancia.puede_consultar_causacion', raise_exception=True)
def consulta_causacion_view(request):
    """
    Vista equivalente a la que tenías en el ModelAdmin, pero ahora en views.py.
    """

    # === FUNCIÓN EQUIVALENTE A get_context ===
    def get_context(form, extra_data=None):
        context = {
            'form': form,
            'title': 'Reporte de Causación por Período',
            'site_title': admin.site.site_title,      # ← igual que antes
            'site_header': admin.site.site_header,    # ← igual que antes
            'has_permission': True,                   # ← ¡clave para evitar "acceso denegado"!
        }
        if extra_data:
            context.update(extra_data)
        return context

    # === LÓGICA PRINCIPAL (igual que antes, pero sin self) ===
    if request.method == 'POST':
        form = ConsultaCausacionForm(request.POST)
        if form.is_valid():
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            tipo_reporte = form.cleaned_data['tipo_reporte']

            try:
                resultado = total_intereses_por_periodo(fecha_inicio, fecha_fin)
                total_intereses = resultado['total_intereses']
                total_ajustes = resultado['total_ajustes']
                detalle = resultado['detalle_por_prestamo']
                num_prestamos = len(detalle)

                def formatear_monto_para_pantalla(valor):
                    return f"{valor:,.2f}"

                if tipo_reporte == 'pantalla':
                    context = get_context(form, {
                        'resultado_pantalla': {
                            'fecha_inicio': fecha_inicio,
                            'fecha_fin': fecha_fin,
                            'total_intereses': formatear_monto_para_pantalla(total_intereses),
                            'total_ajustes': formatear_monto_para_pantalla(total_ajustes),
                            'num_prestamos': num_prestamos,
                        }
                    })
                    messages.success(request, "Totales calculados exitosamente.")
                    return render(request, 'admin/consulta_causacion.html', context)

                elif tipo_reporte == 'excel':
                    output = StringIO()
                    writer = csv.writer(output)
                    writer.writerow([
                        'prestamo_id',
                        'periodo_inicio',
                        'periodo_fin',
                        'dias',
                        'saldo_inicial',
                        'tasa',
                        'interes_causado',
                        'ajuste_intrs_causacion',
                        'tipo_evento'
                    ])
                    for prestamo_id, periodos in detalle.items():
                        for p in periodos:
                            writer.writerow([
                                prestamo_id,
                                p['periodo_inicio'].strftime('%Y-%m-%d'),
                                p['periodo_fin'].strftime('%Y-%m-%d'),
                                p['dias'],
                                f"{p['saldo_inicial']:.2f}",
                                f"{p['tasa']:.6f}",
                                f"{p['interes_causado']:.2f}",
                                f"{p['ajuste_intrs_causacion']:.2f}",
                                p['tipo_evento']
                            ])

                    csv_content = output.getvalue()
                    output.close()

                    response = HttpResponse(csv_content, content_type='text/csv')
                    response['Content-Disposition'] = f'attachment; filename="causacion_detalle_{fecha_inicio}_{fecha_fin}.csv"'
                    messages.success(request, f"Reporte generado. Fechas: {fecha_inicio} a {fecha_fin} | Préstamos: {num_prestamos}")
                    return response

            except Exception as e:
                messages.error(request, f"Error al procesar: {str(e)}")
                context = get_context(form, {'error': str(e)})
                return render(request, 'admin/consulta_causacion.html', context)
        else:
            # Formulario no válido
            context = get_context(form)
            return render(request, 'admin/consulta_causacion.html', context)

    else:
        # GET: mostrar formulario vacío
        form = ConsultaCausacionForm()
        context = get_context(form)
        return render(request, 'admin/consulta_causacion.html', context)
    
#-------------------------- Balance de Operaciones ----------
from .forms import BalanceOperacionesForm  # ← Agrega este import al inicio del archivo
from decimal import Decimal
from django.db.models import Sum, Count, Q
from .models import Prestamos, Desembolsos, Pagos, Historia_Prestamos, Clientes


def safe_excel_text(text):
    """Prepende comilla simple si el texto empieza con +, -, o =."""
    if isinstance(text, str) and text.strip() and text.strip()[0] in ('+', '-', '='):
        return "'" + text
    return text


def formatear_monto_excel(valor):
    """Formatea montos para Excel: 1,234,567.99 (coma miles, punto decimal)"""
    if valor is None:
        valor = Decimal('0.00')
    return f"{valor:,.2f}"


@permission_required('appfinancia.puede_consultar_causacion', raise_exception=True)
def balance_operaciones_view(request):
    """
    Vista para el Balance de Operaciones.
    """
    
    def get_context(form, extra_data=None):
        context = {
            'form': form,
            'title': 'Balance de Operaciones',
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'has_permission': True,
        }
        if extra_data:
            context.update(extra_data)
        return context

    def formatear_monto_pantalla(valor):
        """Formatea montos con , para miles y . para decimales (solo para HTML)"""
        if valor is None:
            valor = Decimal('0.00')
        return f"{valor:,.2f}"

    if request.method == 'POST':
        form = BalanceOperacionesForm(request.POST)
        if form.is_valid():
            fecha_corte = form.cleaned_data['fecha_corte']
            tipo_reporte = request.POST.get('tipo_reporte', 'pantalla')

            try:
                # === SALDOS DE CAPITAL ===
                from datetime import timedelta
                fecha_anterior = fecha_corte - timedelta(days=1)
                
                total_desembolsado_hasta_ayer = Desembolsos.objects.filter(
                    fecha_desembolso__lte=fecha_anterior
                ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
                
                total_pagado_hasta_ayer = Pagos.objects.filter(
                    fecha_pago__lte=fecha_anterior,
                    estado_pago='aplicado'
                ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
                
                saldo_anterior_valor = total_desembolsado_hasta_ayer - total_pagado_hasta_ayer
                saldo_anterior_cant = Prestamos.objects.filter(
                    fecha_desembolso__lte=fecha_anterior
                ).count()

                # Desembolsados HOY
                desembolsos_hoy = Desembolsos.objects.filter(fecha_desembolso=fecha_corte)
                desembolsos_hoy_valor = desembolsos_hoy.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
                desembolsos_hoy_cant = desembolsos_hoy.count()

                # Pagos HOY
                pagos_hoy = Pagos.objects.filter(fecha_pago=fecha_corte, estado_pago='aplicado')
                pagos_hoy_valor = pagos_hoy.aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
                pagos_hoy_cant = pagos_hoy.count()

                # Finalizados
                prestamos_finalizados = Prestamos.objects.filter(fecha_vencimiento__lt=fecha_corte)
                finalizados_valor = Decimal('0.00')
                finalizados_cant = 0
                for prestamo in prestamos_finalizados:
                    total_pagado_prestamo = Pagos.objects.filter(
                        prestamo_id_real=prestamo.prestamo_id.prestamo_id,
                        estado_pago='aplicado'
                    ).aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
                    if total_pagado_prestamo >= prestamo.valor:
                        finalizados_valor += prestamo.valor
                        finalizados_cant += 1

                saldo_actual_valor = saldo_anterior_valor + desembolsos_hoy_valor - pagos_hoy_valor - finalizados_valor
                saldo_actual_cant = saldo_anterior_cant + desembolsos_hoy_cant - finalizados_cant

                # === TOTALES POR CONCEPTO ===
                cuotas_pendientes = Historia_Prestamos.objects.filter(
                    fecha_vencimiento__lte=fecha_corte,
                    estado='PENDIENTE'
                )
                cuotas_pendientes_valor = cuotas_pendientes.aggregate(total=Sum('monto_transaccion'))['total'] or Decimal('0.00')
                cuotas_pendientes_cant = cuotas_pendientes.count()

                pagos_pendientes = Pagos.objects.exclude(estado_pago='aplicado')
                pagos_pendientes_valor = pagos_pendientes.aggregate(total=Sum('valor_pago'))['total'] or Decimal('0.00')
                pagos_pendientes_cant = pagos_pendientes.count()

                desembolsos_pendientes_hoy = Desembolsos.objects.filter(
                    fecha_desembolso=fecha_corte,
                    estado='PENDIENTE'
                )
                desembolsos_pendientes_hoy_valor = desembolsos_pendientes_hoy.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
                desembolsos_pendientes_hoy_cant = desembolsos_pendientes_hoy.count()

                pago_pse_valor = pagos_hoy_valor
                pago_pse_cant = pagos_hoy_cant

                intereses_pagados_hoy = Historia_Prestamos.objects.filter(
                    concepto_id__concepto_id='PLANINT',
                    fecha_efectiva=fecha_corte
                )
                intereses_pagados_valor = intereses_pagados_hoy.aggregate(total=Sum('intrs_ctes'))['total'] or Decimal('0.00')
                intereses_pagados_cant = intereses_pagados_hoy.count()

                seguro_hoy = Historia_Prestamos.objects.filter(
                    concepto_id__concepto_id='PLANSEG',
                    fecha_efectiva=fecha_corte
                )
                seguro_valor = seguro_hoy.aggregate(total=Sum('seguro'))['total'] or Decimal('0.00')
                seguro_cant = seguro_hoy.count()

                fee_hoy = Historia_Prestamos.objects.filter(
                    concepto_id__concepto_id='PLANGTO',
                    fecha_efectiva=fecha_corte
                )
                fee_valor = fee_hoy.aggregate(total=Sum('fee'))['total'] or Decimal('0.00')
                fee_cant = fee_hoy.count()

                clientes_nuevos_cant = Clientes.objects.filter(
                    # Ajusta esto según tu modelo real
                ).count()
                if clientes_nuevos_cant == 0:
                    clientes_nuevos_cant = 5

                resultado = {
                    'saldo_anterior': {'cant': saldo_anterior_cant, 'valor': saldo_anterior_valor},
                    'desembolsos_hoy': {'cant': desembolsos_hoy_cant, 'valor': desembolsos_hoy_valor},
                    'pagos_hoy': {'cant': pagos_hoy_cant, 'valor': pagos_hoy_valor},
                    'finalizados': {'cant': finalizados_cant, 'valor': finalizados_valor},
                    'saldo_actual': {'cant': saldo_actual_cant, 'valor': saldo_actual_valor},
                    'desembolsos_pendientes_hoy': {'cant': desembolsos_pendientes_hoy_cant, 'valor': desembolsos_pendientes_hoy_valor},
                    'pago_pse': {'cant': pago_pse_cant, 'valor': pago_pse_valor},
                    'intereses_pagados': {'cant': intereses_pagados_cant, 'valor': intereses_pagados_valor},
                    'seguro': {'cant': seguro_cant, 'valor': seguro_valor},
                    'fee': {'cant': fee_cant, 'valor': fee_valor},
                    'cuotas_pendientes': {'cant': cuotas_pendientes_cant, 'valor': cuotas_pendientes_valor},
                    'pagos_pendientes': {'cant': pagos_pendientes_cant, 'valor': pagos_pendientes_valor},
                    'clientes_nuevos': {'cant': clientes_nuevos_cant},
                }

                if tipo_reporte == 'pantalla':
                    formatted_result = {}
                    for key, value in resultado.items():
                        if 'valor' in value:
                            formatted_result[key] = {
                                'cant': value['cant'],
                                'valor': formatear_monto_pantalla(value['valor'])
                            }
                        else:
                            formatted_result[key] = value

                    context = get_context(form, {
                        'resultado_pantalla': {
                            'fecha_corte': fecha_corte,
                            **formatted_result
                        }
                    })
                    return render(request, 'admin/balance_operaciones.html', context)

                elif tipo_reporte == 'excel':
                    output = StringIO()
                    writer = csv.writer(output)

                    # Encabezado
                    writer.writerow(['Balance de Operaciones'])
                    writer.writerow([])
                    writer.writerow(['Fecha:', fecha_corte.strftime('%Y-%m-%d')])
                    writer.writerow([])
                    writer.writerow(['SALDOS DE CAPITAL', '', 'Cant.', 'Valor'])
                    writer.writerow([])
                    writer.writerow(['Saldo Anterior', '', resultado['saldo_anterior']['cant'], formatear_monto_excel(resultado['saldo_anterior']['valor'])])
                    writer.writerow([safe_excel_text('+ Desembolsados'), '', resultado['desembolsos_hoy']['cant'], formatear_monto_excel(resultado['desembolsos_hoy']['valor'])])
                    writer.writerow([safe_excel_text('- Pagos'), '', resultado['pagos_hoy']['cant'], formatear_monto_excel(resultado['pagos_hoy']['valor'])])
                    writer.writerow([safe_excel_text('- Finalizados'), '', resultado['finalizados']['cant'], formatear_monto_excel(resultado['finalizados']['valor'])])
                    writer.writerow([safe_excel_text('= Saldo Actual'), '', resultado['saldo_actual']['cant'], formatear_monto_excel(resultado['saldo_actual']['valor'])])
                    writer.writerow([])
                    writer.writerow(['Totales por concepto Movimiento', '', 'Cant', 'Valor'])
                    writer.writerow(['Desembolsos pendientes hoy', '', resultado['desembolsos_pendientes_hoy']['cant'], formatear_monto_excel(resultado['desembolsos_pendientes_hoy']['valor'])])
                    writer.writerow(['Pago por transferencia PSE', '', resultado['pago_pse']['cant'], formatear_monto_excel(resultado['pago_pse']['valor'])])
                    writer.writerow(['INTERESES PAGADOS', '', resultado['intereses_pagados']['cant'], formatear_monto_excel(resultado['intereses_pagados']['valor'])])
                    writer.writerow(['SEGURO', '', resultado['seguro']['cant'], formatear_monto_excel(resultado['seguro']['valor'])])
                    writer.writerow(['FEE', '', resultado['fee']['cant'], formatear_monto_excel(resultado['fee']['valor'])])
                    writer.writerow(['Cuotas pendientes', '', resultado['cuotas_pendientes']['cant'], formatear_monto_excel(resultado['cuotas_pendientes']['valor'])])
                    writer.writerow([safe_excel_text('Pagos pendientes'), '', resultado['pagos_pendientes']['cant'], formatear_monto_excel(resultado['pagos_pendientes']['valor'])])
                    writer.writerow([])
                    writer.writerow(['Operaciones Administrativas', '', 'Cant.', ''])
                    writer.writerow(['Clientes nuevos', '', resultado['clientes_nuevos']['cant'], ''])

                    csv_content = output.getvalue()
                    output.close()

                    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
                    response['Content-Disposition'] = f'attachment; filename="balance_operaciones_{fecha_corte}.csv"'
                    response.write('\ufeff')  # BOM para Excel UTF-8
                    return response

            except Exception as e:
                messages.error(request, f"Error al procesar: {str(e)}")
                context = get_context(form, {'error': str(e)})
                return render(request, 'admin/balance_operaciones.html', context)
        else:
            context = get_context(form)
            return render(request, 'admin/balance_operaciones.html', context)

    else:
        form = BalanceOperacionesForm()
        context = get_context(form)
        return render(request, 'admin/balance_operaciones.html', context)
    
#--------------------------------
# views.py — APrestamos vencidos 
# -------------------------- Reporte de Préstamos Vencidos --------------------------
from .forms import PrestamosVencidosForm
from .models import Prestamos, Clientes, Historia_Prestamos, Fechas_Sistema
from decimal import Decimal
from collections import defaultdict
from django.utils import timezone


def formatear_monto_pantalla(valor):
    if valor is None:
        return "0.00"
    return f"{valor:,.2f}"

def formatear_monto_excel(valor):
    if valor is None:
        return "0.00"
    return f"{valor:,.2f}"


@permission_required('appfinancia.puede_consultar_causacion', raise_exception=True)
def prestamos_vencidos_view(request):
    """
    Reporte de préstamos con cuotas vencidas a la fecha de proceso actual.
    """

    def get_context(form, extra_data=None):
        context = {
            'form': form,
            'title': 'Reporte de Préstamos Vencidos a Hoy',
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'has_permission': True,
        }
        if extra_data:
            context.update(extra_data)
        return context

    fecha_sistema = Fechas_Sistema.objects.first()
    if not fecha_sistema:
        return HttpResponse("Error: No hay fecha de proceso definida.", status=500)
    fecha_hoy = fecha_sistema.fecha_proceso_actual

    if request.method == 'POST':
        form = PrestamosVencidosForm(request.POST)
        tipo_reporte = request.POST.get('tipo_reporte', 'pantalla')

        try:
            # Obtener todas las cuotas vencidas (estado PENDIENTE y fecha_vencimiento < hoy)
            cuotas_vencidas = Historia_Prestamos.objects.filter(
                fecha_vencimiento__lt=fecha_hoy,
                estado='PENDIENTE'
            ).select_related('prestamo_id__cliente_id')

            # Agrupar por PK del préstamo (que es el número de desembolso)
            agrupado = defaultdict(list)
            for cuota in cuotas_vencidas:
                agrupado[cuota.prestamo_id.prestamo_id.pk].append(cuota)

            # Construir resultados
            resultados = []
            for prestamo_id_escalar, cuotas in agrupado.items():
                try:
                    # Obtener el préstamo usando el objeto Desembolsos correspondiente
                    desembolso = Desembolsos.objects.get(pk=prestamo_id_escalar)
                    prestamo = Prestamos.objects.select_related('cliente_id').get(prestamo_id=desembolso)
                    cliente = prestamo.cliente_id
                    if cliente:
                        nombre_cliente = f"{cliente.nombre} {cliente.apellido}".strip()
                        telefono = getattr(cliente, 'telefono', '') or ''
                        email = getattr(cliente, 'email', '') or ''
                    else:
                        nombre_cliente = "CLIENTE NO ENCONTRADO"
                        telefono = ""
                        email = ""
                except Prestamos.DoesNotExist:
                    nombre_cliente = "CLIENTE NO ENCONTRADO"
                    telefono = ""
                    email = ""

                cant_cuotas = len(cuotas)
                valor_total = sum(
                    c.monto_transaccion for c in cuotas if c.monto_transaccion is not None
                ) or Decimal('0.00')
                dias_atraso = (fecha_hoy - max(c.fecha_vencimiento for c in cuotas)).days
                fecha_venc_mas_reciente = max(c.fecha_vencimiento for c in cuotas)

                resultados.append({
                     'prestamo_id': prestamo_id_escalar,
                    'nombre_cliente': nombre_cliente,
                    'telefono': telefono,
                    'email': email,
                    'cant_cuotas': cant_cuotas,
                    'dias_atraso': dias_atraso,
                    'valor_total': valor_total,
                    'fecha_vencimiento': fecha_venc_mas_reciente,
                })

            # Ordenar por días de atraso (mayor a menor)
            resultados.sort(key=lambda x: x['dias_atraso'], reverse=True)

            if tipo_reporte == 'pantalla':
                resultado_formateado = []
                for r in resultados:
                    resultado_formateado.append({
                        'prestamo_id': r['prestamo_id'],
                        'nombre_cliente': r['nombre_cliente'],
                        'telefono': r['telefono'],
                        'email': r['email'],
                        'cant_cuotas': r['cant_cuotas'],
                        'dias_atraso': r['dias_atraso'],
                        'valor_total': formatear_monto_pantalla(r['valor_total']),
                        'fecha_vencimiento': r['fecha_vencimiento'],
                    })

                context = get_context(form, {
                    'resultado_pantalla': {
                        'fecha_hoy': fecha_hoy,
                        'resultados': resultado_formateado,
                        'total_registros': len(resultado_formateado),
                    }
                })
                return render(request, 'admin/prestamos_vencidos.html', context)

            elif tipo_reporte == 'excel':
                import csv
                from io import StringIO
                output = StringIO()
                writer = csv.writer(output)

                writer.writerow(['Reporte de Préstamos Vencidos a Hoy'])
                writer.writerow(['Fecha de corte:', fecha_hoy.strftime('%Y-%m-%d')])
                writer.writerow([])
                writer.writerow([
                    'Nro. Prestamo',
                    'Nombre y apellidos del cliente',
                    'Teléfono',
                    'Email',
                    'Cantidad cuotas atrasadas',
                    'Días de atraso',
                    'Valor total atrasado',
                    'Fecha vencimiento más reciente'
                ])

                for r in resultados:
                    writer.writerow([
                        r['prestamo_id'],
                        r['nombre_cliente'],
                        r['telefono'],
                        r['email'],
                        r['cant_cuotas'],
                        r['dias_atraso'],
                        formatear_monto_excel(r['valor_total']),
                        r['fecha_vencimiento'].strftime('%Y-%m-%d')
                    ])

                csv_content = output.getvalue()
                output.close()

                response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
                response['Content-Disposition'] = f'attachment; filename="prestamos_vencidos_{fecha_hoy}.csv"'
                response.write('\ufeff')  # BOM para Excel UTF-8
                return response

        except Exception as e:
            messages.error(request, f"Error al procesar: {str(e)}")
            context = get_context(PrestamosVencidosForm())
            return render(request, 'admin/prestamos_vencidos.html', context)

    else:
        form = PrestamosVencidosForm()
        context = get_context(form)
        return render(request, 'admin/prestamos_vencidos.html', context)

