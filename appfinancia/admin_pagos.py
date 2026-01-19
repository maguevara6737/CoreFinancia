from django.contrib import admin, messages
from django import forms
from django.db import transaction, IntegrityError
from .models import InBox_PagosCabezal 
from .utils import InBox_Pagos

#-----------------------------------------------------------------------------------------
#Formulario para
#DeDetalle de pagos
# admin.py
#from django.contrib import admin
from .models import InBox_PagosDetalle

class InBox_PagosDetalleAdmin(admin.ModelAdmin):

    # Campos que no se editan manualmente
    readonly_fields = (
        "pago_id", "fecha_carga_archivo","creado_por",
    )

    # Organización del formulario
    fieldsets = (

        ("ARCHIVO DE ORIGEN", {
            "fields": (
                "nombre_archivo_id",
                "fecha_carga_archivo",
            )
        }),

        ("IDENTIFICADORES Y GRUPOS", {
            "fields": (
                "grupo_pse_id",
                "fragmento_de",
            )
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
            )
        }),

        ("INFORMACIÓN REPORTADA POR EL BANCO", {
            "fields": (
                "estado_transaccion_reportado",
                "clase_movimiento",
                "estado_fragmentacion",
                "cliente_id_reportado",
                "prestamo_id_reportado",
                "poliza_id_reportado",
            )
        }),

        ("DATOS DE CONCILIACIÓN", {
            "fields": (
                "cliente_id_real",
                "prestamo_id_real",
                "poliza_id_real",
                "fecha_conciliacion",
                "estado_conciliacion",
            )
        }),

        ("PAGO Y ESTADO", {
            "fields": (
                "fecha_pago",
                "valor_pago",
                "estado_pago",
            )
        }),

        ("AUDITORÍA", {
            "fields": (
                "creado_por",
                "observaciones",
            )
        }),
    )

    # Guarda automáticamente el usuario creador
    def save_model(self, request, obj, form, change):
        if not obj.pk:               # si es nuevo registro
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


admin.site.register(InBox_PagosDetalle, InBox_PagosDetalleAdmin)


#=========================
#FRAGMENTACIÓN DE PAOS
#=========================

# admin_fragmentacion.py  (puedes pegar dentro de admin.py si prefieres)
from decimal import Decimal
from django import forms
from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import InBox_PagosDetalle, Prestamos, Clientes  # importa Prestamos que enviaste


# ---------------------------
# Formulario de Fragmentación
# ---------------------------
class FragmentacionForm(forms.Form):
    # 6 pares prestamo + valor
    for letter in ("A", "B", "C", "D", "E", "F"):
        locals()[f"prestamo_{letter}"] = forms.ModelChoiceField(
            queryset=Prestamos.objects.none(),
            required=False,
            label=f"Préstamo {letter}"
        )
        locals()[f"valor_{letter}"] = forms.DecimalField(
            max_digits=15, decimal_places=2, required=False, label=f"Valor {letter}"
        )
    del letter  # quitar variable temporal

    def __init__(self, *args, pago_padre=None, **kwargs):
        """
        pago_padre: instancia InBox_PagosDetalle (el padre).
        Configura los querysets de los selects de préstamos para que muestren
        solo los préstamos del mismo cliente y con saldo disponible.
        """
        super().__init__(*args, **kwargs)
        self.pago_padre = pago_padre

        if pago_padre:
            cliente = pago_padre.cliente_id_real
            if cliente:
                # queryset con prestamos del cliente
                qs = Prestamos.objects.filter(cliente_id=cliente)

                # opcional: filtrar por saldo > 0 (usamos get_outstanding_balance())
                # no podemos filtrar por ORM si el saldo está calculado en Python,
                # así que ajustamos elección por cada choice en el init.
                # construiremos una lista de pk elegibles
                prestamos_validos = []
                for p in qs:
                    try:
                        saldo = p.get_outstanding_balance()
                        if saldo and Decimal(saldo) > Decimal("0"):
                            prestamos_validos.append(p.pk)
                    except Exception:
                        # si falla el cálculo, conservamos el préstamo (opcional)
                        prestamos_validos.append(p.pk)

                # ahora asignar queryset filtrado por pk
                self.valid_qs = Prestamos.objects.filter(pk__in=prestamos_validos)
            else:
                self.valid_qs = Prestamos.objects.none()
        else:
            self.valid_qs = Prestamos.objects.none()

        # Asignar queryset a cada campo prestamo_X
        for letter in ("A", "B", "C", "D", "E", "F"):
            self.fields[f"prestamo_{letter}"].queryset = self.valid_qs


    def clean(self):
        cleaned = super().clean()

        # Recolectar valores y préstamos seleccionados
        selected_pks = []
        total_aplicado = Decimal("0.00")

        for letter in ("A", "B", "C", "D", "E", "F"):
            prest_field = f"prestamo_{letter}"
            val_field = f"valor_{letter}"
            prest = cleaned.get(prest_field)
            val = cleaned.get(val_field)

            if prest and (val is None):
                raise forms.ValidationError(f"Debe indicar el valor para {prest_field} si selecciona un préstamo.")

            if val is not None and val != "":
                try:
                    val_dec = Decimal(val)
                except Exception:
                    raise forms.ValidationError(f"Valor inválido en {val_field}.")
                if val_dec <= Decimal("0"):
                    raise forms.ValidationError(f"El valor en {val_field} debe ser mayor que cero.")
                total_aplicado += val_dec

            if prest:
                if prest.pk in selected_pks:
                    raise forms.ValidationError("No puede seleccionar el mismo préstamo en más de un campo.")
                selected_pks.append(prest.pk)

                # verificar saldo disponible en el préstamo
                try:
                    saldo = prest.get_outstanding_balance()
                except Exception:
                    saldo = None
                if saldo is not None and Decimal(saldo) < (cleaned.get(val_field) or Decimal("0")):
                    raise forms.ValidationError(
                        f"El préstamo {prest.prestamo_id} no tiene saldo suficiente para el valor indicado en {val_field}."
                    )

        # Validar suma — si pago padre fue provisto, comparar
        if self.pago_padre:
            padre_valor = Decimal(str(self.pago_padre.valor_pago))
            if total_aplicado != padre_valor:
                raise forms.ValidationError(
                    f"La suma de los valores aplicados ({total_aplicado}) debe ser igual al valor del pago padre ({padre_valor})."
                )

        return cleaned


# ---------------------------
# ModelAdmin para InBox_PagosDetalle
# ---------------------------
#@admin.register(InBox_PagosDetalle)
class InBox_PagosDetalleAdmin(admin.ModelAdmin):
    list_display = (
        "pago_id",
        "prestamo_id_real",
        "cliente_id_real",
        "nombre_cliente",        # método que añadiremos abajo
        "valor_pago",
        "fecha_pago",
        "clase_movimiento",
        "estado_pago",
        "fecha_conciliacion",
        "fragment_action",
    )
    list_filter = ("estado_fragmentacion", "estado_pago")
    search_fields = ("pago_id", "cliente_id_real__nombre", "cliente_id_real__apellido")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filtrar por los que están A_FRAGMENTAR (según requerimiento principal)
        return qs.filter(estado_fragmentacion="A_FRAGMENTAR")

    def nombre_cliente(self, obj):
        # retorna nombre y apellido del cliente real si existe
        if obj.cliente_id_real:
            return f"{obj.cliente_id_real.nombre} {obj.cliente_id_real.apellido}"
        return ""
    nombre_cliente.short_description = "nombre cliente"

    def fragment_action(self, obj):
        url = reverse("admin:inbox_fragmentar", args=[obj.pago_id])
        return format_html('<a class="button" href="{}">Fragmentar</a>', url)
    fragment_action.short_description = "Fragmentar"

    # Agregar URL personalizado
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("fragment/<int:pago_id>/", self.admin_site.admin_view(self.fragment_view), name="inbox_fragmentar"),
        ]
        return custom + urls

    # Vista que muestra el subformulario de fragmentación
    def fragment_view(self, request, pago_id):
        pago = get_object_or_404(InBox_PagosDetalle, pago_id=pago_id)

        # Verificar permiso de cambio
        if not self.has_change_permission(request, pago):
            messages.error(request, "No tiene permiso para fragmentar este pago.")
            return redirect("..")

        if request.method == "POST":
            form = FragmentacionForm(request.POST, pago_padre=pago)
            if form.is_valid():
                # crear pagos hijos en transacción
                data = form.cleaned_data
                hijos_creados = []
                try:
                    with transaction.atomic():
                        for letter in ("A", "B", "C", "D", "E", "F"):
                            prest = data.get(f"prestamo_{letter}")
                            val = data.get(f"valor_{letter}")
                            if prest and val is not None:
                                # crear hijo
                                hijo = InBox_PagosDetalle(
                                    nombre_archivo_id=pago.nombre_archivo_id,
                                    fecha_carga_archivo=pago.fecha_carga_archivo,
                                    banco_origen=pago.banco_origen,
                                    cuenta_bancaria=pago.cuenta_bancaria,
                                    tipo_cuenta_bancaria=pago.tipo_cuenta_bancaria,
                                    canal_red_pago=pago.canal_red_pago,
                                    ref_bancaria=pago.ref_bancaria,
                                    ref_red=pago.ref_red,
                                    ref_cliente_1=pago.ref_cliente_1,
                                    ref_cliente_2=pago.ref_cliente_2,
                                    ref_cliente_3=pago.ref_cliente_3,
                                    estado_transaccion_reportado=pago.estado_transaccion_reportado,
                                    clase_movimiento=pago.clase_movimiento,
                                    estado_fragmentacion="FRAGMENTADO",
                                    cliente_id_reportado=pago.cliente_id_reportado,
                                    prestamo_id_reportado=pago.prestamo_id_reportado,
                                    cliente_id_real=pago.cliente_id_real,
                                    prestamo_id_real=prest,
                                    fecha_pago=pago.fecha_pago,
                                    fecha_conciliacion=pago.fecha_conciliacion,
                                    estado_pago=pago.estado_pago,
                                    estado_conciliacion=pago.estado_conciliacion,
                                    valor_pago=Decimal(str(val)),
                                    observaciones=f"Fragmentado de pago {pago.pago_id}",
                                    creado_por=request.user,
                                    fragmento_de=pago.pago_id,
                                )
                                hijo.save()
                                hijos_creados.append(hijo)

                        # actualizar padre
                        pago.estado_fragmentacion = "FRAGMENTADO"
                        pago.save()

                    # éxito
                    self.message_user(request, f"Se crearon {len(hijos_creados)} pagos hijos.", level=messages.SUCCESS)
                    # redirigir al changelist
                    #return redirect(reverse("admin:appfinancia_inbox_pagosdetalle_changelist"))
                    return redirect("admin:appfinancia_inbox_pagosdetalle_changelist")
                except Exception as e:
                    self.message_user(request, f"Error creando pagos hijos: {e}", level=messages.ERROR)

        else:
            form = FragmentacionForm(pago_padre=pago)

        # preparar contexto para template
        context = dict(
            self.admin_site.each_context(request),
            title=f"Fragmentar pago {pago.pago_id}",
            pago=pago,
            form=form,
            opts=self.model._meta,
        )

        return render(request, "admin/fragmentacion_pagos_form.html", context)




