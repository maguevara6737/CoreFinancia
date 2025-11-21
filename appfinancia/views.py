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
from django.contrib.auth.decorators import user_passes_test
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

@staff_member_required
def plan_de_pagos_view(request, prestamo_id): # Este prestamo_id es el ID del Desembolso (por ejemplo, 7)
    """
    Vista personalizada que muestra el plan de pagos de un préstamo en una sola página.
    Agrupa los registros de Historia_Prestamos por número de cuota y fecha de vencimiento,
    y suma los montos por tipo de concepto basado en monto_transaccion y concepto_id.
    """
    # CORRECCIÓN: Busca el Prestamo usando el campo de base de datos 'prestamo_id_id'
    # que almacena el ID numérico del objeto Desembolsos relacionado.
    prestamo = get_object_or_404(Prestamos, prestamo_id_id=prestamo_id)

    # === AGREGA ESTA LÍNEA ===
    print(f"DEBUG: prestamo.pk = {prestamo.pk}, prestamo.prestamo_id = {prestamo.prestamo_id}, prestamo.prestamo_id.pk = {prestamo.prestamo_id.pk if prestamo.prestamo_id else 'None'}")
    # === FIN AGREGADO ===

    # Obtener todas las transacciones del préstamo, ordenadas
    transacciones = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo
    ).select_related(
        'concepto_id', # Esto es suficiente para acceder a t.concepto_id.concepto_id
        'prestamo_id__prestamo_id__cliente_id' # <-- Puede necesitar revisión
        # 'prestamo_id__cliente_id' # <-- Opción alternativa si la relación es directa desde Prestamos
    ).order_by(
        'numero_cuota', 'fecha_vencimiento'
    )

    # Agrupar las transacciones por cuota y fecha de vencimiento
    plan = []

    for t in transacciones:
        # --- IMPRESIÓN: Ver cada transacción y su concepto ---
        print(f"\nProcesando Operación {t.numero_operacion}, Cuota {t.numero_cuota}, Fecha Venc {t.fecha_vencimiento}")
        print(f"  - Concepto ID (objeto): {t.concepto_id}")
        print(f"  - Concepto ID (valor real): {t.concepto_id.concepto_id if t.concepto_id else 'None'}") # Accede al campo del objeto relacionado
        print(f"  - Monto Transacción: {t.monto_transaccion}")
        print(f"  - Abono Capital (real): {t.abono_capital}")
        print(f"  - Inters Ctes (real): {t.intrs_ctes}")
        print(f"  - Seguro (real): {t.seguro}")
        print(f"  - Fee (real): {t.fee}")
        # --- FIN IMPRESIÓN ---

        clave = (t.numero_cuota, t.fecha_vencimiento)
        encontrado = False

        # Determinar el valor a acumular basado en el concepto_id
        # Asumiendo que t.concepto_id es una FK a Conceptos_Transacciones
        # y que t.concepto_id.concepto_id contiene el string identificativo
        concepto_real = t.concepto_id.concepto_id if t.concepto_id else None
        valor_capital = 0.0
        valor_intereses = 0.0
        valor_seguro = 0.0
        valor_fee = 0.0

        # Ajusta las cadenas de comparación según los valores EXACTOS de tu base de datos
        # o usa operaciones como 'in' si hay variaciones en el texto
        if concepto_real and 'PLANCAP' in concepto_real: # Ajusta según sea necesario
            valor_capital = t.monto_transaccion
        elif concepto_real and 'PLANINT' in concepto_real: # Ajusta según sea necesario
            valor_intereses = t.monto_transaccion
        elif concepto_real and 'PLANSEG' in concepto_real: # Ajusta según sea necesario
            valor_seguro = t.monto_transaccion
        elif concepto_real and 'PLANGTO' in concepto_real: # Ajusta según sea necesario, puede ser 'FEE' o similar
            valor_fee = t.monto_transaccion
        # Si no coincide con ninguno, todos los valores temporales siguen siendo 0.0

        print(f"  - Concepto Procesado: {concepto_real}, Asignado a Capital: {valor_capital}, Intereses: {valor_intereses}, Seguro: {valor_seguro}, Fee: {valor_fee}")

        for item in plan:
            if item['clave'] == clave:
                encontrado = True
                # Acumular los valores usando las variables temporales
                item['capital'] += float(valor_capital)
                item['intereses'] += float(valor_intereses)
                item['seguro'] += float(valor_seguro)
                item['fee'] += float(valor_fee)
                print(f"  -> Acumulando en clave {clave}: Cap={item['capital']}, Int={item['intereses']}, Seg={item['seguro']}, Fee={item['fee']}")
                break # <-- Rompe el bucle interno si encuentra la clave

        if not encontrado: # <-- Si no encontró la clave, crea un nuevo item
            plan.append({
                'clave': clave,
                'cuota': t.numero_cuota,
                'fecha_vencimiento': t.fecha_vencimiento,
                'capital': float(valor_capital), # <-- Usar el valor temporal calculado
                'intereses': float(valor_intereses), # <-- Usar el valor temporal calculado
                'seguro': float(valor_seguro), # <-- Usar el valor temporal calculado
                'fee': float(valor_fee), # <-- Usar el valor temporal calculado
            })
            print(f"  -> Nueva entrada en plan para clave {clave} con Cap={valor_capital}, Int={valor_intereses}, Seg={valor_seguro}, Fee={valor_fee}")

    # --- IMPRESIÓN: Ver estado de 'plan' antes de calcular totales ---
    print(f"\n--- Estado de 'plan' ANTES de calcular totales ---")
    for item in plan:
        print(f"  Clave: {item['clave']}, Cuota: {item['cuota']}, Fecha Venc: {item['fecha_vencimiento']}, "
              f"Cap: {item['capital']}, Int: {item['intereses']}, Seg: {item['seguro']}, Fee: {item['fee']}")
    # --- FIN IMPRESIÓN ---

    # Calcular el total de la cuota para cada fila
    for item in plan:
        item['total_cuota'] = item['capital'] + item['intereses'] + item['seguro'] + item['fee']

    # --- IMPRESIÓN: Ver estado final de 'plan' ---
    print(f"\n--- Estado de 'plan' DESPUÉS de calcular totales ---")
    for item in plan:
        print(f"  Cuota: {item['cuota']}, Fecha Venc: {item['fecha_vencimiento']}, "
              f"Total: {item['total_cuota']}, Cap: {item['capital']}, Int: {item['intereses']}, Seg: {item['seguro']}, Fee: {item['fee']}")
    print(f"Total cuotas agrupadas: {len(plan)}")
    # --- FIN IMPRESIÓN ---

    context = {
        'prestamo': prestamo,
        'plan': plan, # Ya es una lista de diccionarios agrupados
        'desembolso_id': prestamo_id, # Opcional: Puedes pasar el ID del desembolso también si es útil en la plantilla
    }
    return render(request, 'appfinancia/plan_de_pagos.html', context)

#__________________________________________________________________________________________________________________________

# appfinancia/views.py (fragmento de la función de exportación)
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse #  
from .models import Prestamos, Historia_Prestamos, Desembolsos
from collections import defaultdict
# No importes openpyxl aquí, hazlo dentro de la vista

@staff_member_required
def exportar_historia_prestamo_xlsx(request, prestamo_id): # Este prestamo_id es el ID del Desembolso (por ejemplo, 7)
    """
    Vista para exportar la historia de un préstamo agrupada por cuota y fecha de vencimiento.
    Utiliza monto_transaccion y concepto_id para calcular los valores correctos.
    """
    # CORRECCIÓN: Busca el Prestamo usando el campo de base de datos 'prestamo_id_id'
    # que almacena el ID numérico del objeto Desembolsos relacionado.
    prestamo = get_object_or_404(Prestamos, prestamo_id_id=prestamo_id)

    # Filtrar y ordenar los registros como en la vista HTML
    queryset = Historia_Prestamos.objects.filter(
        prestamo_id=prestamo
    ).select_related(
        'concepto_id', # Esto es suficiente para acceder a obj.concepto_id.concepto_id
        'prestamo_id__prestamo_id__cliente_id' # <-- Puede necesitar revisión
        # 'prestamo_id__cliente_id' # <-- Opción alternativa si la relación es directa desde Prestamos
    ).order_by(
        'numero_cuota', 'fecha_vencimiento'
    )

    # Agrupar los datos - CORREGIDO: Basado en monto_transaccion y concepto_id
    agrupados = {}

    for obj in queryset:
        clave = (obj.numero_cuota, obj.fecha_vencimiento)

        # --- LÓGICA CORREGIDA: Determinar valores basados en concepto_id ---
        concepto_real = obj.concepto_id.concepto_id if obj.concepto_id else None
        valor_capital = 0.0
        valor_intereses = 0.0
        valor_seguro = 0.0
        valor_fee = 0.0

        # Ajusta las cadenas de comparación según los valores EXACTOS de tu base de datos
        # o usa operaciones como 'in' si hay variaciones en el texto
        if concepto_real and 'PLANCAP' in concepto_real: # Ajusta según sea necesario
            valor_capital = float(obj.monto_transaccion)
        elif concepto_real and 'PLANINT' in concepto_real: # Ajusta según sea necesario
            valor_intereses = float(obj.monto_transaccion)
        elif concepto_real and 'PLANSEG' in concepto_real: # Ajusta según sea necesario
            valor_seguro = float(obj.monto_transaccion)
        elif concepto_real and 'PLANGTO' in concepto_real: # Ajusta según sea necesario, puede ser 'FEE' o similar
            valor_fee = float(obj.monto_transaccion)
        # Si no coincide con ninguno, todos los valores temporales siguen siendo 0.0
        # --- FIN LÓGICA CORREGIDA ---

        # Acumular valores en el diccionario agrupado
        if clave not in agrupados:
            agrupados[clave] = {
                'clave': clave,
                'cuota': obj.numero_cuota,
                'fecha_vencimiento': obj.fecha_vencimiento,
                'capital': 0.0,
                'intereses': 0.0,
                'seguro': 0.0,
                'fee': 0.0,
            }

        agrupados[clave]['capital'] += valor_capital
        agrupados[clave]['intereses'] += valor_intereses
        agrupados[clave]['seguro'] += valor_seguro
        agrupados[clave]['fee'] += valor_fee

    # Convertir el diccionario a lista para facilitar el manejo
    lista_agrupada = list(agrupados.values())

    # Calcular el total de la cuota para cada fila
    for item in lista_agrupada:
        item['total_cuota'] = item['capital'] + item['intereses'] + item['seguro'] + item['fee']

    # Crear el archivo Excel con openpyxl
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = f"Plan_Pago_{prestamo.prestamo_id.prestamo_id}" # Asumiendo que prestamo.prestamo_id.prestamo_id es el ID del desembolso

    # Encabezados - EXACTAMENTE IGUALES a la vista HTML
    encabezados = [
        "Cuota", "Fecha Vencimiento", "Total Cuota", "Capital",
        "Intereses", "Seguro", "Fee"
    ]
    ws.append(encabezados)

    # Aplicar formato a encabezados
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    # Agregar filas agrupadas
    for item in lista_agrupada: # Iterar sobre la lista convertida
        fila = [
            item['cuota'],
            item['fecha_vencimiento'].strftime('%Y-%m-%d'), # Formato yyyy-mm-dd
            f"${item['total_cuota']:,.2f}",
            f"${item['capital']:,.2f}",
            f"${item['intereses']:,.2f}",
            f"${item['seguro']:,.2f}",
            f"${item['fee']:,.2f}",
        ]
        ws.append(fila)

    # Ajustar ancho de columnas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)  # Máximo 50 caracteres
        ws.column_dimensions[column_letter].width = adjusted_width

    # Preparar respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=plan_pago_{prestamo.prestamo_id.prestamo_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

    # Guardar el archivo en la respuesta
    wb.save(response)
    return response
