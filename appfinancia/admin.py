from decimal import Decimal
from django.contrib import admin, messages

# appfinancia/admin.py (fragmento)
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

#from .models import Desembolsos,  Bitacora
#from . import utils  # importa las funciones definidas en utils.py

from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from .models import Desembolsos, Comentarios_Prestamos, Comentarios
from django.core.exceptions import ValidationError
from .utils import cerrar_periodo_interes, aplicar_pago_cuota_inicial
from .views import generar_excel_estado_cuenta, redirect, ver_comprobante_pago 

# Register your models here.

# inicio-para personalizar el Panel Administrador Django 20251031
# Personalización del título y encabezados
admin.site.site_header = "Sistema Financia Seguros - Panel de Administración"
admin.site.site_title = "Sistema Financia Admin"
admin.site.index_title = "Gestión del Sistema Financiero"

# admin.py
# appfinancia/admin.py
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse


# fin-para personalizar el Panel Administrador Django  ************

#Para los formatos de número
#--------------------------------------------------------------------------------------



# appfinancia/admin.py
#from django.contrib import admin
#from django import forms
from .models import Fechas_Sistema
from django import forms

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

@admin.register(Fechas_Sistema)
class FechasSistemaAdmin(admin.ModelAdmin):
    form = FechasSistemaForm
    list_display = (
        'fecha_proceso_actual',
        'estado_sistema_colored',
        'modo_fecha_sistema',
        'fecha_ultima_modificacion',
        'cambiado_por',
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
        
           

#1---------------------------------------------------------------------------------------*
from .models import Tipos_Identificacion

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

#2---------------------------------------------------------------------------------------*
from .models import Asesores

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
        
#3---------------------------------------------------------------------------------------*
from .models import Aseguradoras

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

        
#4---------------------------------------------------------------------------------------*
#from .models import Tasas
#@admin.register(Tasas)
#class TasasAdmin(admin.ModelAdmin):
#    list_display = ['tipo_tasa', 'valor_tasa']  


from .models import Tasas

@admin.register(Tasas)
class TasasAdmin(admin.ModelAdmin):
    list_display = ('tipo_tasa', 'fecha_aplica', 'tasa')
    list_filter = ('tipo_tasa',)
    ordering = ('-fecha_aplica', 'tipo_tasa') # Verás siempre la más reciente arriba

    # Evitar que se edite tipo_tasa después de creado (es clave primaria)
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe (modo edición)
            return ('tipo_tasa',)
        return ()

#5---------------------------------------------------------------------------------------*
from .models import Departamentos

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

#6---------------------------------------------------------------------------------------*
from .models import Municipios

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

#7---------------------------------------------------------------------------------------*
from .models import Vendedores

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
        
#8---------------------------------------------------------------------------------------*
# admin.py
#from django.contrib import admin
#from django.contrib import messages
from .models import Numeradores

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
            'fields': (
                'numerador_aux_1',
                'numerador_aux_2',
                'numerador_aux_3',
                'numerador_aux_4',
                'numerador_aux_5'
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
        
        
#9---------------------------------------------------------------------------------------*
from .models import Clientes

@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = (
        'cliente_id', 'tipo_id', 'nombre', 'apellido',
        'email', 'telefono', 'estado',
    )
    search_fields = ('cliente_id', 'nombre', 'apellido', 'email', 'direccion')
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

#10---------------------------------------------------------------------------------------*
#DESEMBOLSOS Y COMENTARIOS_PRESTAMOS
#-----------------------------------------------------------------------------------------*    
# appfinancia/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError

from .models import Desembolsos, Comentarios_Prestamos


# ===================================================================
# INLINE DE COMENTARIOS
# ===================================================================
class ComentarioInline(admin.TabularInline):
    model = Comentarios_Prestamos
    extra = 1
    readonly_fields = (
        #'numero_comentario',
        #'comentario_catalogo',
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
# ===================================================================
# ADMIN PRINCIPAL DE DESEMBOLSOS
# ===================================================================
@admin.register(Desembolsos)
class DesembolsosAdmin(admin.ModelAdmin):
    list_display = (
        'prestamo_id',
        'cliente_id_display',
        'valor_formatted',
        'estado_colored',
        'fecha_desembolso',
        'acciones_columna',
    )
    search_fields = ('=prestamo_id', '=cliente_id__cliente_id', 'cliente_id__nombre')
    ordering = ('-fecha_desembolso',)
    inlines = [ComentarioInline]
    #exclude = ()  2026-01-08
    list_filter = ('estado','tipo_tasa', 'tiene_oneroso')   
    # Campos siempre de solo lectura
    readonly_fields_base = (
        'prestamo_id', 
        'fecha_vencimiento', 'tasa_mes', 'tasa',
        'fecha_creacion', 
        #'valor_cuota_mensual', # El sistema lo calcula, el usuario solo lo mira 2026-01-12 de edicion temporalmente
        #'valor_cuota_1'        # El sistema lo mueve según la inicial    2026-01-12 de edicion temporalmente
    )
    
    list_per_page = 14

    # ------------------------------------------------------------------
    # Diseño del formulario
    # ------------------------------------------------------------------
    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('1. Parámetros de Financiación', {
            'description': 'Ingrese los valores base para calcular la cuota mensual.',
            'fields': (
                'tipo_tasa', 
                'tasa_mes',
                'tasa', 
                'plazo_en_meses', 
                'valor', 
                'valor_seguro_mes', 
                'valor_cuota_mensual' #  aquí para que se vea el resultado del cálculo
            )
        }),
        ('2. Definición de Recaudo Inicial', {
            'description': 'Determine cómo se cobrará la primera obligación.',
            'fields': (
                'ofrece_cuota_inicial', 
                'valor_cuota_inicial', 
                'valor_cuota_1', 
                'numero_transaccion_cuota_1'
            )
        }),
        ('Condiciones Adicionales', {
            'fields': (
                'dia_cobro', 
                'fecha_desembolso', 
                'fecha_vencimiento', 
                'tiene_oneroso', 
                'entidad_onerosa'
            )
        }),
        ('Estado y Auditoría', {
            'fields': ('estado', 'fecha_creacion'),
            'classes': ('collapse',), # Opcional: esconder por defecto
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
# 1. Definimos las acciones disponibles
    actions = ['regresar_a_elaboracion', 'anular']

    # 2. Acción para usuarios de nivel superior
    @admin.action(description="🔄 Regresar a ELABORACION (Para corregir)", permissions=['change'])
    def regresar_a_elaboracion(self, request, queryset):
        # Solo permitimos actuar sobre registros que no han sido desembolsados aún
        queryset_validos = queryset.filter(estado='A_DESEMBOLSAR')
        total = queryset_validos.count()
        
        if total > 0:
            queryset_validos.update(estado='ELABORACION')
            self.message_user(
                request, 
                f"✅ {total} registro(s) regresaron a ELABORACION. Los campos ahora son editables.",
                level='success'
            )
        else:
            self.message_user(
                request, 
                "⚠️ No se realizaron cambios. Solo se pueden regresar registros en estado 'A DESEMBOLSAR'.", 
                level='warning'
            )

    # 3. Restricción de visibilidad de la acción
    def get_actions(self, request):
        actions = super().get_actions(request)
        # Solo superusuarios o miembros del grupo 'Supervisores' pueden ver esta acción
        es_supervisor = (
            request.user.is_superuser or 
            request.user.groups.filter(name='Administradores del Sistema').exists()
        )

        if not es_supervisor:
            if 'regresar_a_elaboracion' in actions:
                del actions['regresar_a_elaboracion']
        return actions
    

    #2025-11-25 6:52am traslado funcion pasar_a_desembolsado a utils.py


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
       
    # Luego verificamos si el clean() de models dejó activada la bandera 
        if getattr(obj, '_mostrar_warning_oneroso', False):
            from django.contrib import messages
            messages.warning(
                request, 
                "⚠️ AVISO: El campo 'Entidad Onerosa' fue borrado automáticamente porque seleccionó que NO tiene oneroso."
            )


    #bloque de código para inyectar el java script, debe ir dentro una clase. 2025/11/25 pam  
    #class Media:
    #    js = [
    #        'appfinancia/js/session-expiry.js',
    #        'appfinancia/js/number-format.js',
    #        'appfinancia/js/close-tab-logout.js',
    #    ]            
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/confirmar-desembolso/',
                self.admin_site.admin_view(self.confirmar_desembolso_view),
                name='appfinancia_desembolsos_confirmar',
            ),
            path(
                    '<path:object_id>/revertir-desembolso/',
                    self.admin_site.admin_view(self.revertir_desembolso_confirm_view),
                    name='revertir_desembolso_confirm',
                ),
        ]
        return custom_urls + urls

    def confirmar_desembolso_view(self, request, object_id):
        """Wrapper que conecta el Admin con la lógica en views.py"""
        from .views import ejecutar_desembolso_view
        return ejecutar_desembolso_view(request, object_id)
    
    def revertir_desembolso_confirm_view(self, request, object_id):
        """
        Encapsulo la vista de confirmación dentro del Admin para 
        no depender de archivos views.py externos 
        """
        from .forms import ReversionDesembolsoMotivoForm
        from django.template.response import TemplateResponse
        from .utils import revertir_desembolso
        from .models import Desembolsos

        obj = self.get_object(request, object_id)
        
        # Validación de permiso explícita
        if not request.user.has_perm('appfinancia.can_revert_desembolso'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        if request.method == 'POST':
            form = ReversionDesembolsoMotivoForm(request.POST)
            if form.is_valid():
                motivo = form.cleaned_data['motivo']
                try:
                    revertir_desembolso(object_id, request.user.username, motivo)
                    self.message_user(request, f"✅ Reversión exitosa del desembolso {object_id}.", level='SUCCESS')
                    return redirect("admin:appfinancia_desembolsos_changelist")
                except Exception as e:
                    self.message_user(request, f"❌ Error: {str(e)}", level='ERROR')
        else:
            form = ReversionDesembolsoMotivoForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'obj': obj,
            'form': form,
            'title': f"Confirmar Reversión: {obj.prestamo_id}",
        }
        # Asegúrate de que el template esté en: templates/admin/appfinancia/revertir_desembolso.html
        return TemplateResponse(request, "appfinancia/revertir_desembolso.html", context) # type: ignore
    
    def acciones_columna(self, obj):
        if obj.estado == 'A_DESEMBOLSAR':
            # CASO 1: El registro está listo para desembolsar 
            url_des = reverse('admin:appfinancia_desembolsos_confirmar', args=[obj.pk])
            return format_html(
                        '<a href="{}" onclick="return confirm(\'¿Confirmar desembolso para {}?\')">'
                        '🚀 Desembolsar</a>',
                        url_des, obj.prestamo_id
            )
        
        # CASO 2: El registro ya fue desembolsado y se permite la REVERSIÓN si no hay más pagos
        if obj.estado == 'DESEMBOLSADO':
            if self.request.user.has_perm('appfinancia.can_revert_desembolso'):
                from .models import Historia_Prestamos
                
                # CORRECCIÓN AQUÍ: 
                # Filtramos Historia_Prestamos usando directamente el ID numérico (obj.pk)
                # que es el mismo prestamo_id.
                pagos_posteriores = Historia_Prestamos.objects.filter(
                    prestamo_id=obj.pk, # Filtro directo por ID numérico
                    estado='PAGADA'
                ).exclude(numero_cuota__in=[0, 1]).exists()

                if not pagos_posteriores:
                    url_revertir = reverse('admin:revertir_desembolso_confirm', args=[obj.pk])
                    return format_html(
                        '<a href="{}" style="color: #ba2121; font-weight: bold; text-decoration: none;">'
                        '🔄 Revertir</a>', 
                        url_revertir
                    )
                else:
                    return format_html('<span style="color: #999;" title="Tiene pagos posteriores">🔒 Bloqueado</span>')

        return "—"

    acciones_columna.short_description = "Acción"

    # Inyectar el request en el admin para usarlo en acciones_columna
    def get_list_display(self, request):
        self.request = request
        return super().get_list_display(request)

#Fin Clase de Desembolso-----------------------------------------------------------------*

#11--------------------------------------------------------------------------------------* 
from .models import Conceptos_Transacciones

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
#12--------------------------------------------------------------------------------------*

# admin.py
#from django.contrib import admin
#from django.contrib import messages
from .models import Comentarios

@admin.register(Comentarios)
class ComentariosAdmin(admin.ModelAdmin):
    list_display = (
        #'comentario_id',
        'operacion_id', 'evento_id',
        'comentario', 'estado'
    )
    search_fields = ('operacion_id', 'evento_id', 'comentario')
    list_filter = ('estado',)
    ordering = ('operacion_id', 'evento_id')
    #readonly_fields = ('comentario_id',)

    fieldsets = (
        ('Identificación', {
            #'fields': ('comentario_id', 'operacion_id', 'evento_id'),
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

#13--------------------------------------------------------------------------------------*
# appfinancia/admin.py

#from django.contrib import admin
#from django.utils.html import format_html
#from .models import Comentarios_Prestamos

"""
@admin.register(Comentarios_Prestamos)
class ComentariosPrestamosAdmin(admin.ModelAdmin):
    list_display = (
        'numero_comentario',
        'prestamo_link',
        'comentario_catalogo_link',
        'operacion_id',
        'evento_id',
        'comentario_corto',
        'creado_por',
        'fecha_comentario'
    )
    list_display_links = ('numero_comentario',)
    search_fields = (
        'prestamo__prestamo_id',
        'comentario_catalogo__operacion_id',
        'comentario_catalogo__evento_id',
        'comentario'
    )
    list_filter = (
        'fecha_comentario',
        'comentario_catalogo__estado',
        'creado_por'
    )
    ordering = ('-fecha_comentario',)

    # Formulario de creación
    fieldsets = (
        ('Préstamo y Comentario', {
            'fields': ('prestamo', 'comentario_catalogo', 'comentario'),
            'description': "⚠️ El campo 'comentario' es opcional (texto personalizado)."
        }),
    )

    # Métodos personalizados para la lista
    def prestamo_link(self, obj):
        url = f"/admin/appfinancia/desembolsos/{obj.prestamo_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.prestamo_id)
    prestamo_link.short_description = 'Préstamo ID'

    def comentario_catalogo_link(self, obj):
        url = f"/admin/appfinancia/comentarios/{obj.comentario_catalogo_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.comentario_catalogo)
    comentario_catalogo_link.short_description = 'Comentario'

    def operacion_id(self, obj):
        return obj.operacion_id
    operacion_id.short_description = 'Operación'

    def evento_id(self, obj):
        return obj.evento_id
    evento_id.short_description = 'Evento'

    def comentario_corto(self, obj):
        return (obj.comentario[:50] + '...') if len(obj.comentario) > 50 else obj.comentario
    comentario_corto.short_description = 'Comentario'

    # 🔒 Permisos: solo crear y ver, no editar ni eliminar
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return True

    # ✅ Asignar automáticamente creado_por
    def save_model(self, request, obj, form, change):
        if not change:  # Solo al crear
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
        
"""
        
#14--------------------------------------------------------------------------------------*
from .models import Politicas

# appfinancia/admin.py
#from django.contrib import admin
from django import forms
#from .models import Politicas

# Formulario con formato colombiano (1.234.567,89)
class PoliticasForm(forms.ModelForm):
    class Meta:
        model = Politicas
        fields = '__all__'
        widgets = {
            'valor_cred_min': forms.TextInput(attrs={'placeholder': '1.000.000,00'}),
            'valor_cred_max': forms.TextInput(attrs={'placeholder': '50.000.000,00'}),
        }

    def clean_valor_cred_min(self):
        value = self.cleaned_data['valor_cred_min']
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        return value

    def clean_valor_cred_max(self):
        value = self.cleaned_data['valor_cred_max']
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        return value


@admin.register(Politicas)
class PoliticasAdmin(admin.ModelAdmin):
    form = PoliticasForm
    list_display = ('edad_min', 'edad_max',
                    'valor_cred_min', 'valor_cred_max',
                    'porcentaje_min_cuota_ini', 'porcentaje_max_cuota_ini',
                    'tasa_min', 'tasa_max',
                    'plazo_min', 'plazo_max',
                    'dias_max_desembolso_atras')        
        
    readonly_fields = ('id',)

    fieldsets = (
        (
            'Edad del Cliente', {
            'fields': ('edad_min', 'edad_max'),
            'description': '<small class="text-muted">Rango de edad permitido para solicitar crédito</small>'
        }),
        ('Valor del Crédito', {
            'fields': ('valor_cred_min', 'valor_cred_max'),
            'description': '<small class="text-muted">Use punto como decimal y coma como separador de miles</small>'
        }),
        ('Cuota Inicial (%)', {
            'fields': ('porcentaje_min_cuota_ini', 'porcentaje_max_cuota_ini')
        }),
        ('Tasas de Interés Mensual (%)', {
            'fields': ('tasa_min', 'tasa_max')
        }),
        ('Plazo del Crédito', {
            'fields': ('plazo_min', 'plazo_max')
        }),
        ('Dias permitidos con fechas atras para desembolsos', {
            'fields': ('dias_max_desembolso_atras',)
        }),
    )

    # Solo permite 1 registro
    def has_add_permission(self, request):
        return not Politicas.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Nunca se puede borrar

    def changelist_view(self, request, extra_context=None):
        if not Politicas.objects.exists():
            Politicas.load().save()
        return super().changelist_view(request, extra_context)


#15--------------------------------------------------------------------------------------*
# appfinancia/admin.py

from django.contrib import admin
from django.contrib import admin
from datetime import date
from .models import Prestamos, Fechas_Sistema

class ConAtrasoFilter(admin.SimpleListFilter):    #esta clase debe ir antes de PrestamosAdmin
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

#16--------------------------------------------------------------------------------------* 
#   2025-11-15 Incluyo metodos para consultar cuotas pagadas, proyectadas, saldo pendiente
# appfinancia/admin.py

from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from datetime import date
from decimal import Decimal

from .models import (
    Prestamos,
    Historia_Prestamos,
    Fechas_Sistema,
)

#---- filtro por rangos dias de  atraso
import datetime
from django.contrib import admin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

class DiasAtrasoFilter(admin.SimpleListFilter):
    title = _('Rango de Atraso')
    parameter_name = 'rango_mora'

    def lookups(self, request, model_admin):
        return (
            ('0_5', _('0 a 5 días')),
            ('6_30', _('6 a 30 días')),
            ('31_90', _('31 a 90 días')),
            ('mas_90', _('Más de 90 días')),
        )

    def queryset(self, request, queryset):
        from .models import Fechas_Sistema
        
        # Obtenemos la fecha actual del negocio
        fs = Fechas_Sistema.objects.first()
        if not fs or not self.value():
            return queryset
        
        fecha_corte = fs.fecha_proceso_actual
        
        # Definimos los deltas de tiempo
        hace_5_dias = fecha_corte - datetime.timedelta(days=5)
        hace_6_dias = fecha_corte - datetime.timedelta(days=6)
        hace_30_dias = fecha_corte - datetime.timedelta(days=30)
        hace_31_dias = fecha_corte - datetime.timedelta(days=31)
        hace_90_dias = fecha_corte - datetime.timedelta(days=90)

        # Filtro base: Solo cuotas PENDIENTES
        base_filter = Q(historia_prestamos__estado='PENDIENTE')

        if self.value() == '0_5':
            # Vencidas entre hoy y hace 5 días
            return queryset.filter(
                base_filter,
                historia_prestamos__fecha_vencimiento__lte=fecha_corte,
                historia_prestamos__fecha_vencimiento__gte=hace_5_dias
            ).distinct()

        if self.value() == '6_30':
            # Vencidas entre hace 6 y hace 30 días
            return queryset.filter(
                base_filter,
                historia_prestamos__fecha_vencimiento__lte=hace_6_dias,
                historia_prestamos__fecha_vencimiento__gte=hace_30_dias
            ).distinct()

        if self.value() == '31_90':
            # Vencidas entre hace 31 y hace 90 días
            return queryset.filter(
                base_filter,
                historia_prestamos__fecha_vencimiento__lte=hace_31_dias,
                historia_prestamos__fecha_vencimiento__gte=hace_90_dias
            ).distinct()

        if self.value() == 'mas_90':
            # Vencidas hace más de 90 días
            return queryset.filter(
                base_filter,
                historia_prestamos__fecha_vencimiento__lt=hace_90_dias
            ).distinct()

        return queryset
        

#_________________________________________________________________
@admin.register(Prestamos)
class PrestamosAdmin(admin.ModelAdmin):
    list_display = [
        'prestamo_id',
        'monto_atrasado_formateado',  
        'cuotas_atrasadas_display',
        'dias_atraso_display',
        'tiene_oneroso',
        'total_pendiente_real_formateado',
        'ver_estado_cuenta_link',
        'ver_plan_pagos_link',
    ]
    
    search_fields = [
            'prestamo_id__prestamo_id', # Entra a Desembolsos y busca por ID numérico
            'cliente_id__cliente_id',   # Busca por el número de identificación (BigIntegerField)
            'cliente_id__nombre',       # Busca por nombre del cliente
            'cliente_id__apellido',     # Busca por apellido del cliente
        ]
    
    list_filter = (DiasAtrasoFilter, 'tipo_tasa', 'tiene_oneroso')   
    ordering = ('prestamo_id',)
    list_per_page = 14

    readonly_fields = (
        'prestamo_id',
        'fecha_vencimiento', 'tasa_mes', 'tasa', #2026-01-09
        'fecha_desembolso',
        'enlace_reporte',
         'saldo_pendiente_formateado',  # Opcional: si quieres verlo en detalle
        'resumen_pagos',
    )

    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            'fields': (
                'tipo_tasa', 'tasa_mes', 'tasa',
                'valor', 'valor_cuota_1',
                'valor_cuota_mensual', 'valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento', 'tiene_oneroso', 'entidad_onerosa')
        }),
    )

    #nuevos formateos --- 2025-12-21 mags.-
    def _format_currency(self, value):
        """Helper para formatear moneda consistentemente."""
        try:
            val = float(value) if value is not None else 0.0
            return f"${val:,.2f}"
        except (TypeError, ValueError):
            return "Error"

    def _colored_span(self, value, positive_color="red", zero_color="green"):
        """Helper para colorear valores."""
        try:
            val = float(value)
            color = positive_color if val > 0 else zero_color
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, self._format_currency(value))
        except:
            return format_html('<span style="color: gray;">Error</span>')

    # --- Nuevos displays --- 2025-12-21 mags.-
    def saldo_capital_formateado(self, obj):
        return self._colored_span(obj.saldo_capital_pendiente())
    saldo_capital_formateado.short_description = "Saldo Capital"

    def intereses_vencidos_formateado(self, obj):
        return self._colored_span(obj.intereses_vencidos_no_pagados())
    intereses_vencidos_formateado.short_description = "Int. Vencidos"

    def seguros_vencidos_formateado(self, obj):
        return self._colored_span(obj.seguros_vencidos_no_pagados())
    seguros_vencidos_formateado.short_description = "Seg. Vencidos"

    def total_pendiente_real_formateado(self, obj):
        return self._colored_span(obj.total_pendiente_real(), positive_color="darkred")
    total_pendiente_real_formateado.short_description = "Total Adeudado"

    def monto_atrasado_formateado(self, obj):
        return self._colored_span(obj.monto_atrasado())
    monto_atrasado_formateado.short_description = "Monto Atrasado"




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
            path(
                'estado-cuenta/<int:prestamo_id>/',
                self.admin_site.admin_view(self.estado_cuenta_view),
                name='appfinancia_prestamos_estado_cuenta',
            ),
            path(
                'estado-cuenta/<int:prestamo_id>/excel/',
                self.admin_site.admin_view(self.generar_excel_estado_cuenta_view),
                name='appfinancia_prestamos_estado_cuenta_excel',
            ),
        ]
        return custom_urls + urls
    
    
    # ✅ En admin.py: solo wrappers ligeros 
    def estado_cuenta_view(self, request, prestamo_id):
        from .views import estado_cuenta
        return estado_cuenta(request, prestamo_id)

    def generar_excel_estado_cuenta_view(self, request, prestamo_id):
        from .views import generar_excel_estado_cuenta_view
        return generar_excel_estado_cuenta_view(request, prestamo_id)                                                              

    def generar_reporte_detalle(self, request, prestamo_id):
        from utils import generar_reporte_excel_en_memoria
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
            from .utils import generar_reporte_excel_en_memoria
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
    #-------------------- para el estado de cuenta: ----
    def ver_estado_cuenta_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        # Asegurarse de que obj.prestamo_id y su ID numérico existen
        if obj.prestamo_id and hasattr(obj.prestamo_id, 'prestamo_id') and obj.prestamo_id.prestamo_id:
            try:
                prestamo_id_num = obj.prestamo_id.prestamo_id  # ← este es el entero
                url = reverse('admin:appfinancia_prestamos_estado_cuenta', args=[prestamo_id_num])
                return format_html('<a href="{}" target="_blank">Ver Estado de Cuenta</a>', url)
            except Exception as e:
                # Opcional: imprime el error en los logs para depuración
                # print(f"Error generando URL para préstamo {prestamo_id_num}: {e}")
                return format_html('<span style="color: red;">Error en URL</span>')
        else:
            return format_html('<span style="color: gray;">N/A</span>')

    ver_estado_cuenta_link.short_description = 'Estado de Cuenta'
#17--------------------------------------------------------------------------------------*
from django.contrib import admin
from .models import Historia_Prestamos

# appfinancia/admin.py

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
    #search_fields = ('prestamo_id','numero_cuota')
    search_fields = ('prestamo_id__prestamo_id__exact','numero_cuota')
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
#18--------------------------------------------------------------------------------------*

#2025-11-15 Elimino Plan_Pagos


#18---------------------------------------------------------------------------------------------*

from .models import Bitacora
@admin.register(Bitacora)

class BitacoraAdmin(admin.ModelAdmin):
    # Solo permite ver, no crea, edita ni elimina
    list_display = ('secuencial', 'fecha_hora', 'fecha_proceso', 'user_name', 'evento_realizado', 'proceso', 'resultado')
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


#=========================================================================================        
# === CONTROL DE ARCHIVOS DE PAGOS === 2025/11/24       
#=========================================================================================

from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import Pagos


#admin.site.register(Pagos_Archivos, Pagos_Archivos_Admin)
# admin.site.register(Pagos)  2025-12-14 comento esta linea porque no deja subir el server.-mags

        
#23---------------------------------------------------------------------------------------
#=====CONTROL DE FECHAS DEL SISTEMA
#-----------------------------------------------------------------------------------------
# appfinancia/admin.py
#from django.contrib import admin
#from django import forms
# appfinancia/admin.py

#from django.contrib import admin
#from django import forms
#from django.utils.html import format_html

# aqui esta lo ddel banner de  las fechas   <<<-------
#Fin fechas del sistema

#-----------------------------------------------------------------------------------------
#                       InBox
#-----------------------------------------------------------------------------------------

from django.contrib import admin, messages
from django import forms
from django.db import transaction, IntegrityError
from .models import InBox_PagosCabezal, InBox_PagosDetalle
from .utils import f_procesar_archivo, f_anular_archivo,InBox_Pagos
#from .importacion_archivos import InBox_Pagos

#import os
#from django.contrib import admin, messages
#from django import forms

#from .models import InBox_PagosCabezal
#from .utils import f_procesar_archivo, f_anular_archivo


# ================================================================
# FORMULARIO PERSONALIZADO PARA CABEZAL
# ================================================================
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


# ================================================================
# ADMIN PERSONALIZADO
# ================================================================
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
        'nombre_archivo_id',
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
        }),
        ("Resultados", {
            "classes": ("collapse",),   # SECCIÓN OCULTA
            "fields": (
                "valor_total",
                "registros_cargados",
                "registros_rechazados",
                "estado_proceso_archivo",
            ),
        }),
        ("Auditoría", {
            "classes": ("collapse",),   # SECCIÓN OCULTA
            "fields": ("fecha_carga_archivo", "creado_por"),
        }),
    )

    # -------------------------------------------------------------
    # ACCIONES PERSONALIZADAS
    # -------------------------------------------------------------
    actions = ["accion_procesar_archivo", "accion_anular_archivo"]

    #-----------------------------------------------------
    def col_fecha(self, obj):
        if obj.fecha_carga_archivo:
            return obj.fecha_carga_archivo.strftime('%Y-%m-%d %H:%M:%S')
        return "N/A" # Manejar el caso donde la fecha es nula
        
    def col_cargados(self, obj):
        return obj.registros_cargados
    col_cargados.short_description = "Cargados"
    
    def col_rechazados(self, obj):
        return obj.registros_rechazados
    col_rechazados.short_description = "Rechazados"
    
    def col_estado_archivo(self, obj):
        return obj.estado_proceso_archivo
    col_estado_archivo.short_description = "Estado"
    
    #-----------------------------------------------------

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



# ================================================================
# ADMIN PARA DETALLE
# ================================================================

from django.urls import reverse
from django.utils.html import format_html

# admin.py (fragmento a pegar en la clase InBox_PagosDetalleAdmin)
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from .services.conciliacion import conciliacion_por_movimiento

@admin.register(InBox_PagosDetalle)
class InBox_PagosDetalleAdmin(admin.ModelAdmin):
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
        'regularizar_pago_action',   # ← NUEVO
        'fragmentar_pago_action',
    )
    list_filter = ('estado_pago','estado_conciliacion','estado_fragmentacion','clase_movimiento','cliente_id_real')
    search_fields = ('=cliente_id_real', '=pago_id', 'lote_pse')
    ordering = ('-pago_id',)
    
    readonly_fields = (
        "pago_id",
        "fecha_carga_archivo",
        "creado_por",
    )
    fieldsets = (
        ("ARCHIVO DE ORIGEN", {
            "fields": ("nombre_archivo_id", "fecha_carga_archivo"),
        }),

        ("IDENTIFICADORES Y GRUPOS", {
            "fields": ("lote_pse", "fragmento_de"),
        }),

        ("DATOS BANCARIOS", {
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

        ("INFORMACIÓN REPORTADA POR EL BANCO", {
            "fields": (
                "estado_transaccion_reportado",
                "clase_movimiento",
                "estado_fragmentacion",
                "cliente_id_reportado",
                "prestamo_id_reportado",
                "poliza_id_reportado",
            ),
        }),

        ("DATOS DE CONCILIACIÓN", {
            "fields": (
                "cliente_id_real",
                "prestamo_id_real",
                "poliza_id_real",
                "fecha_conciliacion",
                "estado_conciliacion",
            ),
        }),

        ("PAGO Y ESTADO", {
            "fields": ("fecha_pago", "valor_pago", "estado_pago"),
        }),

        ("AUDITORÍA", {
            "fields": ("creado_por", "observaciones"),
        }),
    )
    
    actions = ["action_conciliar_movimientos_seleccionados"]
    
    def col_estado_pago(self, obj):
        return obj.estado_pago
    col_estado_pago.short_description = "Estado"
    
    def col_clase_movimiento(self, obj):
        return obj.clase_movimiento
    col_clase_movimiento.short_description = "Clase Pago"
    
    def col_fecha_pago(self, obj):
        if obj.fecha_pago:
            return obj.fecha_pago.strftime('%Y-%b-%d')
        return "N/A"
    col_fecha_pago.short_description = "Fecha Pago"    
    
    def col_pago_id(self, obj):
        return obj.pago_id
    col_pago_id.short_description = "PagoId"
    
    def col_fragmento(self, obj):
        return obj.fragmento_de
    col_fragmento.short_description = "Frag"
    
    def col_fragmentacion(self, obj):
        return obj.estado_fragmentacion
    col_fragmentacion.short_description = "Fragmentacion"

    def col_cliente(self, obj):
        return obj.cliente_id_real
    col_cliente.short_description = "Cliente"

    def col_prestamo(self, obj):
        return obj.prestamo_id_real
    col_prestamo.short_description = "Prestamo"
    
    def col_conciliacion(self, obj):
        return obj.estado_conciliacion
    col_conciliacion.short_description = "Conci"
    
    #boton de fragmentación---------------------------------------------------
    def fragmentar_pago_action(self, obj):
        url = reverse("appfinancia:fragmentar_pago", args=[obj.pago_id])
        return format_html('<a class="button" href="{}">Frag</a>', url)
    fragmentar_pago_action.short_description = "Frag"
    #-------------------------------------------------------------------------

    def regularizar_pago_action(self, obj):
        url = reverse("appfinancia:regularizar_pago", args=[obj.pago_id])
        return format_html('<a class="button" href="{}">Regu</a>', url)
    regularizar_pago_action.short_description = "Regu"

    #-------------------------------------------------------------------------

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
        
   #Acción conciliación-------------------------------------------------------------------     
    def action_conciliar_movimientos_seleccionados(self, request, queryset):
        """
        Action para conciliar los movimientos seleccionados (que deben ser ABONO_PSE).
        """
        movimientos = queryset.filter(clase_movimiento="ABONO_PSE", estado_pago="A_PROCESAR")
        total_mov = movimientos.count()
        conciliados = 0
        asignados_total = 0
        no_conciliar = []

        for mov in movimientos:
            # candidatos: pagos directos PSE sin grupo asignado y A_PROCESAR
            candidatos_qs = InBox_PagosDetalle.objects.filter(
                #clase_movimiento="PAGO_PSE_PSE",
                clase_movimiento="PAGO_PSE",
                estado_pago="A_PROCESAR",
                estado_conciliacion="NO",                
                lote_pse__isnull=True,  # no asignados aún
            )
            ok, msg, detalles = conciliacion_por_movimiento(mov, candidatos_qs)
            if ok:
                conciliados += 1
                asignados_total += detalles.get("hijos_creados", 0)
            else:
                no_conciliar.append((mov.pago_id, msg))

        if conciliados:
            self.message_user(
                request,
                _(f"{conciliados} de {total_mov} movimientos conciliados correctamente. Pagos asignados: {asignados_total}"),
                level=messages.SUCCESS
            )

        if no_conciliar:
            # mostrar algunos detalles
            lines = "; ".join([f"{mid}: {msg}" for mid, msg in no_conciliar[:10]])
            self.message_user(
                request,
                _(f"{len(no_conciliar)} movimientos no conciliados. Ejemplos: {lines}"),
                level=messages.WARNING
            )

    action_conciliar_movimientos_seleccionados.short_description = "Conciliar movimientos seleccionados (PSE grupos)"



#=========================================================================================        
# === CONTROL DE ARCHIVOS DE PAGOS === 2025/11/24       
#=========================================================================================
# appfinancia/admin.py
#from django.contrib import admin
#from django.utils.html import format_html

#=========================================================================================        
# === DETALLE DE LOS PAGOS ===  2025/11/24           
#=========================================================================================    
        
# appfinancia/admin.py
#from django.contrib import admin
from .models import Pagos
from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import reverse
from .views import ver_comprobante_pago 

@admin.register(Pagos)
class PagosAdmin(admin.ModelAdmin):
    list_display = (
        'pago_id',
        'prestamo_id_real',
        'cliente_id_real',
        'valor_pago_formatted',
        'estado_pago_colored',
        'fecha_pago',
        'fecha_aplicacion_pago',  #2025-12-30
        'previsualizar_link',  #2025-12-16
        'ver_comprobante_link', #2025-12-30
    )
    list_filter = (
        'estado_pago',
        'estado_conciliacion',
        'fecha_pago',
        'canal_red_pago',
        'banco_origen',
    )
    search_fields = (
        'pago_id',
        'nombre_archivo_id__nombre_archivo_id',
        'prestamo_id_reportado',
        'cliente_id_reportado',
        'ref_bancaria',
        'ref_red',
    )
    ordering = ('-fecha_pago', '-pago_id')
    readonly_fields = (
        'pago_id',
        'fecha_carga_archivo',
        'creado_por',
        #'fecha_aplicacion_pago', temporal para #2026-01-04
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
    list_per_page = 12
        
    #actions = ['aplicar_pagos_conciliados'] #se traslado esta accion a vista


    # Métodos personalizados
    def valor_pago_formatted(self, obj):
        return f"${obj.valor_pago:,.2f}"
    valor_pago_formatted.short_description = "Valor Pago"

    def estado_pago_colored(self, obj):
        from django.utils.html import format_html
        colores = {
            'Recibido': '#1f77b4',
            'pendiente': '#ff7f0e',
            'rechazado': '#d62728', 
            'CONCILIADO': '#2ca02c',
            'aplicado': '#9467bd',
            'reversado': '#8c564b',
            'acreedores': '#17becf',
        }
        color = colores.get(obj.estado_pago, '#7f7f7f')
        #return f'<span style="color:{color}; font-weight:bold;">{obj.get_estado_pago_display()}</span>'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_pago_display()
        )
    estado_pago_colored.short_description = "Estado"
    #estado_pago_colored.allow_tags = True
    estado_pago_colored.admin_order_field = 'estado_pago'

    # Guardar usuario actual
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)        

    def get_urls(self):
        urls = super().get_urls()
        from .views import (
            previsualizar_aplicacion_pago,
            confirmar_aplicacion_pago,
            ver_comprobante_pago,
            exportar_comprobante_pdf,
            exportar_comprobante_excel,
        )
        custom_urls = [
            path(
                'previsualizar/<int:pago_id>/',
                self.admin_site.admin_view(previsualizar_aplicacion_pago),
                name='appfinancia_pagos_previsualizar',
            ),
            path(
                'aplicar/<int:pago_id>/',
                self.admin_site.admin_view(confirmar_aplicacion_pago),
                name='appfinancia_pagos_aplicar',
            ),
            path(
                '<int:pago_id>/ver-comprobante/',
                self.admin_site.admin_view(ver_comprobante_pago),
                name='appfinancia_pagos_ver_comprobante',  # ← ¡Eliminado el ":" sobrante!
            ),
            path(
                '<int:pago_id>/exportar-pdf/',
                self.admin_site.admin_view(exportar_comprobante_pdf),
                name='appfinancia_pagos_exportar_pdf',
            ),
            path(
                '<int:pago_id>/exportar-excel/',
                self.admin_site.admin_view(exportar_comprobante_excel),
                name='appfinancia_pagos_exportar_excel',
            ),
            path('<path:object_id>/reversion-pago/',
                 self.admin_site.admin_view(self.reversion_pago_confirm_view),
                 name='reversion_pago_confirm'
            ),
        ]
        return custom_urls + urls 

    def previsualizar_link(self, obj):
        # 1. CASO: PAGO LISTO PARA APLICAR (CONCILIADO)
        if obj.estado_pago.upper() == 'CONCILIADO':
            url = reverse('admin:appfinancia_pagos_previsualizar', args=[obj.pk])
            return format_html(
                '<a href="{}" target="_blank" style="color: #28a745; font-weight: bold;">💸 Aplicar</a>', 
                url
            )

        # 2. CASO: PAGO YA APLICADO (PERMITIR REVERSIÓN)
        if obj.estado_pago.upper() == 'APLICADO':
            # Validación de Permisos
            if not self.request.user.has_perm('appfinancia.can_revert_pago'):
                return format_html('<span style="color: #999;">-</span>')

            # Validación Cronológica: Buscar pagos aplicados posteriores del mismo préstamo
            # Esto garantiza la integridad de la causación de intereses (CAUSAC)
            pago_post = Pagos.objects.filter(
                prestamo_id_real=obj.prestamo_id_real,
                fecha_pago__gt=obj.fecha_pago,
                estado_pago='APLICADO'
            ).exists()

            if pago_post:
                return format_html(
                    '<span style="color: #999;" title="Debe reversar primero los pagos más recientes">🔒 Bloqueado</span>'
                )
            
            # Si pasa las validaciones, mostramos el enlace de reversión
            url_rev = reverse('admin:reversion_pago_confirm', args=[obj.pk])
            return format_html(
                '<a href="{}" style="color: #ba2121; font-weight: bold;">🔄 Reversar</a>', 
                url_rev
            )
        
        # 3. OTROS ESTADOS (REVERSADO, RECIBIDO, etc.)
        return format_html('<span style="color: #666;">{}</span>', obj.estado_pago)

    previsualizar_link.short_description = "Acción"
    previsualizar_link.allow_tags = True

    def ver_comprobante_link(self, obj):
        # Opcional: verifica si existe el comprobante (asumiendo relación OneToOne o ForeignKey inversa)
        # Si tu modelo ComprobantePago tiene: pago = models.OneToOneField(Pagos, ...)
        # entonces puedes usar: hasattr(obj, 'comprobante')
        if hasattr(obj, 'comprobante'):
            url = reverse('admin:appfinancia_pagos_ver_comprobante', args=[obj.pk])  
            return format_html('<a href="{}" target="_blank">📄 Ver comprobante</a>', url)
        return "No generado"
    #    fin  pre-y aplicar pagos con boton --- 2025-12-16

    # Inyectar el request en el admin para usarlo en acciones_columna
    def get_list_display(self, request):
        self.request = request
        return super().get_list_display(request)


    #aplicar pagos conciliados se traslada a la vista previsualizar 2026-01-02

    def reversion_pago_confirm_view(self, request, object_id):
        from .forms import ReversionPagoMotivoForm
        from .utils import revertir_aplicacion_pago
        from django.template.response import TemplateResponse
        from django.shortcuts import redirect
        # REGLA: Restricción explícita de permisos en el Admin
        # 1. SEGURIDAD: Validar permiso antes que cualquier otra cosa
        if not request.user.has_perm('appfinancia.can_revert_pago'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("No tiene los privilegios necesarios para revertir pagos.")

        # 2. Obtener el objeto
        pago = self.get_object(request, object_id)

        # --- VALIDACIÓN DE SEGURIDAD EN PYTHON ---
        # Si alguien intenta entrar a la URL manualmente, Python lo bloquea aquí
        pago_post = Pagos.objects.filter(
            prestamo_id_real=pago.prestamo_id_real,
            fecha_pago__gt=pago.fecha_pago,
            estado_pago='APLICADO'
        ).exists()

        if pago_post:
            self.message_user(request, "ERROR: No se puede reversar. Existen pagos aplicados posteriores.", level='ERROR')
            return redirect("admin:appfinancia_pagos_changelist")



        if pago_post:
            self.message_user(request, "ERROR: No se puede reversar. Existen pagos aplicados posteriores.", level='ERROR')
            return redirect("admin:appfinancia_pagos_changelist")

        # --- MANEJO DEL FORMULARIO ---
        if request.method == 'POST':
            form = ReversionPagoMotivoForm(request.POST)
            if form.is_valid():
                try:
                    # Llamamos a la función de utils.py que ya incluye la lógica del asiento_contable
                    revertir_aplicacion_pago(object_id, request.user.username, form.cleaned_data['motivo'])
                    self.message_user(request, f"✅ Pago {object_id} reversado correctamente.", level='SUCCESS')
                    return redirect("admin:appfinancia_pagos_changelist")
                except Exception as e:
                    self.message_user(request, f"❌ Error en la reversión: {str(e)}", level='ERROR')
        else:
            form = ReversionPagoMotivoForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'pago': pago,
            'form': form,
            'title': f"Confirmar Reversión: Pago {pago.pago_id}",
        }
        return TemplateResponse(request, "appfinancia/revertir_aplicacion_pago.html", context)
        
#--------------------------------------------------------------------------------------------------------------------
# 
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, reverse
from .models import ConsultasReportesProxy
from .views import consulta_causacion_view, balance_operaciones_view, prestamos_vencidos_view, buscar_comprobante_view

@admin.register(ConsultasReportesProxy)
class ConsultasReportesAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super().get_urls()   
        custom_urls = [
            path('causacion/', self.admin_site.admin_view(consulta_causacion_view), name='appfinancia_consultasreportes_causacion'),
            path('balance-operaciones/', self.admin_site.admin_view(balance_operaciones_view), name='appfinancia_consultasreportes_balance'), 
            path('prestamos-vencidos/', self.admin_site.admin_view(prestamos_vencidos_view), name='appfinancia_consultasreportes_vencidos'),
            path('buscar-comprobante/', self.admin_site.admin_view(buscar_comprobante_view), name='appfinancia_consultasreportes_buscar_comprobante'),
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
            'buscar_comprobante_url': reverse('admin:appfinancia_consultasreportes_buscar_comprobante'),
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
#------------------------------------------------------------------------------------------
      
from django.contrib import admin
from .models import EntidadesFinancieras

@admin.register(EntidadesFinancieras)
class EntidadesFinancierasAdmin(admin.ModelAdmin):
    # Columnas que se verán en el listado principal
    list_display = ('nit_formateado', 'nombre_corto', 'nombre_completo',  'fecha_creacion')
    
    # Campos por los que puedes buscar (el NIT es BigInt, funciona perfecto)
    search_fields = ('nit', 'nombre_corto', 'nombre_completo', 'email')
    
    # Filtros laterales para limpieza de datos
    list_filter = ('estado',)
    
    # Hacer que el nombre corto sea un link para editar también
    list_display_links = ('nit_formateado', 'nombre_corto')
    
    # Organización de los campos dentro del formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': ('nit', 'nombre_corto', 'nombre_completo')
        }),
        ('Contacto', {
            'fields': ('nombre_contacto', 'email')
        }),
        ('Configuración del Sistema', {
            'fields': ('estado',),
            'description': 'Determine si la entidad está operativa para el proceso de seguros.'
        }),
    )

    # Opcional: Para que la fecha de creación se vea en el formulario (aunque sea auto_now_add)
    readonly_fields = ('fecha_creacion',)

    @admin.display(description='NIT', ordering='nit')
    def nit_formateado(self, obj):
        if not obj.nit:
            return "-"
        nit_str = str(obj.nit)
        # Separamos el último dígito (DV) del resto
        nit_parte = nit_str[:-1]
        dv = nit_str[-1]
        return f"{nit_parte}-{dv}"
    
    # Método para dar color al estado en el listado (opcional, visualmente ayuda mucho)
    @admin.display(description='Estado')
    def estado_status(self, obj):
        from django.utils.html import format_html
        color = 'green' if obj.estado == 'HABILITADO' else 'red'
        return format_html('<b style="color:{};">{}</b>', color, obj.estado)

#________________________________________________________________________________________