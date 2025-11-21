from django.contrib import admin, messages

# appfinancia/admin.py (fragmento)
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from .models import Desembolsos,  Bitacora
from . import utils  # importa las funciones definidas en utils.py
from .utils import create_prestamo  # importa las funciones definidas en utils.py
from .utils import create_movimiento  # importa las funciones definidas en services
#from .utils import create_historia_prestamo  # importa las funciones definidas en services
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
#from .models import Desembolsos
# admin.py
#from django.contrib import admin
from .models import Desembolsos


class ComentarioInline(admin.TabularInline):
    model = Comentarios_Prestamos
    extra = 1
    fields = ['comentario_catalogo', 'fecha_comentario', 'creado_por']
    readonly_fields = ['fecha_comentario', 'creado_por']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "comentario_catalogo":
            kwargs["queryset"] = Comentarios.objects.filter(estado='HABILITADO')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

@admin.register(Desembolsos)
class DesembolsosAdmin(admin.ModelAdmin):
    list_display = (
        'prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id',
        'valor', 'fecha_formateada',
        'estado'
    )
    search_fields = (
        'prestamo_id', 'cliente_id', 'asesor_id'
    )
    list_filter = (
        'estado', 'tiene_fee', 'fecha_desembolso', 'aseguradora_id'
    )
    ordering = ('-fecha_desembolso',)
    readonly_fields = (
        'prestamo_id', 'fecha_vencimiento', 'fecha_creacion'  #,'estado'
    )
    #--------------------------------
    actions = ['procesar_desembolsos_pendientes']   #<-------
    #--------------------------------
    list_per_page = 14
    # 3. Método personalizado para mostrar la fecha en formato yyyy-mm-dd
    def fecha_formateada(self, obj):
        return obj.fecha_creacion.strftime('%Y-%m-%d')
    fecha_formateada.short_description = 'Fecha'  # Nombre que aparece en el encabezado
    fecha_formateada.admin_order_field = 'fecha'  # Permite ordenar por este campo
    #--------------------------------
    fieldsets = (
        ('Identificación', {
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            'fields': (
                'tipo_tasa', 'tasa',
                'valor', 'valor_cuota_1', 'numero_transaccion_cuota_1',
                'valor_cuota_mensual', 'valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_creacion')
        }),
    )
    
    #funcion para los comentarios 2025/11/17
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        # Pasar comentarios HABILITADOS al template
        extra_context['comentarios_habilitados'] = Comentarios.objects.filter(estado='HABILITADO')
        return super().change_view(request, object_id, form_url, extra_context)
   # Fin

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si ya existe
            #return self.readonly_fields + ('cliente', 'asesor', 'aseguradora', 'vendedor', 'tipo_tasa')
            return self.readonly_fields + ('prestamo_id', 'cliente_id', 'fecha_creacion')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    #2025-11-17  para comentarios 8:37pm +++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/agregar-comentario/',
                self.admin_site.admin_view(self.agregar_comentario_view),
                name='agregar-comentario-desembolso',
            ),
        ]
        return custom_urls + urls

    def agregar_comentario_view(self, request, object_id):
        desembolso = get_object_or_404(Desembolsos, pk=object_id)

        if request.method == 'POST':
            form = ComentarioPrestamoForm(request.POST)
            if form.is_valid():
                comentario = form.save(commit=False)
                comentario.prestamo = desembolso
                comentario.creado_por = request.user
                comentario.save()
                # Redirigir de vuelta al formulario de edición
                url = reverse('admin:appfinancia_desembolsos_change', args=[object_id])
                return HttpResponseRedirect(url)

        else:
            form = ComentarioPrestamoForm()

        context = {
            'desembolso': desembolso,
            'form': form,
            'title': 'Agregar Comentario',
        }
        return TemplateResponse(request, 'admin/appfinancia/desembolsos/agregar_comentario.html', context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        desembolso = self.get_object(request, object_id)
        if desembolso:
            form = ComentarioPrestamoForm()
            extra_context['comentario_form'] = form
            extra_context['desembolso'] = desembolso

        return super().change_view(request, object_id, form_url, extra_context)




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
                   # create_historia_prestamo(prestamo, desembolso, user_name=request.user.username)

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
from django.contrib import admin
from .models import   Prestamos     
from django.utils.html import format_html
from django.urls import reverse                 
from django.utils import timezone # Asegúrate de importar timezone si usas los métodos get_paid_cuotas o get_outstanding_balance

@admin.register(Prestamos)
class PrestamosAdmin(admin.ModelAdmin):
    list_display = ['prestamo_id', 'valor', 'fecha_desembolso','ver_plan_pagos_link',]
    search_fields = [
        'cliente_id__nombre',  # Si tienes un campo 'nombre' en Clientes
        'asesor_id__nombre',
        'prestamo_id__id',  # Si quieres buscar por el ID del desembolso
    ]
    list_filter = (
        'fecha_desembolso',
        'aseguradora_id'
    )
    ordering = ('-fecha_desembolso',)
    readonly_fields = (
        'prestamo_id',
        'fecha_vencimiento',
        'fecha_desembolso'
    )
    list_per_page = 14

    # 3. Este método debe estar DENTRO de la clase y al mismo nivel de indentación que otros métodos
    def fecha_formateada(self, obj):
        """
        Método para mostrar la fecha en formato yyyy-mm-dd en la lista de admin.
        """
        # Asegúrate de que 'fecha_desembolso' sea un campo válido en tu modelo Prestamos
        return obj.fecha_desembolso.strftime('%Y-%m-%d')

    # 4. Importante: Define el encabezado de la columna
    fecha_formateada.short_description = 'Fecha Ini.'
    # 5. Opcional: Permite ordenar por este valor (refiriéndose al campo real del modelo)
    fecha_formateada.admin_order_field = 'fecha_desembolso'

    # 6. Este otro método también debe estar DENTRO de la clase y correctamente indentado
        # --- MÉTODO CORREGIDO ---
    def ver_plan_pagos_link(self, obj):
        """
        Método para crear un enlace al plan de pagos personalizado.
        Accede al ID numérico del Desembolso relacionado.
        """
        # Obtiene el VALOR NUMÉRICO del ID del desembolso relacionado
        prestamo_id_valor = obj.prestamo_id_id # <-- CORREGIDO: Usar _id

        # Valida que el ID sea un entero positivo antes de usar reverse
        if prestamo_id_valor and isinstance(prestamo_id_valor, int) and prestamo_id_valor > 0:
            try:
                # Solo intenta hacer reverse si el ID es válido
                url = reverse('plan_pagos', kwargs={'prestamo_id': prestamo_id_valor})
                # target="_blank" abre el enlace en una nueva pestaña
                return format_html('<a href="{}" target="_blank">Ver Plan de Pagos</a>', url)
            except Exception as e:
                # Si reverse falla por cualquier otro motivo, devuelve un mensaje o enlace roto
                # print(f"Error en reverse para prestamo_id {prestamo_id_valor}: {e}") # Descomenta para debug si es necesario
                return format_html('<span style="color: red;">Error en URL</span>')
        else:
            # Si el ID no es válido (p. ej., es None o 0), muestra un mensaje indicándolo
            # print(f"prestamo_id_id no válido: {prestamo_id_valor}, tipo: {type(prestamo_id_valor)}") # Descomenta para debug si es necesario
            return format_html('<span style="color: gray;">N/A</span>')

    ver_plan_pagos_link.short_description = 'Plan de Pagos'
    # --- FIN DEL MÉTODO CORREGIDO ---


    fieldsets = (
        ('Identificación', {
            # CORREGIDO: Cambiado 'asesor' por 'asesor_id', 'aseguradora' por 'aseguradora_id', 'vendedor' por 'vendedor_id'
            'fields': ('prestamo_id', 'cliente_id', 'asesor_id', 'aseguradora_id', 'vendedor_id')
        }),
        ('Tasa y Valores', {
            # CORREGIDO: Removido 'numero_transaccion_cuota_1' porque no existe en el modelo Prestamos
            'fields': (
                'tipo_tasa', 'tasa',
                'valor', 'valor_cuota_1', # <-- Removido 'numero_transaccion_cuota_1'
                'valor_cuota_mensual', 'valor_seguro_mes', 'tiene_fee'
            )
        }),
        ('Condiciones', {
            'fields': ('dia_cobro', 'plazo_en_meses', 'fecha_desembolso', 'fecha_vencimiento')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si el objeto ya existe (está siendo editado)
            return self.readonly_fields + ('prestamo_id', 'cliente_id', 'fecha_creacion')
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    # NOTA: Otros métodos como get_total_cuotas, get_paid_cuotas, etc.
    # deben estar aquí, dentro de la clase y con la indentación correcta
    # si planeas usarlos en list_display o fieldsets.
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
from .models import Historia_Prestamos

class HistoriaPrestamosAdmin(admin.ModelAdmin):
    # Usamos los campos reales del modelo
    list_display = (
        'id',  # PK autogenerado por Django, o usa 'pk' si prefieres
        'detalle_breve',
        'fecha_efectiva',
        'fecha_proceso'
    )
    readonly_fields = (
        'detalle_breve', # Tu campo personalizado
        'id',            # PK autogenerado por Django
        'prestamo_id',   # Cambiado de 'prestamo' a 'prestamo_id'
        'numero_cuota',  # Campo existente
        'concepto_id',   # Cambiado de 'codigo_transaccion' a 'concepto_id'
        'fecha_vencimiento', # Campo existente
        'monto_transaccion', # Campo existente
        'fecha_efectiva',    # Campo existente
        'fecha_proceso',     # Campo existente
        'abono_capital',     # Campo existente
        'intrs_ctes',        # Campo existente
        'seguro',            # Campo existente
        'fee',               # Campo existente
        'usuario',           # Campo existente
        # 'comentario',     # Eliminado porque no existe en el modelo actual
    )
    list_per_page = 14
    # Opcional: Ocultar los campos individuales si solo se quiere mostrar el detalle_breve
    fieldsets = (
        (None, {
            'fields': ('detalle_breve',)  # Solo se muestra el detalle_breve
        }),
        # Si se quiere ocultar completamente otros campos, no los incluyas aquí
    )

    def has_add_permission(self, request):
        return False  # Evita que se agreguen registros desde el admin

    def has_change_permission(self, request, obj=None):
        return False  # Evita que se editen registros desde el admin

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

#-------------------------------------------------------------------------------


