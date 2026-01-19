# ======================================================
# 1. LIBRERÍAS ESTÁNDAR DE PYTHON
# ======================================================
import os
from datetime import date
from decimal import Decimal

# ======================================================
# 2. LIBRERÍAS DE TERCEROS (DJANGO)
# ======================================================
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import action, DateFieldListFilter
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import models, transaction, IntegrityError
from django.forms import TextInput
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

# ======================================================
# 3. IMPORTACIONES LOCALES (APPFINANCIA)
# ======================================================

# --- Modelos ---
from .models import (
    Asesores, Aseguradoras, Bitacora, Clientes, Comentarios, 
    Comentarios_Prestamos, Conceptos_Transacciones, ConsultasReportesProxy,
    Departamentos, Desembolsos, Fechas_Sistema, Financiacion, 
    Historia_Prestamos, InBox_PagosCabezal, InBox_PagosDetalle, 
    Municipios, Numeradores, Pagos, PagosParaRegularizar, Politicas, 
    Prestamos, Tasas, Tipos_Identificacion, Vendedores
)

# --- Formularios ---
from .forms import ComentarioPrestamoForm

# --- Utilidades (.utils) ---
from .utils import (
    aplicar_pago_cuota_inicial, calculate_loan_schedule, cerrar_periodo_interes,
    confirmar_pagos, create_loan_payments, create_movimiento, create_prestamo,
    f_anular_archivo, f_procesar_archivo, generar_reporte_excel_en_memoria,
    get_next_conciliacion_id, InBox_Pagos
)

# --- Servicios (.services) ---
from .services.conciliacion import conciliacion_por_movimiento, reporte_resumen_conciliacion
from .services.reportes_pagos import generar_reporte_pagos_excel
from .services.reportes_conciliacion import generar_reporte_conciliacion_excel
from .services.financiacion_imap import procesar_emails
from .services.financiacion_aprobacion import f_aprobar_financiacion
from .services.financiacion_pdf import f_generar_pdf_plan_pagos
from .services.financiacion_plan_pagos import f_plan_pagos_cuota_fija
from .services.financiacion_correo_aprobacion import f_correo_aprobacion

# --- Vistas ---
from .views import (
    consulta_causacion_view, balance_operaciones_view, prestamos_vencidos_view
)

# ----------------------------------------------------------------------------------------
class AdminBaseMoneda(admin.ModelAdmin):
    formfield_overrides = {
        models.DecimalField: {
            "widget": TextInput(attrs={"class": "vTextField"})
        }
    }

    class Media:
        js = ('appfinancia/js/moneda_admin_global.js',)

#-----------------------------------------------------------------------------------------
class FechasSistemaForm(forms.ModelForm):
    class Meta:
        model = Fechas_Sistema
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance.pk and instance.modo_fecha_sistema == 'AUTOMATICO':
            # En modo automático, solo permitir editar estado y modo
            for field in ['fecha_proceso_anterior', 'fecha_proceso_actual', 'fecha_proximo_proceso']:
                self.fields[field].disabled = True
                self.fields[field].help_text = "🔒 Solo editable en modo 'Manual'."
                
#-----------------------------------------------------------------------------------------
'''
class FechasSistemaForm(forms.ModelForm):
    class Meta:
        model = Fechas_Sistema
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya existe y está en modo AUTOMÁTICO → bloquear fechas
        if self.instance.pk and self.instance.modo_fecha_sistema == 'AUTOMATICO':
            for field_name in ['fecha_proceso_anterior', 'fecha_proceso_actual', 'fecha_proximo_proceso']:
                self.fields[field_name].disabled = True
                self.fields[field_name].help_text = "🔒 Solo editable en modo 'Manual'."
'''
#-----------------------------------------------------------------------------------------
@admin.register(Fechas_Sistema)
class FechasSistemaAdmin(admin.ModelAdmin):
    form = FechasSistemaForm
    list_display = (
        'fecha_proceso_actual','estado_sistema_colored', 'modo_fecha_sistema',
        'fecha_ultima_modificacion', 'cambiado_por',
    )

    def estado_sistema_colored(self, obj):
        color = 'green' if obj.estado_sistema == 'ABIERTO' else 'red'
        return f'<span style="color:{color}; font-weight:bold;">{obj.get_estado_sistema_display()}</span>'

    estado_sistema_colored.short_description = "Estado"
    estado_sistema_colored.allow_tags = True

    def has_delete_permission(self, request, obj=None):
        return False  # ❌ Nunca permitir eliminar

    def has_add_permission(self, request):
        return not Fechas_Sistema.objects.exists()  # ✅ Solo si no existe

    def save_model(self, request, obj, form, change):
        obj._request = request  # pasar request para asignar cambiado_por
        super().save_model(request, obj, form, change)

#-----------------------------------------------------------------------------------------
@admin.register(Tipos_Identificacion)
class TiposIdentificacionAdmin(admin.ModelAdmin):
    list_display = ('tipo_id', 'descripcion_id')
    search_fields = ('tipo_id', 'descripcion_id')
    ordering = ('tipo_id',)

    # Evitar que se edite el tipo_id después de creado (es PK)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe (modo edición)
            return ('tipo_id',)
        return ()

#-----------------------------------------------------------------------------------------
@admin.register(Asesores)
class AsesoresAdmin(admin.ModelAdmin):
    list_display = ('asesor_id', 'asesor_nombre', 'asesor_estado', 'fecha_creacion')
    search_fields = ('asesor_id', 'asesor_nombre')
    list_filter = ('asesor_estado', 'fecha_creacion')
    ordering = ('asesor_nombre',)

    fieldsets = (
        ('Identificación', {
            'fields': ('asesor_id',),
            'description': "ID único del asesor (no editable después de creado)."
        }),
        ('Información Personal', {
            'fields': ('asesor_nombre', 'asesor_estado')
        }),
    )

    readonly_fields = ('fecha_creacion',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe, bloquear asesor_Id y fecha_creacion
            return self.readonly_fields + ('asesor_Id',)
        return self.readonly_fields

#-----------------------------------------------------------------------------------------
@admin.register(Aseguradoras)
class AseguradorasAdmin(admin.ModelAdmin):
    list_display = ('aseguradora_id', 'aseguradora_nombre', 'aseguradora_estado', 'fecha_creacion')
    search_fields = ('aseguradora_id', 'aseguradora_nombre')
    list_filter = ('aseguradora_estado', 'fecha_creacion')
    ordering = ('aseguradora_nombre',)

    fieldsets = (
        ('Identificación', {
            'fields': ('aseguradora_id',),
            'description': "ID único de la aseguradora (no editable después de creado)."
        }),
        ('Información', {
            'fields': ('aseguradora_nombre', 'aseguradora_estado')
        }),
    )

    readonly_fields = ('fecha_creacion',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el registro ya existe
            return self.readonly_fields + ('aseguradora_id',)
        return self.readonly_fields

#-----------------------------------------------------------------------------------------
@admin.register(Tasas)
class TasasAdmin(admin.ModelAdmin):
    list_display = ('tipo_tasa', 'tasa')
    ordering = ('tipo_tasa',)

    # Evitar que se edite tipo_tasa después de creado (es clave primaria)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe (modo edición)
            return ('tipo_tasa',)
        return ()

#-----------------------------------------------------------------------------------------
@admin.register(Departamentos)
class DepartamentosAdmin(admin.ModelAdmin):
    list_display = ('departamento_id', 'departamento_nombre')
    search_fields = ('departamento_id', 'departamento_nombre')
    ordering = ('departamento_id',)

    # Evitar que se edite el ID después de creado (es clave primaria)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el registro ya existe
            return ('departamento_id',)
        return ()

#-----------------------------------------------------------------------------------------
@admin.register(Municipios)
class MunicipiosAdmin(admin.ModelAdmin):
    list_display = ('municipio_id', 'departamento', 'municipio_nombre')
    list_display_links = ('municipio_id', 'municipio_nombre')
    search_fields = ('municipio_nombre', 'municipio_id', 'departamento__departamento_nombre')
    list_filter = ('departamento',)
    ordering = ('departamento', 'municipio_id')

    fieldsets = (
        ('Identificación', {
            'fields': ('municipio_id', 'departamento'),
            'description': "El municipio se identifica por su código y su departamento."
        }),
        ('Nombre', {
            'fields': ('municipio_nombre',)
        }),
    )

    # Evitar editar la clave compuesta tras la creación
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe
            return ('municipio_id', 'departamento')
        return ()

#-----------------------------------------------------------------------------------------
@admin.register(Vendedores)
class VendedoresAdmin(admin.ModelAdmin):
    list_display = ('cod_venta_id', 'cod_venta_nombre', 'estado', 'fecha_creacion')
    search_fields = ('cod_venta_id', 'cod_venta_nombre')
    list_filter = ('estado', 'fecha_creacion')
    ordering = ('cod_venta_nombre',)

    fieldsets = (
        ('Identificación', {
            'fields': ('cod_venta_id',),
            'description': "Código único del vendedor (no editable después de creado)."
        }),
        ('Información Personal', {
            'fields': ('cod_venta_nombre', 'estado')
        }),
    )

    readonly_fields = ('fecha_creacion',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el registro ya existe
            return self.readonly_fields + ('cod_venta_id',)
        return self.readonly_fields

#-----------------------------------------------------------------------------------------
@admin.register(Numeradores)
class NumeradoresAdmin(admin.ModelAdmin):
    list_display = (
        'numerador_prestamo', 'numerador_transaccion',
        'numerador_operacion', 'numerador_conciliacion',
        'numerador_pagos'
    )

    fieldsets = (
        ('Contadores Principales', {
            'fields': (
                'numerador_prestamo',
                'numerador_transaccion',
                # 'numerador_operacion',
                'numerador_conciliacion',
                'numerador_pagos'
            )
        }),
        ('Contadores Auxiliares', {
            'fields': ('numerador_aux_1','numerador_aux_2', 'numerador_aux_3',
                'numerador_aux_4', 'numerador_aux_5'
            ),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return not Numeradores.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if not Numeradores.objects.exists():
            return self.add_view(request)
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        try:
            # Guardar y mostrar mensaje
            super().save_model(request, obj, form, change)
            messages.success(request, "✅ Numeradores actualizados.")
        except ValidationError as e:
            for field, errs in e.message_dict.items():
                for err in errs:
                    messages.error(request, f"{field}: {err}")
        except Exception as e:
            messages.error(request, f"❌ Error: {e}")

#-----------------------------------------------------------------------------------------
@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = (
        'cliente_id', 'tipo_id', 'nombre', 'apellido',
        'email', 'telefono', 'estado',
    )
    # search_fields = ('cliente_id', 'nombre', 'apellido', 'email', 'direccion') #2025/12/19
    search_fields = ("cliente_id__icontains", "nombre__icontains", "apellido__icontains", 'email', 'direccion')

    list_filter = ('tipo_id', 'fecha_creacion')
    ordering = ('apellido', 'nombre')

    fieldsets = (
        ('Identificación', {
            'fields': ('cliente_id', 'tipo_id'),
            'description': "ID único y tipo de identificación del cliente."
        }),
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'email', 'telefono', 'direccion')
        }),
        ('Ubicación', {
            'fields': ('departamento', 'municipio')
        }),
        ('Estado y Registro', {
            'fields': ('estado', 'fecha_creacion')
        }),
    )

    readonly_fields = ('fecha_creacion',)
    list_per_page = 14

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe, bloquear cliente_id y fecha_creacion
            return self.readonly_fields + ('cliente_id',)
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # Ejecuta las validaciones personalizadas
        super().save_model(request, obj, form, change)

#-----------------------------------------------------------------------------------------
class ComentarioInline(admin.TabularInline):
    model = Comentarios_Prestamos
    extra = 1
    readonly_fields = (
        # 'numero_comentario',
        # 'comentario_catalogo',
        'fecha_comentario',
        'creado_por',
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "comentario_catalogo":
            kwargs["queryset"] = Comentarios.objects.filter(estado='HABILITADO')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Solo permitir añadir comentarios cuando el desembolso ya está guardado
    '''
    def has_add_permission(self, request, obj=None):
        return obj is not None and obj.pk is not None

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
    '''

#-----------------------------------------------------------------------------------------
@admin.register(Desembolsos)
class DesembolsosAdmin(AdminBaseMoneda):
    list_display = ('prestamo_id','cliente_id_display','valor_formatted',
        'estado_colored', 'fecha_desembolso',
    )
    list_filter = ('estado',)
    search_fields = ('=prestamo_id', '=cliente_id__cliente_id', 'cliente_id__nombre')
    ordering = ('-fecha_desembolso',)
    inlines = [ComentarioInline]
    exclude = ('valor_cuota_mensual',)

    # Campos siempre de solo lectura
    readonly_fields_base = ('prestamo_id', 'fecha_vencimiento', 'fecha_creacion')

    list_per_page = 14

    # ------------------------------------------------------------------
    # Diseño del formulario
    # ------------------------------------------------------------------
    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            'fields': ('tipo_tasa', 'tasa', 'valor', 'valor_cuota_1', 
            'numero_transaccion_cuota_1','valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento')
        }),
        ('Estado y Auditoría', {
            'fields': ('estado', 'fecha_creacion')
        }),
    )

    # ------------------------------------------------------------------
    # Columnas con formato bonito
    # ------------------------------------------------------------------
    def cliente_id_display(self, obj):
        return f"{obj.cliente_id.cliente_id} - {obj.cliente_id}"

    cliente_id_display.short_description = "Cliente"

    def valor_formatted(self, obj):
        return f"${obj.valor:,.0f}"

    valor_formatted.short_description = "Valor"

    def estado_colored(self, obj):
        colores = {
            'ELABORACION': '#3498db',
            'A_DESEMBOLSAR': '#e67e22',
            'DESEMBOLSADO': '#27ae60',
            'ANULADO': '#c0392b',
        }
        textos = {
            'ELABORACION': 'En Elaboración',
            'A_DESEMBOLSAR': 'A Desembolsar',
            'DESEMBOLSADO': 'Desembolsado',
            'ANULADO': 'Anulado',
        }
        color = colores.get(obj.estado, '#7f8c8d')
        texto = textos.get(obj.estado, obj.estado)
        return format_html('<b style="color:{};">{}</b>', color, texto)

    estado_colored.short_description = "Estado"

    # ------------------------------------------------------------------
    # Control de campos readonly según estado
    # ------------------------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        if obj is None:  # Creación
            return self.readonly_fields_base
        if obj.estado == 'ELABORACION':
            return self.readonly_fields_base
        # Otros estados: todo bloqueado (excepto comentarios)
        return [f.name for f in self.model._meta.fields if f.name != 'id']

    # ------------------------------------------------------------------
    # Control de opciones de estado en el formulario
    # ------------------------------------------------------------------
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "estado":
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:  # Edición
                kwargs["choices"] = [
                    ('ELABORACION', 'En Elaboración'),
                    ('A_DESEMBOLSAR', 'A Desembolsar'),
                ]
            else:  # Creación
                kwargs["choices"] = [('ELABORACION', 'En Elaboración')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    # ------------------------------------------------------------------
    # Acciones masivas
    # ------------------------------------------------------------------
    actions = ['procesar_desembolsos_pendientes', 'anular']

    def anular(self, request, queryset):
        updated = queryset.exclude(estado='ANULADO').update(estado='ANULADO')
        self.message_user(request, f"{updated} desembolso(s) anulado(s).")

    anular.short_description = "Anular"

    # ------------------------------------------------------------------
    # Seguridad
    # ------------------------------------------------------------------
    def has_delete_permission(self, request, obj=None):
        return False  # Nadie puede borrar desembolsos

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"Error al guardar: {e}", level='error')

    # bloque de código para inyectar el java script, debe ir dentro una clase. 2025/11/25 pam
    '''
    class Media:
        js = [
            'appfinancia/js/session-expiry.js',
            'appfinancia/js/number-format.js',
            'appfinancia/js/close-tab-logout.js',
        ]            
    '''

#-----------------------------------------------------------------------------------------
    @action(description="Procesar desembolsos pendientes A_DESEMBOLSAR")
    def procesar_desembolsos_pendientes(modeladmin, request, queryset):
        from .utils import get_next_asientos_id
        """-------------------------------------------------------------------------------------
        Action para el Django Admin: procesa todos los desembolsos en estado 'A_DESEMBOLSAR'.
        Crea registros en Prestamos, Movimientos, Historia_Prestamos y calcula el plan de pagos.
        ----------------------------------------------------------------------------------------"""
        desembolsos_marcados = list(queryset.filter(estado="A_DESEMBOLSAR"))
        print(f"\n🔍 1. Inicio proceso. Cantidad: {len(desembolsos_marcados)}")
        if not desembolsos_marcados:
            messages.warning(request, "⚠️ No hay desembolsos A_DESEMBOLSAR para procesar.")
            return

        try:
            print(f"\n🔍 2. Entrando al try. Cantidad: {len(desembolsos_marcados)}")
            with transaction.atomic():
                print(f"\n🔍 3. Dentro de transaction.atomic(). Cantidad: {len(desembolsos_marcados)}")
                # ✅ Obtener número de asiento contable único por desembolso
                numero_asiento_desembolso = get_next_asientos_id()
                for desembolso in desembolsos_marcados:
                    print(f"\n🔍 4. Procesando desembolso ID={desembolso.prestamo_id}, estado={desembolso.estado}")
                    if Prestamos.objects.filter(prestamo_id=desembolso).exists():
                        messages.warning(
                            request,
                            f"⚠️ El desembolso {desembolso.prestamo_id} ya tiene un préstamo. Se omite."
                        )
                        continue

                    # 1. Crear Prestamo
                    prestamo = create_prestamo(desembolso)
                    print(f"✅ Préstamo creado con PK: {prestamo.pk}")

                    # 2. Crear Movimiento
                    create_movimiento(desembolso)
                    print(f"✅ Movimiento creado para desembolso {desembolso.prestamo_id}")

                    # 4. Calcular plan de pagos
                    plan_pagos = calculate_loan_schedule(desembolso)
                    print(f"✅ Plan de pagos calculado: {len(plan_pagos)} cuotas")

                    # 5. Crear cuotas en Historia_Prestamos
                    if plan_pagos:
                        created_count = create_loan_payments(
                            prestamo=prestamo,
                            desembolso=desembolso,
                            plan_pagos=plan_pagos,
                            user_name=request.user.username
                        )
                        print(f"✅ Creadas {created_count} cuotas en Historia_Prestamos")

                    # 6.  Aplicar el pago de la cuota inicial 2025-11-28 
                    if desembolso.numero_transaccion_cuota_1 and desembolso.valor_cuota_1:
                        aplicar_pago_cuota_inicial(
                            desembolso,
                            prestamo,
                            usuario='sistema',
                            numero_asiento_contable=numero_asiento_desembolso  # ✅
                        )
                    print(f"✅ Aplicado pago de cuota inicial {prestamo.pk}")

                    # 7. Inicializar el primer período de interés (día del desembolso)
                    cerrar_periodo_interes(
                        prestamo_id=prestamo.pk,  # o prestamo.prestamo_id si usas PK explícita
                        fecha_corte=desembolso.fecha_desembolso,
                        pago_referencia=f"DESEMBOLSO_{desembolso.prestamo_id}",
                        numero_asiento_contable=numero_asiento_desembolso  # ✅
                    )
                    print(f"✅ Período de interés inicializado para préstamo {prestamo.pk}")
                    # ===  Í ===

                    # 8. ✅ ACTUALIZAR ESTADO (clave del cambio 2025-11-25) 
                    Desembolsos.objects.filter(prestamo_id=desembolso.prestamo_id).update(estado='DESEMBOLSADO')
                    print(f"✅ Estado actualizado a 'DESEMBOLSADO' para desembolso {desembolso.prestamo_id}")

            messages.success(
                request,
                f"✅ Se procesaron exitosamente {len(desembolsos_marcados)} desembolsos con plan de pagos."
            )
            print(f"✅ Proceso completado exitosamente para {len(desembolsos_marcados)} desembolsos.")

        except Exception as e:
            error_msg = f"❌ Error al procesar desembolsos: {str(e)}"
            messages.error(request, error_msg)
            print(error_msg)

            if request.user.username:
                Bitacora.objects.create(
                    fecha_proceso=timezone.now().date(),
                    user_name=request.user.username,
                    evento_realizado='PROCESO_DESEMBOLSOS',
                    proceso='ERROR',
                    resultado=error_msg
                )

    procesar_desembolsos_pendientes.short_description = "Pasar a Desembolsado"

#-----------------------------------------------------------------------------------------
@admin.register(Conceptos_Transacciones)
class ConceptosTransaccionesAdmin(admin.ModelAdmin):
    list_display = ('concepto_id', 'codigo_transaccion', 'descripcion', 'estado')
    search_fields = ('concepto_id', 'codigo_transaccion', 'descripcion')
    list_filter = ('estado',)
    ordering = ('concepto_id',)

    fieldsets = (
        ('Identificación', {
            'fields': ('concepto_id', 'codigo_transaccion'),
            'description': "El 'concepto_id' es la clave primaria. El 'codigo_transaccion' debe ser único."
        }),
        ('Descripción y Estado', {
            'fields': ('descripcion', 'estado')
        }),
    )

    # Evitar eliminación de registros
    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        # Bloqueo adicional por seguridad
        messages.error(request, "No se permite eliminar conceptos de transacciones.")
        return

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

#-----------------------------------------------------------------------------------------
@admin.register(Comentarios)
class ComentariosAdmin(admin.ModelAdmin):
    list_display = (
        # 'comentario_id',
        'operacion_id', 'evento_id',
        'comentario', 'estado'
    )
    search_fields = ('operacion_id', 'evento_id', 'comentario')
    list_filter = ('estado',)
    ordering = ('operacion_id', 'evento_id')
    # readonly_fields = ('comentario_id',)

    fieldsets = (
        ('Identificación', {
            # 'fields': ('comentario_id', 'operacion_id', 'evento_id'),
            'fields': ('operacion_id', 'evento_id'),
            'description': "La combinación (Operación, Evento) debe ser única."
        }),
        ('Contenido', {
            'fields': ('comentario', 'estado')
        }),
    )

    # ❌ No permitir eliminación
    def has_delete_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        messages.error(request, "❌ No se permite eliminar comentarios. Use 'DESHABILITADO' en el estado.")
        return

    # ✅ Permitir edición de todos los campos (excepto comentario_id)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe
            return ('comentario_id',)
        return ()  # Al crear, todos editables

    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")

#-----------------------------------------------------------------------------------------
@admin.register(Politicas)
class PoliticasAdmin(AdminBaseMoneda):
    # ==========================
    # LISTADO
    # ==========================
    list_display = ('edad_min','edad_max',
        'valor_cred_min','valor_cred_max',
        'porcentaje_min_cuota_ini','porcentaje_max_cuota_ini',
        'tasa_min','tasa_max',
        'plazo_min','plazo_max',
        'dias_max_desembolso_atras',
    )

    # ==========================
    # SOLO LECTURA
    # ==========================
    readonly_fields = ('id',)

    # ==========================
    # FIELDSETS
    # ==========================
    fieldsets = (
        ('👤 Edad del Cliente', {
            'fields': ('edad_min', 'edad_max'),
            'description': 'Rango de edad permitido para solicitar crédito',
        }),
        ('💰 Valor del Crédito', {
            'fields': ('valor_cred_min', 'valor_cred_max'),
            'description': 'Formato automático con separador de miles y decimales',
        }),
        ('📊 Cuota Inicial (%)', {
            'fields': ('porcentaje_min_cuota_ini', 'porcentaje_max_cuota_ini'),
        }),
        ('📈 Tasas de Interés Mensual (%)', {
            'fields': ('tasa_min', 'tasa_max'),
        }),
        ('📅 Plazo del Crédito', {
            'fields': ('plazo_min', 'plazo_max'),
        }),
        ('⏱ Días permitidos para desembolsos atrasados', {
            'fields': ('dias_max_desembolso_atras',),
        }),
    )

    # ==========================
    # REGLAS DE NEGOCIO
    # ==========================
    def has_add_permission(self, request):
        """Solo se permite un registro de políticas"""
        return not Politicas.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Las políticas nunca se eliminan"""
        return False

    def changelist_view(self, request, extra_context=None):
        """
        Garantiza que siempre exista un registro de políticas
        """
        if not Politicas.objects.exists():
            Politicas.load().save()
        return super().changelist_view(request, extra_context)

#-----------------------------------------------------------------------------------------
class ConAtrasoFilter(admin.SimpleListFilter):  # esta clase debe ir antes de PrestamosAdmin
    title = 'Préstamos con atraso'
    parameter_name = 'con_atraso'

    def lookups(self, request, model_admin):
        return (
            ('si', 'Con atraso'),
            ('no', 'Al día'),
        )

    def queryset(self, request, queryset):
        from .models import Fechas_Sistema
        fecha_corte = date.today()
        fecha_sistema = Fechas_Sistema.objects.first()
        if fecha_sistema:
            fecha_corte = fecha_sistema.fecha_proceso_actual

        if self.value() == 'si':
            return queryset.filter(
                historia_prestamos__fecha_vencimiento__lt=fecha_corte,
                historia_prestamos__estado="PENDIENTE"
            ).distinct()
        if self.value() == 'no':
            return queryset.exclude(
                historia_prestamos__fecha_vencimiento__lt=fecha_corte,
                historia_prestamos__estado="PENDIENTE"
            ).distinct()
        return queryset

#-----------------------------------------------------------------------------------------
#   2025-11-15 Incluyo metodos para consultar cuotas pagadas, proyectadas, saldo pendiente
@admin.register(Prestamos)
class PrestamosAdmin(AdminBaseMoneda):
    list_display = [
        'prestamo_id', 'saldo_pendiente_formateado',
        'monto_atrasado_display',  # funciona
        'cuotas_atrasadas_display',  # funciona
        'dias_atraso_display',  # funciona
        'ver_estado_cuenta_link',
        'ver_plan_pagos_link',
        'fecha_desembolso',
    ]
    # nuevo 2025/12/19 pam
    search_fields = (
        'prestamo_id__prestamo_id','cliente_id__cliente_id',
        'cliente_id__nombre', 'cliente_id__apellido',
    )

    list_select_related = ('cliente_id', 'prestamo_id')

    list_filter = ('fecha_desembolso',)
    ordering = ('fecha_desembolso',)
    list_per_page = 14

    readonly_fields = ('prestamo_id','fecha_vencimiento',
        'fecha_desembolso','enlace_reporte',
        'saldo_pendiente_formateado', 'resumen_pagos',
    )

    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            'fields': (
                'tipo_tasa', 'tasa',
                'valor', 'valor_cuota_1',
                'valor_cuota_mensual', 'valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento')
        }),
    )

    def cliente_cliente_id(self, obj):
        return obj.cliente_id.cliente_id
    cliente_cliente_id.short_description = "Cliente ID"

    def cliente_nombre(self, obj):
        return f"{obj.cliente_id.nombre} {obj.cliente_id.apellido}"
    cliente_nombre.short_description = "Cliente"

    # ================================
    # QuerySet personalizado
    # ================================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    # ================================
    # Métodos de visualización (admin)
    # ================================

    def saldo_pendiente_formateado(self, obj):
        from django.utils.html import format_html
        saldo = obj.saldo_pendiente_actual()

        try:
            saldo_float = float(saldo) if saldo is not None else 0.0
            saldo_str = f"${saldo_float:,.2f}"
        except (TypeError, ValueError):
            saldo_str = "Error numérico"

        color = "red" if saldo_float > 0 else "green"
        return format_html('<strong style="color: {};">{}</strong>', color, saldo_str)

    saldo_pendiente_formateado.short_description = "Saldo Pendiente Actual"

    def cuotas_atrasadas_display(self, obj):
        from django.utils.html import format_html
        cantidad = obj.cuotas_atrasadas()  # ← método del modelo (correcto)
        color = "red" if cantidad > 0 else "green"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, cantidad)

    cuotas_atrasadas_display.short_description = "Cuotas Atrasadas"

    def dias_atraso_display(self, obj):
        from django.utils.html import format_html
        dias = obj.dias_atraso()  # ← método del modelo
        color = "red" if dias > 0 else "green"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, dias)

    dias_atraso_display.short_description = "Días de Atraso"

    def monto_atrasado_display(self, obj):
        from django.utils.html import format_html
        monto = obj.monto_atrasado()

        # Convertir a float y formatear como string PLANO
        try:
            monto_float = float(monto)
            monto_formateado = f"${monto_float:,.2f}"  # ← esto es un str plano
        except (TypeError, ValueError):
            monto_formateado = "Error numérico"

        color = "red" if monto_float > 0 else "green"
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, monto_formateado)

    monto_atrasado_display.short_description = "Monto Atrasado"

    def fecha_formateada(self, obj):
        return obj.fecha_desembolso.strftime('%Y-%m-%d')

    fecha_formateada.short_description = 'Fecha Ini.'
    fecha_formateada.admin_order_field = 'fecha_desembolso'

    def ver_plan_pagos_link(self, obj):
        prestamo_id_valor = obj.prestamo_id_id
        if prestamo_id_valor and isinstance(prestamo_id_valor, int) and prestamo_id_valor > 0:
            try:
                url = reverse('appfinancia:plan_pagos', kwargs={'prestamo_id': prestamo_id_valor})
                return format_html('<a href="{}" target="_blank">Ver Plan de Pagos</a>', url)
            except Exception:
                return format_html('<span style="color: red;">Error en URL</span>')
        return format_html('<span style="color: gray;">N/A</span>')

    ver_plan_pagos_link.short_description = 'Plan de Pagos'

    def resumen_pagos(self, obj):
        try:
            saldo = obj.saldo_pendiente_actual()
            if saldo is None:
                saldo = Decimal('0.00')
            valor = obj.valor or Decimal('0.00')
            total_pagado = valor - saldo
            return f"Saldo: ${float(saldo):,.2f} | Pagado: ${float(total_pagado):,.2f}"
        except Exception as e:
            return f"Error en cálculo: {str(e)}"

    resumen_pagos.short_description = "Resumen de Pagos"

    def enlace_reporte(self, obj):
        return format_html(
            '<a href="{}" class="button" target="_blank" style="background: #28a745; color: white; padding: 8px 12px; border-radius: 4px; text-decoration: none;">'
            '📥 Descargar Reporte Excel'
            '</a>',
            f"reporte_excel/{obj.prestamo_id}/"
        )

    enlace_reporte.short_description = "Reporte del Historial"

    # ================================
    # URLs y reportes
    # ================================

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'reporte_excel/<int:prestamo_id>/',
                self.admin_site.admin_view(self.generar_reporte_detalle),
                name='appfinancia_prestamos_reporte_excel',
            ),
        ]
        return custom_urls + urls

    def generar_reporte_detalle(self, request, prestamo_id):
        prestamo = get_object_or_404(Prestamos, prestamo_id=prestamo_id)
        buffer = generar_reporte_excel_en_memoria(prestamo_id)
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=reporte_prestamo_{prestamo_id}.xlsx'
        return response

    # ================================
    # Acción personalizada
    # ================================

    @admin.action(description="📥 Generar reporte Excel del historial")
    def generar_reporte_prestamo(modeladmin, request, queryset):
        if queryset.count() != 1:
            modeladmin.message_user(
                request,
                "❌ Seleccione exactamente UN préstamo para generar el reporte.",
                level='error'
            )
            return

        prestamo = queryset.first()
        # 🔑 Corrección clave: usar _id para obtener el valor numérico
        prestamo_id_valor = prestamo.prestamo_id_id  # ← esto es un entero

        buffer = generar_reporte_excel_en_memoria(prestamo_id_valor)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=reporte_prestamo_{prestamo_id_valor}.xlsx'
        return response

    actions = ['generar_reporte_prestamo']

    # ================================
    # Comportamiento en edición
    # ================================

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('cliente_id', 'fecha_creacion')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    #
    # -------------------- para el estado de cuenta: ----
    def ver_estado_cuenta_link(self, obj):
        from django.utils.html import format_html
        prestamo_id_valor = obj.prestamo_id_id

        if prestamo_id_valor and isinstance(prestamo_id_valor, int) and prestamo_id_valor > 0:
            try:
                from django.urls import reverse
                url = reverse('appfinancia:estado_cuenta', kwargs={'prestamo_id': prestamo_id_valor})
                return format_html('<a href="{}" target="_blank">Ver Estado de Cuenta</a>', url)
            except Exception:
                return format_html('<span style="color: red;">Error en URL</span>')
        else:
            return format_html('<span style="color: gray;">N/A</span>')

    ver_estado_cuenta_link.short_description = 'Estado de Cuenta'

#-----------------------------------------------------------------------------------------
class HistoriaPrestamosAdmin(admin.ModelAdmin):
    # Usamos los campos reales del modelo
    list_display = (
        'id',
        'prestamo_id',  # ← Añadido para ver a qué préstamo pertenece
        'numero_cuota',
        'concepto_id',
        'fecha_vencimiento',
        'monto_transaccion',
        'abono_capital',
        'estado',
        'fecha_efectiva',
        'fecha_proceso'
    )
    list_filter = ('prestamo_id',)
    # search_fields = ('prestamo_id','numero_cuota')
    # search_fields = ('prestamo_id__prestamo_id__exact','numero_cuota')
    search_fields = ('prestamo_id', 'numero_cuota')
    readonly_fields = (
        'id',
        'prestamo_id',
        'numero_cuota',
        'concepto_id',
        'fecha_vencimiento',
        'monto_transaccion',
        'fecha_efectiva',
        'fecha_proceso',
        'abono_capital',
        'intrs_ctes',
        'seguro',
        'fee',
        'usuario',
        'estado',
        'ordinal_interno',
        'numero_operacion',
        'tasa'
    )
    list_per_page = 14

    # Eliminamos fieldsets para mostrar todos los campos readonly
    # (o puedes personalizarlo sin detalle_breve)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

admin.site.register(Historia_Prestamos, HistoriaPrestamosAdmin)

#-----------------------------------------------------------------------------------------
@admin.register(Bitacora)
class BitacoraAdmin(admin.ModelAdmin):
    # Solo permite ver, no crea, edita ni elimina
    list_display = ('secuencial', 'fecha_hora', 'fecha_proceso', 'user_name', 'evento_realizado', 'proceso',
                    'resultado')
    readonly_fields = [field.name for field in Bitacora._meta.fields]  # Todos los campos son solo lectura
    ordering = ['-secuencial']  # Orden descendente por secuencial
    list_filter = ('fecha_proceso', 'user_name', 'proceso')  # Opcional: filtros
    search_fields = ('user_name', 'evento_realizado', 'proceso')  # Opcional: búsqueda

    # Deshabilitar la creación, edición y eliminación
    def has_add_permission(self, request):
        return False  # No permite crear

    def has_change_permission(self, request, obj=None):
        return False  # No permite editar

    def has_delete_permission(self, request, obj=None):
        return False  # No permite eliminar

# admin.site.register(Pagos_Archivos, Pagos_Archivos_Admin)
# admin.site.register(Pagos)  2025-12-14 comento esta linea porque no deja subir el server.-mags

#-----------------------------------------------------------------------------------------
class InBoxPagosCabezalForm(forms.ModelForm):
    archivo_subido = forms.FileField(
        required=True,
        label="Archivo a cargar",
        help_text="Seleccione un archivo .xls, .xlsx, .csv o .pdf"
    )

    class Meta:
        model = InBox_PagosCabezal
        fields = ["observaciones"]  # archivo va como campo adicional

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # CREAR → permitir edición
        if not self.instance or not self.instance.pk:
            return

        # EDITAR → deshabilitar campos
        self.fields["archivo_subido"].disabled = True
        self.fields["observaciones"].disabled = True

#-----------------------------------------------------------------------------------------
@admin.register(InBox_PagosCabezal)
class InBox_PagosCabezalAdmin(admin.ModelAdmin):
    form = InBoxPagosCabezalForm

    # Asegurar funcionalidad de collapse en fieldsets
    class Media:
        js = ("admin/js/jquery.init.js", "admin/js/collapse.js")

    # -------------------------------------------------------------
    # CONFIGURACIÓN ADMIN
    # -------------------------------------------------------------
    list_display = (
        'col_fecha',
        'valor_total',
        'col_cargados',
        'col_rechazados',
        'col_estado_archivo',
        'col_nombre_archivo',
    )

    list_filter = ('estado_proceso_archivo',)
    search_fields = ('nombre_archivo_id',)
    ordering = ('-fecha_carga_archivo',)
    list_per_page = 10

    readonly_fields = (
        "nombre_archivo_id",
        "fecha_carga_archivo",
        "valor_total",
        "registros_cargados",
        "registros_rechazados",
        "estado_proceso_archivo",
        "creado_por",
    )

    # -------------------------------------------------------------
    # ORGANIZAR FORMULARIO EN SECCIONES (FIELDSETS)
    # -------------------------------------------------------------
    fieldsets = (
        ("Datos del Archivo", {
            "fields": ("archivo_subido", "nombre_archivo_id", "observaciones"),
            #"fields": ("nombre_archivo_id", "observaciones"),
        }),
        ("Resultados", {
            "classes": ("collapse",),  # SECCIÓN OCULTA
            "fields": (
                "valor_total",
                "registros_cargados",
                "registros_rechazados",
                "estado_proceso_archivo",
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),  # SECCIÓN OCULTA
            "fields": ("fecha_carga_archivo", "creado_por"),
        }),
    )

    # -------------------------------------------------------------
    # ACCIONES PERSONALIZADAS
    # -------------------------------------------------------------
    actions = ["accion_procesar_archivo", "accion_anular_archivo"]

    # --------colores al campo nombre_archivo---
    def col_nombre_archivo(self, obj):
        # Mapeo de colores según el campo 'formato'
        colores = {
            '1-FORMATO PSE': {
                'bg': '#e3f2fd', 'fg': '#1565c0', 'icono': '📄'  # Azul (PDF)
            },
            '2-FORMATO ESTANDAR': {
                'bg': '#e8f5e9', 'fg': '#2e7d32', 'icono': '📊'  # Verde (XLS)
            },
            '3-FORMATO EXTRACTO BANCOLOMBIA': {
                'bg': '#fff9c4', 'fg': '#f57f17', 'icono': '💰'  # Amarillo (XLS Bancol)
            },
        }

        # Obtenemos la configuración o un estilo gris por defecto
        config = colores.get(obj.formato, {
            'bg': '#f5f5f5', 'fg': '#616161', 'icono': '📁'
        })

        # Retornamos el HTML con el estilo aplicado
        return format_html(
            '<span style="background-color: {}; color: {}; '
            'padding: 5px 10px; border-radius: 6px; '
            'font-weight: bold; font-size: 11px; display: inline-block; border: 1px solid rgba(0,0,0,0.05);">'
            '<span style="margin-right: 5px;">{}</span> {}</span>',
            config['bg'],
            config['fg'],
            config['icono'],
            obj.nombre_archivo_id  # Aquí mostramos el nombre real del archivo
        )

    # Configuración de la columna en el listado
    col_nombre_archivo.short_description = "Archivo / Formato"
    col_nombre_archivo.admin_order_field = "nombre_archivo_id"

    # ----------------------fin colores------------------------

    def col_fecha(self, obj):
        if obj.fecha_carga_archivo:
            return obj.fecha_carga_archivo.strftime('%Y-%m-%d %H:%M:%S')
        return "N/A"  # Manejar el caso donde la fecha es nula

    def col_cargados(self, obj):
        return obj.registros_cargados

    col_cargados.short_description = "Cargados"

    def col_rechazados(self, obj):
        return obj.registros_rechazados

    col_rechazados.short_description = "Rechazados"

    def col_estado_archivo(self, obj):
        return obj.estado_proceso_archivo

    col_estado_archivo.short_description = "Estado"

    # -----------------------------------------------------

    def accion_procesar_archivo(self, request, queryset):
        procesados = 0

        for obj in queryset:
            try:
                ok, msg = f_procesar_archivo(obj, request.user)

                if ok:
                    procesados += 1
                    self.message_user(
                        request,
                        f"✔ Archivo {obj.nombre_archivo_id} procesado: {msg}",
                        level=messages.SUCCESS,
                    )
                else:
                    self.message_user(
                        request,
                        f"⚠ Archivo {obj.nombre_archivo_id} con advertencias: {msg}",
                        level=messages.WARNING,
                    )

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error procesando {obj.nombre_archivo_id}: {e}",
                    level=messages.ERROR,
                )

        self.message_user(request, f"✔ Procesados {procesados} archivo(s).")

    accion_procesar_archivo.short_description = "Procesar archivo seleccionado"

    def accion_anular_archivo(self, request, queryset):
        anulados = 0

        for obj in queryset:
            try:
                ok, msg = f_anular_archivo(obj, request.user)

                if ok:
                    anulados += 1
                    self.message_user(
                        request,
                        f"✔ Archivo {obj.nombre_archivo_id} anulado",
                        level=messages.WARNING,
                    )
                else:
                    self.message_user(
                        request,
                        f"⚠ No se pudo anular {obj.nombre_archivo_id}: {msg}",
                        level=messages.ERROR,
                    )

            except Exception as e:
                self.message_user(
                    request,
                    f"❌ Error anulando {obj.nombre_archivo_id}: {e}",
                    level=messages.ERROR,
                )

        self.message_user(request, f"✔ Anulados {anulados} archivo(s).")

    accion_anular_archivo.short_description = "Anular archivo seleccionado"

    # -------------------------------------------------------------
    # GUARDADO + CARGA DEL ARCHIVO
    # -------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        archivo = form.cleaned_data.get("archivo_subido")

        # Usuario creador
        if not change:
            obj.creado_por = request.user

        # Asignar nombre del archivo
        if archivo:
            obj.nombre_archivo_id = archivo.name

        # Validación de duplicados
        if InBox_PagosCabezal.objects.filter(nombre_archivo_id=obj.nombre_archivo_id).exists():
            self.message_user(
                request,
                f"❌ Ya existe un archivo con el nombre '{obj.nombre_archivo_id}'.",
                level=messages.ERROR,
            )
            return

        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)

            # Procesar archivo automáticamente al cargarlo
            ok, msg = InBox_Pagos(
                archivo_pagos=archivo,
                usuario=request.user,
                cabezal=obj,
            )

            if ok:
                self.message_user(request, f"✔ Archivo procesado: {msg}", level=messages.SUCCESS)
            else:
                self.message_user(request, f"⚠ Advertencia: {msg}", level=messages.WARNING)

        except IntegrityError:
            self.message_user(
                request,
                "❌ Error: el nombre del archivo ya existe.",
                level=messages.ERROR
            )
            
#-----------------------------------------------------------------------------------------
@admin.register(Pagos)
class PagosAdmin(admin.ModelAdmin):
    list_display = (
        'pago_id',
        'col_prestamo_id_real',
        'col_cliente_id_real',
        'valor_pago_formatted',
        'estado_pago',
        'col_fecha_pago',
    )
    list_filter = (
        'estado_pago',
        'estado_conciliacion',
        'fecha_pago',
        'canal_red_pago',
        'banco_origen',
    )
    search_fields = (
        '=pago_id',
        '=prestamo_id_real',
        # 'nombre_archivo_id__nombre_archivo_id',
        # 'prestamo_id_reportado',
        # 'cliente_id_reportado',
        'ref_bancaria',
        'ref_red',
    )
    ordering = ('-fecha_pago', '-pago_id')
    readonly_fields = (
        'pago_id',
        'fecha_carga_archivo',
        'creado_por',
        'fecha_aplicacion_pago',
        'fecha_conciliacion',
    )

    fieldsets = (
        ('Archivo Origen', {
            'fields': ('nombre_archivo_id', 'fecha_carga_archivo')
        }),
        ('Datos del Pago Reportado', {
            'fields': (
                'fecha_pago', 'hora_pago',
                'valor_pago',
                'estado_transaccion_reportado',
                'banco_origen', 'cuenta_bancaria', 'tipo_cuenta_bancaria',
                'canal_red_pago',
                ('ref_bancaria', 'ref_red'),
                ('ref_cliente_1', 'ref_cliente_2', 'ref_cliente_3'),
            )
        }),
        ('Identificación Reportada', {
            'fields': (
                'cliente_id_reportado',
                'prestamo_id_reportado',
                'poliza_id_reportado',
            )
        }),
        ('Conciliación y Aplicación', {
            'fields': (
                'estado_pago',
                'estado_conciliacion',
                'fecha_conciliacion',
                'fecha_aplicacion_pago',
                'cliente_id_real',
                'prestamo_id_real',
                'poliza_id_real',
            )
        }),

        ('Auditoría', {
            'fields': ('observaciones', 'creado_por'),
        }),
    )

    actions = ['aplicar_pagos_conciliados']

    # Métodos personalizados
    def col_prestamo_id_real(self, obj):
        if obj.prestamo_id_real:
            return obj.prestamo_id_real
        return "N/A"  # Manejar el caso donde la fecha es nula

    col_prestamo_id_real.short_description = "Prestamo id"

    def col_cliente_id_real(self, obj):
        if obj.cliente_id_real:
            return obj.cliente_id_real
        return "N/A"  # Manejar el caso donde la fecha es nula

    col_cliente_id_real.short_description = "Cliente id"

    def col_fecha_pago(self, obj):
        if obj.fecha_pago:
            return obj.fecha_pago.strftime('%Y-%m-%d')
        return "N/A"  # Manejar el caso donde la fecha es nula

    col_fecha_pago.short_description = "Fecha Pago"

    def valor_pago_formatted(self, obj):
        return f"${obj.valor_pago:,.2f}"

    valor_pago_formatted.short_description = "Valor Pago"

    def estado_pago_colored(self, obj):
        from django.utils.html import format_html
        colores = {
            'Recibido': '#1f77b4',
            'pendiente': '#ff7f0e',
            'rechazado': '#d62728',
            'conciliado': '#2ca02c',
            'aplicado': '#9467bd',
            'reversado': '#8c564b',
            'acreedores': '#17becf',
        }
        color = colores.get(obj.estado_pago, '#7f7f7f')
        return f'<span style="color:{color}; font-weight:bold;">{obj.get_estado_pago_display()}</span>'

    estado_pago_colored.short_description = "Estado"
    estado_pago_colored.allow_tags = True
    estado_pago_colored.admin_order_field = 'estado_pago'

    # Guardar usuario actual
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

        # ← ¡Importante!

    @admin.action(description="✅ Aplicar pagos conciliados")
    def aplicar_pagos_conciliados(modeladmin, request, queryset):
        """
        Action para el Django Admin: aplica pagos en estado 'conciliado'.
        - Procesa solo los pagos seleccionados con estado_pago = 'conciliado'.
        - Valida que tengan prestamo_id_real (entero).
        - Usa transaction.atomic() para garantizar integridad.
        - Llama a aplicar_pago(pago_id, usuario) para cada pago.
        - Registra en Bitacora en caso de error.
        - Muestra mensajes detallados con préstamo y ref_bancaria.
        """
        # Filtrar solo pagos conciliados
        pagos_conciliados = queryset.filter(estado_pago="conciliado")
        total_seleccionados = queryset.count()
        total_conciliados = pagos_conciliados.count()

        if total_conciliados == 0:
            if total_seleccionados == 0:
                messages.warning(request, "⚠️ No hay pagos seleccionados.")
            else:
                messages.warning(request, "⚠️ Ninguno de los pagos seleccionados está en estado 'conciliado'.")
            return

        # Validar que todos los pagos tengan prestamo_id_real (entero)
        pagos_sin_prestamo = pagos_conciliados.filter(prestamo_id_real__isnull=True)
        if pagos_sin_prestamo.exists():
            refs_invalidas = []
            for pago in pagos_sin_prestamo:
                ref = pago.ref_bancaria or f"ID {pago.pago_id}"
                refs_invalidas.append(ref)
            messages.error(
                request,
                f"❌ Los siguientes pagos no tienen préstamo asignado: {', '.join(refs_invalidas)}. "
                "Verifique la conciliación antes de aplicar."
            )
            return

        try:
            with transaction.atomic():
                errores = []
                exitosos = 0

                for pago in pagos_conciliados:
                    try:
                        # Llamar a la función de aplicación (pago_id es entero, prestamo_id_real es entero)
                        from .utils import aplicar_pago
                        resultado = aplicar_pago(pago.pago_id, request.user.username)
                        exitosos += 1

                    except Exception as e:
                        # Capturar error con datos útiles para el usuario
                        prestamo_id = pago.prestamo_id_real or "N/A"
                        ref_bancaria = pago.ref_bancaria or f"ID {pago.pago_id}"
                        error_detalle = f"Préstamo {prestamo_id} (Ref: {ref_bancaria}): {str(e)}"
                        errores.append(error_detalle)

                # Si hubo errores, lanzamos excepción para rollback
                if errores:
                    raise Exception("; ".join(errores))

            # Éxito total
            messages.success(
                request,
                f"✅ Se aplicaron exitosamente {exitosos} pagos conciliados."
            )

        except Exception as e:
            error_msg = f"❌ Error al aplicar pagos: {str(e)}"
            messages.error(request, error_msg)

            # Registrar en bitácora
            Bitacora.objects.create(
                fecha_proceso=timezone.now().date(),
                user_name=request.user.username,
                evento_realizado='APLICAR_PAGOS_CONCILIADOS',
                proceso='ERROR',
                resultado=error_msg[:500]  # Evitar truncamiento en DB
            )

#-----------------------------------------------------------------------------------------
@admin.register(ConsultasReportesProxy)
class ConsultasReportesAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('causacion/', self.admin_site.admin_view(consulta_causacion_view),
                 name='appfinancia_consultasreportes_causacion'),
            path('balance-operaciones/', self.admin_site.admin_view(balance_operaciones_view),
                 name='appfinancia_consultasreportes_balance'),
            path('prestamos-vencidos/', self.admin_site.admin_view(prestamos_vencidos_view),
                 name='appfinancia_consultasreportes_vencidos')
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        context = {
            'title': 'Consultas y Reportes',
            'site_title': admin.site.site_title,
            'site_header': admin.site.site_header,
            'opts': self.model._meta,
            'causacion_url': reverse('admin:appfinancia_consultasreportes_causacion'),
            'balance_url': reverse('admin:appfinancia_consultasreportes_balance'),
            'vencidos_url': reverse('admin:appfinancia_consultasreportes_vencidos'),
        }
        return render(request, 'admin/consultas_reportes_index.html', context)

    # ... (permisos igual que antes)
    # Permisos
    def has_module_permission(self, request):
        return request.user.has_perm('appfinancia.puede_consultar_causacion')

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

#-----------------------------------------------------------------------------------------
@admin.register(InBox_PagosDetalle)
class InBox_PagosDetalleAdmin(admin.ModelAdmin):

    # ==================================================
    # CONFIGURACIÓN GENERAL
    # ==================================================
    raw_id_fields = ("cliente_id_real", "prestamo_id_real")

    class Media:
        js = ("admin/js/jquery.init.js", "admin/js/collapse.js")

    list_display = (
        'col_pago_id',
        'lote_pse',
        'col_fragmento',
        'col_clase_movimiento',
        'col_estado_pago',
        'col_conciliacion',
        'col_cliente',
        'col_prestamo',
        'valor_pago',
        'col_fecha_pago',
    )
    '''
    list_filter = (
        'estado_pago',
        'estado_conciliacion',
        'estado_fragmentacion',
        'clase_movimiento',
        'fecha_pago',
    )
    '''
    
    list_filter = (
        'nombre_archivo_id',
        ('fecha_carga_archivo', DateFieldListFilter),
        'lote_pse',
        'pago_id',
    
        # filtros que ya tenías
        'estado_pago',
        'estado_conciliacion',
        'estado_fragmentacion',
        'clase_movimiento',
    )

    search_fields = (
        'pago_id__exact',
        'lote_pse__exact',
        #'cliente_id_real__numero_documento__exact',
    )

    ordering = ('-pago_id',)
    list_per_page = 20

    # ==================================================
    # 🔒 BLOQUEO TOTAL DE EDICIÓN
    # ==================================================
    def has_add_permission(self, request):
        return False
     
    def has_change_permission(self, request, obj=None):
        return False
     
    def has_delete_permission(self, request, obj=None):
        return False

    # ==================================================
    # FIELDSETS (SOLO VISUAL)
    # ==================================================
    fieldsets = (
        ("📂 ARCHIVO DE ORIGEN", {
            "fields": ("nombre_archivo_id", "fecha_carga_archivo"),
        }),
        ("🔗 IDENTIFICADORES", {
            "fields": ("pago_id", "lote_pse", "fragmento_de"),
        }),
        ("🏦 DATOS BANCARIOS", {
            "fields": (
                "banco_origen",
                "cuenta_bancaria",
                "tipo_cuenta_bancaria",
                "canal_red_pago",
                "ref_bancaria",
                "ref_red",
                "ref_cliente_1",
                "ref_cliente_2",
                "ref_cliente_3",
            ),
        }),
        ("📑 INFORMACIÓN REPORTADA", {
            "fields": (
                "clase_movimiento",
                "estado_fragmentacion",
                "cliente_id_reportado",
                "prestamo_id_reportado",
                "poliza_id_reportado",
            ),
        }),
        ("🔍 CONCILIACIÓN", {
            "fields": (
                "cliente_id_real",
                "prestamo_id_real",
                "poliza_id_real",
                "fecha_conciliacion",
                "estado_conciliacion",
            ),
        }),
        ("💰 PAGO", {
            "fields": ("fecha_pago", "valor_pago", "estado_pago"),
        }),
        ("🕒 AUDITORÍA", {
            "fields": ("creado_por", "observaciones"),
        }),
    )

    # ==================================================
    # 📊 ACCIONES DE REPORTES
    # ==================================================
    actions = (
        "action_reporte_pagos_pdf",
        "action_reporte_pagos_excel",
    )

    @admin.action(description="📄 Exportar pagos a PDF")
    def action_reporte_pagos_pdf(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request,
                "No hay pagos para exportar.",
                level=messages.WARNING
            )
            return

        generar_reporte_pagos_pdf(
            queryset=queryset,
            usuario=request.user
        )

        self.message_user(
            request,
            "✔ Reporte PDF generado correctamente.",
            level=messages.SUCCESS
        )

    @admin.action(description="📊 Exportar pagos a Excel")
    def action_reporte_pagos_excel(self, request, queryset):
        if not queryset.exists():
            self.message_user(
                request,
                "No hay pagos para exportar.",
                level=messages.WARNING
            )
            return

        return generar_reporte_pagos_excel(queryset)

    # ==================================================
    # 🔵 FUNCIONES DE COLUMNA (NO SE TOCAN)
    # ==================================================
    def col_pago_id(self, obj):
        return obj.pago_id
    col_pago_id.short_description = "ID"

    def col_fragmento(self, obj):
        return obj.fragmento_de
    col_fragmento.short_description = "Frag"

    def col_cliente(self, obj):
        return obj.cliente_id_real
    col_cliente.short_description = "Cliente"

    def col_prestamo(self, obj):
        return obj.prestamo_id_real
    col_prestamo.short_description = "Préstamo"

    def col_estado_pago(self, obj):
        return obj.estado_pago
    col_estado_pago.short_description = "Estado"

    def col_conciliacion(self, obj):
        return obj.estado_conciliacion
    col_conciliacion.short_description = "Conci"

    def col_fecha_pago(self, obj):
        return obj.fecha_pago.strftime('%Y-%b-%d') if obj.fecha_pago else "N/A"
    col_fecha_pago.short_description = "Fecha Pago"

    # ==================================================
    # 🎨 CLASE DE MOVIMIENTO CON COLORES
    # ==================================================
    def col_clase_movimiento(self, obj):
        colores = {
            'PAGO_PSE': {'bg': '#e3f2fd', 'fg': '#1565c0', 'label': 'PAGO PSE'},
            'PAGO_BANCOL': {'bg': '#fff9c4', 'fg': '#f57f17', 'label': 'BANCOLOMBIA'},
            'LOTE_PSE': {'bg': '#e8f5e9', 'fg': '#2e7d32', 'label': 'LOTE PSE'},
            'EXCLUIDO': {'bg': '#f5f5f5', 'fg': '#616161', 'label': 'EXCLUIDO'},
        }

        config = colores.get(
            obj.clase_movimiento,
            {'bg': '#eeeeee', 'fg': '#424242', 'label': obj.clase_movimiento}
        )

        return format_html(
            '<span style="background-color:{}; color:{}; '
            'padding:4px 10px; border-radius:12px; '
            'font-size:10px; font-weight:bold;">{}</span>',
            config['bg'], config['fg'], config['label']
        )

    col_clase_movimiento.short_description = "Clase"
    col_clase_movimiento.admin_order_field = "clase_movimiento"

    # Generar reporte de conciliación:
    # ==================================================
    # URL PERSONALIZADA DEL ADMIN
    # ==================================================
    '''
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "reporte-conciliacion/",
                self.admin_site.admin_view(self.reporte_conciliacion_view),
                name="reporte_conciliacion_excel",
            ),
        ]
        return custom_urls + urls
    
    # ==================================================
    # VISTA DEL REPORTE (ADMIN)
    # ==================================================
    def reporte_conciliacion_view(self, request):
        return generar_reporte_conciliacion_excel(request)
    '''
    def get_urls(self):
	    urls = super().get_urls()
	    custom_urls = [
	        path(
	            "reporte-conciliacion/",
	            self.admin_site.admin_view(self.reporte_conciliacion_view),
	            name="reporte_conciliacion",
	        ),
	    ]
	    return custom_urls + urls
	
	
    def reporte_conciliacion_view(self, request):
	    return generar_reporte_conciliacion_excel(request)
    
    # filtros
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["reporte_conciliacion_url"] = "reporte-conciliacion/"
        return super().changelist_view(request, extra_context)

#-----------------------------------------------------------------------------------------
@admin.register(PagosParaRegularizar)
class PagosParaRegularizarAdmin(InBox_PagosDetalleAdmin):

    raw_id_fields = ("cliente_id_real", "prestamo_id_real")

    # =====================================================
    # QUERYSET
    # =====================================================
    def get_queryset(self, request):
        return super().get_queryset(request).filter(estado_pago="A_PROCESAR")

    # =====================================================
    # LISTADO
    # =====================================================
    list_display = (
        "col_pago_id",
        "col_lote_pse",
        "col_fragmento",
        "col_clase_movimiento",
        "col_estado_pago",
        "col_conciliacion",
        "col_cliente",
        "col_prestamo",
        "valor_pago",
        "col_fecha_pago",
        "col_fragmentacion",
    )

    list_filter = (
        "estado_pago",
        "estado_conciliacion",
        "estado_fragmentacion",
        "clase_movimiento",
    )

    search_fields = (
        "cliente_id_real__exact",
        "pago_id__exact",
        "lote_pse__exact",
    )

    ordering = ("-pago_id",)

    # =====================================================
    # PERMISOS
    # =====================================================
    #def has_add_permission(self, request):
    #    return True
    
    def has_add_permission(self, request):
        return False


    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    # =====================================================
    # SOLO LECTURA
    # =====================================================
    readonly_fields = (
        "pago_id",
        "nombre_archivo_id",
        "fecha_carga_archivo",
        "creado_por",
        "clase_movimiento",
        "lote_pse",
        "fecha_pago",
        "valor_pago",
        "estado_pago",
        "fecha_conciliacion",
        "estado_conciliacion",
        "fragmento_de",
        "canal_red_pago",
        "ref_bancaria",
        "ref_red",
        "ref_cliente_1",
        "ref_cliente_2",
        "ref_cliente_3",
        "prestamo_id_reportado",
        "cliente_id_reportado",
    )

    # =====================================================
    # FIELDSETS
    # =====================================================
    fieldsets = (
        ("INFORMACIÓN DEL PAGO", {
            "classes": ("collapse",),
            "fields": (
                ("nombre_archivo_id", "fecha_carga_archivo"),
                ("fecha_pago", "valor_pago", "estado_pago"),
                ("clase_movimiento", "pago_id", "lote_pse", "fragmento_de"),
                ("fecha_conciliacion", "estado_conciliacion"),
            ),
        }),
        ("ASIGNACIÓN Y REFERENCIAS", {
            "fields": (
                ("canal_red_pago", "ref_bancaria", "ref_red"),
                ("ref_cliente_1", "ref_cliente_2", "ref_cliente_3"),
                ("cliente_id_reportado", "prestamo_id_reportado"),
                ("prestamo_id_real",),
                ("estado_fragmentacion",),
            ),
        }),
    )

    # =====================================================
    # ACCIONES
    # =====================================================
    actions = (
        "action_conciliar_movimientos_seleccionados",
        "action_confirmar_pagos",
    )

    # =====================================================
    # BOTÓN DESCARGA RESUMEN (CHANGE LIST)
    # =====================================================
    def boton_descargar_resumen(self, request):
        conciliacion_id = (
            self.get_queryset(request)
            .exclude(conciliacion_id__isnull=True)
            .aggregate(max_id=Max("conciliacion_id"))
            .get("max_id")
        )

        if not conciliacion_id:
            return ""

        url = f"descargar-resumen-conciliacion/?conciliacion_id={conciliacion_id}"

        return format_html(
            '<a class="button" href="{}">📥 Descargar Resumen Conciliación</a>',
            url
        )

    # =====================================================
    # URL ADMIN
    # =====================================================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "descargar-resumen-conciliacion/",
                self.admin_site.admin_view(self.descargar_resumen_conciliacion_view),
                name="descargar_resumen_conciliacion",
            ),
        ]
        return custom_urls + urls

    # =====================================================
    # VIEW DESCARGA
    # =====================================================
    def descargar_resumen_conciliacion_view(self, request):
        from django.http import FileResponse, Http404
        from appfinancia.models import InBox_PagosDetalle
        from appfinancia.services.conciliacion import reporte_resumen_conciliacion
        import os
    
        conciliacion_id = request.GET.get("conciliacion_id")
    
        # ✅ ENTERPRISE: tomar la última conciliación si no viene parámetro
        if not conciliacion_id:
            conciliacion_id = (
                InBox_PagosDetalle.objects
                .exclude(conciliacion_id__isnull=True)
                .order_by("-conciliacion_id")
                .values_list("conciliacion_id", flat=True)
                .first()
            )
    
        if not conciliacion_id:
            raise Http404("No existe ninguna conciliación generada aún")
    
        ruta = reporte_resumen_conciliacion(conciliacion_id)
    
        return FileResponse(
            open(ruta, "rb"),
            as_attachment=True,
            filename=os.path.basename(ruta),
        )
        
    # =====================================================
    # COLORES CLASE MOVIMIENTO
    # =====================================================
    def col_clase_movimiento(self, obj):
        colores = {
            "PAGO_PSE": ("#e3f2fd", "#1565c0", "PAGO PSE"),
            "PAGO_BANCOL": ("#fff9c4", "#f57f17", "BANCOLOMBIA"),
            "LOTE_PSE": ("#e8f5e9", "#2e7d32", "LOTE PSE"),
            "EXCLUIDO": ("#f5f5f5", "#616161", "EXCLUIDO"),
        }

        bg, fg, label = colores.get(
            obj.clase_movimiento,
            ("#ffffff", "#000000", obj.clase_movimiento)
        )

        return format_html(
            '<span style="background:{};color:{};padding:4px 12px;border-radius:12px;font-size:10px;font-weight:bold;">{}</span>',
            bg, fg, label
        )

    col_clase_movimiento.short_description = "Clase"
    col_clase_movimiento.admin_order_field = "clase_movimiento"

    # =====================================================
    # COLUMNAS SIMPLES
    # =====================================================
    def col_fecha_pago(self, obj):
        return obj.fecha_pago.strftime("%Y-%b-%d") if obj.fecha_pago else "N/A"
    col_fecha_pago.short_description = "Fecha Pago"
    
    def col_pago_id(self, obj):
        return obj.pago_id
    col_pago_id.short_description = "ID"
    
    def col_lote_pse(self, obj):
        return obj.lote_pse
    col_lote_pse.short_description = "Lote"
    
    def col_fragmento(self, obj):
        return obj.fragmento_de
    col_fragmento.short_description = "Frag"
    
    def col_cliente(self, obj):
        return obj.cliente_id_real
    col_cliente.short_description = "Cliente"
    
    def col_prestamo(self, obj):
        return obj.prestamo_id_real
    col_prestamo.short_description = "Préstamo"
    
    def col_estado_pago(self, obj):
        return obj.estado_pago
    col_estado_pago.short_description = "Estado"
    
    def col_conciliacion(self, obj):
        return obj.estado_conciliacion
    col_conciliacion.short_description = "Conci"
    
    # =====================================================
    # FRAGMENTACIÓN
    # =====================================================
    def col_fragmentacion(self, obj):
        if obj.clase_movimiento == "LOTE_PSE":
            return "-"
    
        estado = (obj.estado_fragmentacion or "").strip()
    
        if estado == "FRAGMENTADO":
            return format_html('<span style="color:#9e9e9e;">FRAGMENTADO</span>')
    
        if not obj.cliente_id_real or not obj.prestamo_id_real:
            return format_html(
                '<span style="color:#bcbcbc; font-style: italic;">Sin asignar</span>'
            )
    
        if estado == "A_FRAGMENTAR":
            url = reverse("appfinancia:fragmentar_pago", args=[obj.pago_id])
            return format_html(
                '<a href="{}" '
                'style="background:#f44336;color:white;padding:5px 10px;'
                'border-radius:6px;font-size:10px;font-weight:bold;">'
                '⚡ A_FRAGMENTAR</a>',
                url
            )
    
        return format_html(
            '<span style="color:#757575;font-size:10px;">{}</span>',
            estado or "-"
        )

    col_fragmentacion.short_description = "Fragmentación"
    col_fragmentacion.admin_order_field = "estado_fragmentacion"

    # =====================================================
    # ACTION CONFIRMAR PAGOS
    # =====================================================
    def action_confirmar_pagos(self, request, queryset):
        ok, msg = confirmar_pagos(queryset, request.user)
        self.message_user(
            request,
            msg,
            level=messages.SUCCESS if ok else messages.ERROR
        )

    action_confirmar_pagos.short_description = "Confirmar pagos seleccionados"
    
    # =====================================================
    # ASIGNAR CLIENTE Y PRESTAMO
    # =====================================================
    def save_model(self, request, obj, form, change):
        # 1. Lógica de integridad:
        # Si hay un préstamo seleccionado,
        # forzamos que el cliente sea el dueño de ese préstamo.
        if obj.prestamo_id_real:
            obj.cliente_id_real = obj.prestamo_id_real.cliente_id
    
        # 2. Auditoría: asignar usuario creador
        if not obj.pk:
            obj.creado_por = request.user
    
        # 3. Guardado final
        super().save_model(request, obj, form, change)

    # =====================================================
    # ACTION CONCILIAR
    # =====================================================
    def action_conciliar_movimientos_seleccionados(self, request, queryset):
        movimientos = queryset.filter(clase_movimiento="LOTE_PSE")
        num_conciliacion = get_next_conciliacion_id()

        conciliados = 0
        asignados = 0

        for mov in movimientos:
            candidatos = InBox_PagosDetalle.objects.filter(
                clase_movimiento="PAGO_PSE",
                estado_pago="A_PROCESAR",
                estado_conciliacion="NO",
                lote_pse__isnull=True,
            )

            ok, _, detalles = conciliacion_por_movimiento(mov, candidatos, num_conciliacion)
            if ok:
                conciliados += 1
                asignados += detalles.get("hijos_creados", 0)

        self.message_user(
            request,
            f"{conciliados} movimientos conciliados. Pagos asignados: {asignados}",
            level=messages.SUCCESS
        )

#-----------------------------------------------------------------------------------------
@admin.register(Financiacion)
class FinanciacionAdmin(AdminBaseMoneda):
    # ==========================
    # TEMPLATE PERSONALIZADO
    # ==========================
    # change_form_template = "admin/appfinancia/financiacion/change_form.html"

    # ==========================
    # LISTADO
    # ==========================
    list_display = (
        "col_solicitud_id",
        "col_financiacion_id",
        "col_nombre_completo",
        "col_numero_documento",
        "email_origen",
        "col_fecha_solicitud",
        # "estado_solicitud",
        "acciones_estado",
    )

    list_filter = (
        "estado_solicitud",
        "cliente_nuevo",
        "cliente_vetado",
        "seguro_vida",
        "fecha_creacion",
    )

    search_fields = (
        "financiacion_id",
        "nombre_completo",
        "numero_documento",
        "correo_electronico",
        "email_origen",
        "asesor",
        "agencia",
    )

    ordering = ("-fecha_creacion",)
    list_per_page = 25

    # ==========================
    # SOLO LECTURA
    # ==========================
    readonly_fields = (
        "solicitud_id",
        "message_id",
        "fecha_creacion",
        "email_origen",
        "asunto",
        "cliente_nuevo",
        "cliente_vetado",
    )

    # ==========================
    # FIELDSETS
    # ==========================
    fieldsets = (
        ("📨 DATOS DEL CORREO", {
            "fields": (
                "message_id",
                "email_origen",
                "asunto",
                "fecha_solicitud",
            ),
            'classes': ('collapse',)
        }),
        ("👤 DATOS DEL CLIENTE", {
            "fields": (
                "nombre_completo",
                "tipo_documento",
                "numero_documento",
                "telefono",
                "correo_electronico",
            ),
            'classes': ('collapse',)
        }),
        ("🏢 DATOS COMERCIALES", {
            "fields": (
                "asesor",
                "agencia",
                "numero_cuotas",
            ),
            'classes': ('collapse',)
        }),
        ("💰 VALORES", {
            "fields": (
                "valor_prestamo",
                "valor_cuota_inicial",
                "valor_seguro_vida",
                "tasa",
            )
        }),
        ("📄 PÓLIZA", {
            "fields": (
                "placas",
                "numero_poliza",
                "seguro_vida",
            )
        }),
        ("📎 ADJUNTOS", {
            "fields": (
                "adjunta_cedula",
                "adjunta_poliza",
                "adjunta_segurovida",
            )
        }),
        ("⚙️ VALIDACIONES Y CHECK LIST", {
            "fields": (
                "cliente_nuevo",
                "cliente_vetado",
                "info_cliente_valida",
                "adjunta_documento_identificacion",
                "adjunta_poliza_seguro",
                "adjunta_autorizacion_datos",
                "adjunta_seguro_vida",
            )
        }),
        ("📌 ESTADO DE LA SOLICITUD", {
            "fields": (
                "estado_solicitud",
            )
        }),
        ("🕒 AUDITORÍA", {
            "fields": (
                "fecha_creacion",
            )
        }),
    )

    # ==========================
    # ACCIONES MASIVAS
    # ==========================
    actions = (
        "leer_correos_financiacion",
        "aprobar_solicitudes",
        "negar_solicitudes",
    )

    @admin.action(description="📨 Leer correos de financiación (IMAP)")
    def leer_correos_financiacion(self, request, queryset):
        try:
            procesar_emails()
            self.message_user(
                request,
                "✔ Correos leídos correctamente.",
                level=messages.SUCCESS
            )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Error leyendo correos: {e}",
                level=messages.ERROR
            )

    @admin.action(description="✅ Aprobar solicitudes seleccionadas")
    #@admin.action(description="✔ Aprobar financiación")
    def aprobar_solicitudes(modeladmin, request, queryset):
    
        if queryset.count() != 1:
            messages.error(
                request,
                "Debe seleccionar UNA sola financiación para aprobar."
            )
            return
    
        financiacion = queryset.first()
        
        #probar solo la impresión:
        #f_plan_pagos_cuota_fija(102)
        #f_generar_pdf_plan_pagos(102)
        #f_correo_aprobacion(102)
        #return
        
        try:
            f_aprobar_financiacion(
                solicitud_id=financiacion.solicitud_id,
                usuario=request.user
            )
    
            messages.success(
                request,
                "✅ Financiación aprobada correctamente."
            )
    
        except Exception as e:
            # 👇 NUNCA iterar errores
            messages.error(
                request,
                f"❌ Error al aprobar la financiación: {str(e)}"
            )
    
    '''
    def aprobar_solicitudes(self, request, queryset):   
        pendientes = queryset.filter(estado_solicitud="RECIBIDO")
        count = pendientes.update(estado_solicitud="APROBADO")

        self.message_user(
            request,
            f"{count} solicitud(es) aprobadas." if count else
            "No hay solicitudes en estado RECIBIDO.",
            level=messages.SUCCESS if count else messages.WARNING
        )
        '''

    @admin.action(description="❌ Negar solicitudes seleccionadas")
    def negar_solicitudes(self, request, queryset):
        pendientes = queryset.filter(estado_solicitud="RECIBIDO")
        count = pendientes.update(estado_solicitud="NEGADO")

        self.message_user(
            request,
            f"{count} solicitud(es) negadas." if count else
            "No hay solicitudes en estado RECIBIDO.",
            level=messages.SUCCESS if count else messages.WARNING
        )

    # ==========================
    # ESTADO VISUAL
    # ==========================
    def acciones_estado(self, obj):
        colores = {
            "RECIBIDO": "orange",
            "APROBADO": "green",
            "NEGADO": "red",
        }
        iconos = {
            "RECIBIDO": "⏳",
            "APROBADO": "✔",
            "NEGADO": "✖",
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{} {}</span>',
            colores.get(obj.estado_solicitud, "gray"),
            iconos.get(obj.estado_solicitud, ""),
            obj.estado_solicitud,
        )

    acciones_estado.short_description = "Estado"

    def col_solicitud_id(self, obj):
        return obj.solicitud_id

    col_solicitud_id.short_description = "ID"

    def col_financiacion_id(self, obj):
        return obj.financiacion_id

    col_financiacion_id.short_description = "FIN-ID"

    def col_nombre_completo(self, obj):
        return obj.nombre_completo

    col_financiacion_id.short_description = "NOMBRE"

    def col_numero_documento(self, obj):
        return obj.numero_documento

    col_numero_documento.short_description = "DOCUMENTO"

    def col_fecha_solicitud(self, obj):
        if obj.fecha_solicitud:
            return obj.fecha_solicitud.strftime('%Y-%m-%d %H:%M:%S')
        return "N/A"

    # ==========================
    # URL PERSONALIZADA DEL ADMIN
    # ==========================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "leer-correos/",
                self.admin_site.admin_view(self.leer_correos_view),
                name="appfinancia_financiacion_leer_correos",
            ),
        ]
        return custom_urls + urls

    # ==========================
    # VISTA BOTÓN CHANGE_FORM
    # ==========================
    def leer_correos_view(self, request):
        try:
            procesar_emails()
            self.message_user(
                request,
                "✔ Correos de financiación procesados correctamente.",
                level=messages.SUCCESS,
            )
        except Exception as e:
            self.message_user(
                request,
                f"❌ Error procesando correos: {e}",
                level=messages.ERROR,
            )
        return redirect("..")

#-----------------------------------------------------------------------------------------
