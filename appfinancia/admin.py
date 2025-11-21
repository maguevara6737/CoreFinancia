from django.contrib import admin, messages

# appfinancia/admin.py (fragmento)
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from .models import Desembolsos,  Bitacora
from . import utils  # importa las funciones definidas en utils.py
from .utils import create_prestamo  # importa las funciones definidas en utils.py
from .utils import create_movimiento  # importa las funciones definidas en services
from .utils import calculate_loan_schedule, create_loan_payments   

from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from .models import Desembolsos, Comentarios_Prestamos, Comentarios
from .forms import ComentarioPrestamoForm



 
from django.core.exceptions import ValidationError
 
#from .models import Menu

# Register your models here.

# inicio-para personalizar el Panel Administrador Django 20251031
from django.contrib.admin import AdminSite
# Personalización del título y encabezados
admin.site.site_header = "Sistema Financia Seguros - Panel de Administración"
admin.site.site_title = "Sistema Financia Admin"
admin.site.index_title = "Gestión del Sistema Financiero"
# fin-para personalizar el Panel Administrador Django

#Para los formatos de número
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.formats import number_format

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
    list_display = ('tipo_tasa', 'tasa')
    ordering = ('tipo_tasa',)

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
                'numerador_operacion',
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
        'departamento', 'municipio', 'fecha_creacion'
    )
    search_fields = ('cliente_id', 'nombre', 'apellido', 'email', 'direccion')
    list_filter = ('estado', 'departamento', 'municipio', 'tipo_id', 'fecha_creacion')
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
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
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
    )
    list_filter = ('estado',)
    search_fields = ('prestamo_id', 'cliente_id__cliente_id', 'cliente_id__nombres')
    ordering = ('-fecha_desembolso',)
    inlines = [ComentarioInline]
    exclude = ('valor_cuota_mensual',)

    # Campos siempre de solo lectura
    readonly_fields_base = ('prestamo_id', 'fecha_vencimiento', 'fecha_creacion')

    # ------------------------------------------------------------------
    # Diseño del formulario
    # ------------------------------------------------------------------
    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            'fields': (
                'tipo_tasa', 'tasa',
                'valor', 'valor_cuota_1', 'numero_transaccion_cuota_1',
                'valor_seguro_mes', 'tiene_fee'
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
    actions = ['pasar_a_desembolsado', 'anular']

    def pasar_a_desembolsado(self, request, queryset):
        updated = queryset.filter(estado='A_DESEMBOLSAR').update(estado='DESEMBOLSADO')
        self.message_user(request, f"{updated} desembolso(s) pasado(s) a DESEMBOLSADO.")
    pasar_a_desembolsado.short_description = "Pasar a DESEMBOLSADO"

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
            
    
#Fin Clase de Desembolso-----------------------------------------------------------------*


    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #====================================== inicio  desembolsos   ======================= 2025-11-15 
    from django.db import transaction
    from django.contrib import messages
    from django.utils import timezone
    from django.contrib.admin import action
 


    from .models import Desembolsos, Bitacora, Historia_Prestamos

    @action(description="Procesar desembolsos pendientes")
    def procesar_desembolsos_pendientes(modeladmin, request, queryset):
        """
        Action para el Django Admin: procesa todos los desembolsos en estado 'PENDIENTE'.
        Crea registros en Prestamos, Movimientos, Historia_Prestamos y calcula el plan de pagos.
        """
        desembolsos_marcados = list(queryset.filter(estado="PENDIENTE"))

        if not desembolsos_marcados:
            messages.warning(request, "No hay desembolsos pendientes para procesar.")
            return

        try:
            with transaction.atomic():
                for desembolso in desembolsos_marcados:
                    # 1. Crear Prestamo
                    prestamo = create_prestamo(desembolso)

                    # 2. Crear Movimiento
                    create_movimiento(desembolso)

                    # 3. Crear Historia_Prestamos inicial (registro de desembolso)
                    #create_historia_prestamo(prestamo, desembolso, user_name=request.user.username)

                    # 4. Calcular plan de pagos
                    plan_pagos = calculate_loan_schedule(desembolso)

                    # 5. Crear registros de cuotas en Historia_Prestamos
                    if plan_pagos:
                        created_count = create_loan_payments(
                            prestamo=prestamo,
                            desembolso=desembolso,
                            plan_pagos=plan_pagos,
                            user_name=request.user.username
                        )
                        print(f"✅ Creadas {created_count} cuotas para desembolso {desembolso.prestamo_id}")

                    # 6. Actualizar estado del desembolso
                    desembolso.estado = 'DESEMBOLSADO'
                    desembolso.save(update_fields=['estado'])

            messages.success(
                request,
                f"✅ Se procesaron exitosamente {len(desembolsos_marcados)} desembolsos con plan de pagos."
            )
            print(f"✅ Proceso completado exitosamente para {len(desembolsos_marcados)} desembolsos.")

        except Exception as e:
            # transaction.atomic() hace rollback automáticamente
            error_msg = f"❌ Error al procesar desembolsos: {str(e)}"
            messages.error(request, error_msg)
            print(error_msg)

            # Registrar en Bitácora
            if request.user.username:
                Bitacora.objects.create(
                    fecha_proceso=timezone.now().date(),
                    user_name=request.user.username,
                    evento_realizado='PROCESO_DESEMBOLSOS',
                    proceso='ERROR',
                    resultado=error_msg
                )
    
    #====================== fin desembolsos   =======================  2025-11-15 



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

#16--------------------------------------------------------------------------------------* 
#   2025-11-15 Incluyo metodos para consultar cuotas pagadas, proyectadas, saldo pendiente

from .models import   Prestamos                      

@admin.register(Prestamos)
class PrestamosAdmin(admin.ModelAdmin):
    list_display = (
        'prestamo_id', 'cliente_id', 
         'fecha_formateada', 'valor'
        
    )
    search_fields = (
        'prestamo_id', 'cliente__cliente_id', 'asesor__asesor_Id'
    )
    list_filter = (
                'fecha_desembolso', 'aseguradora_id'
    )
    ordering = ('-fecha_desembolso',)
    readonly_fields = (
        'prestamo_id', 'fecha_vencimiento', 'fecha_desembolso'
    )
    list_per_page = 14
    # 3. Método personalizado para mostrar la fecha en formato yyyy-mm-dd
    def fecha_formateada(self, obj):
        return obj.fecha_desembolso.strftime('%Y-%m-%d')
    fecha_formateada.short_description = 'Fecha Ini.'  # Nombre que aparece en el encabezado
    fecha_formateada.admin_order_field = 'fecha'  # Permite ordenar por este campo
    #--------------------------------
    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor', 'aseguradora', 'vendedor')
        }),
        ('Tasa y Valores', {
            'fields': (
                'tipo_tasa', 'tasa',
                'valor', 'valor_cuota_1', 'numero_transaccion_cuota_1',
                'valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento')
        }),

    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe
            #return self.readonly_fields + ('cliente', 'asesor', 'aseguradora', 'vendedor', 'tipo_tasa')
            return self.readonly_fields + ('prestamo_id', 'cliente', 'fecha_creacion')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

        def get_total_cuotas(self):
            #"""Número total de cuotas proyectadas."""
            return len(self.get_payment_schedule())

    def get_paid_cuotas(self):
        """Número de cuotas ya pagadas (abono_capital > 0 y fecha_vencimiento <= hoy)."""
        from .models import Historia_Prestamos, Conceptos_Transacciones
        try:
            concepto_cuota = Conceptos_Transacciones.objects.get(concepto_id="CUOTA")
        except Conceptos_Transacciones.DoesNotExist:
            return 0

        today = timezone.now().date()
        return Historia_Prestamos.objects.filter(
            prestamo_id=self,
            concepto_id=concepto_cuota,
            abono_capital__gt=0,
            fecha_vencimiento__lte=today
        ).count()

    def get_outstanding_balance(self):
        """Saldo pendiente: suma de cuotas no pagadas (capital + intereses + seguro)"""
        schedule = self.get_payment_schedule()
        return sum(
            cuota['total_cuota'] for cuota in schedule
            if cuota['estado'] in ['PROYECTADO', 'VENCE_HOY', 'MOROSO']
    )


#17--------------------------------------------------------------------------------------*
from django.contrib import admin
from django.utils.html import format_html
from .models import Historia_Prestamos

@admin.register(Historia_Prestamos)
class HistoriaPrestamosAdmin(admin.ModelAdmin):
    # Mostrar todos los campos en la lista
    list_display = (
        'detalle_breve',  # ✅ Nuevo campo formateado
        'prestamo_id',
        'fecha_efectiva',
        'fecha_proceso',
        'numero_operacion',
        'concepto_id',
        'fecha_vencimiento',
        'tasa',
        'monto_transaccion',
        'abono_capital',
        'intrs_ctes',
        'seguro',
        'fee',
        'estado',
    )
    readonly_fields = ('mostrar_campos',)
    # ... resto del código

    def mostrar_campos(self, obj):
        # Formatear fechas
        fecha_efectiva = obj.fecha_efectiva.strftime('%Y-%m-%d') if obj.fecha_efectiva else ''
        fecha_proceso = obj.fecha_proceso.strftime('%Y-%m-%d') if obj.fecha_proceso else ''
        fecha_vencimiento = obj.fecha_vencimiento.strftime('%Y-%m-%d') if obj.fecha_vencimiento else ''

        # Formatear números decimales
        tasa = f"{obj.tasa:,.4f}" if obj.tasa else '0.0000'
        monto_transaccion = f"{obj.monto_transaccion:,.2f}" if obj.monto_transaccion else '0.00'
        abono_capital = f"{obj.abono_capital:,.2f}" if obj.abono_capital else '0.00'
        intrs_ctes = f"{obj.intrs_ctes:,.2f}" if obj.intrs_ctes else '0.00'
        seguro = f"{obj.seguro:,.2f}" if obj.seguro else '0.00'
        fee = f"{obj.fee:,.2f}" if obj.fee else '0.00'

        return format_html(
            "<h3>Datos del Préstamo</h3>"
            "<div><strong>Préstamo ID:</strong> {}</div>"
            "<div><strong>Fecha Efectiva:</strong> {}</div>"
            "<div><strong>Fecha Proceso:</strong> {}</div>"
            "<div><strong>Número Operación:</strong> {}</div>"
            "<div><strong>Concepto ID:</strong> {}</div>"
            "<div><strong>Fecha Vencimiento:</strong> {}</div>"
            "<div><strong>Tasa:</strong> {}</div>"
            "<div><strong>Monto Transacción:</strong> {}</div>"
            "<div><strong>Abono Capital:</strong> {}</div>"
            "<div><strong>Intereses Ctes:</strong> {}</div>"
            "<div><strong>Seguro:</strong> {}</div>"
            "<div><strong>Fee:</strong> {}</div>"
            "<div><strong>Usuario:</strong> {}</div>"
            "<div><strong>Número Cuota:</strong> {}</div>"
            "<div><strong>Estado:</strong> {}</div>",
            obj.prestamo_id,
            fecha_efectiva,
            fecha_proceso,
            obj.numero_operacion,
            obj.concepto_id,
            fecha_vencimiento,
            tasa,
            monto_transaccion,
            abono_capital,
            intrs_ctes,
            seguro,
            fee,
            obj.usuario,
            obj.numero_cuota,
            obj.estado,
        )

    mostrar_campos.short_description = "Detalle del Préstamo"

    list_per_page = 14

    # Desactivar la creación de nuevos registros
    def has_add_permission(self, request):
        return False

    # Desactivar la eliminación
    def has_delete_permission(self, request, obj=None):
        return False
    # Opcional: mejorar el título del campo en la lista (ej. mostrar nombres en lugar de "Prestamos object")
    # Si los modelos relacionados (Prestamos, Conceptos_Transacciones) tienen __str__ bien definidos,
    # ya se mostrarán correctamente.

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

#-------------------------------------------------------------------------------


