from datetime import date
from django import forms
from .models import Comentarios_Prestamos, Comentarios, Fechas_Sistema, Prestamos

class ComentarioPrestamoForm(forms.ModelForm):
    class Meta:
        model = Comentarios_Prestamos
        fields = ['comentario_catalogo']
        widgets = {
            'comentario_catalogo': forms.Select(
                attrs={'class': 'form-control'},
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo comentarios habilitados
        self.fields['comentario_catalogo'].queryset = Comentarios.objects.filter(estado='HABILITADO')
        
#------------------------------
#formulario para Fragmentación
#------------------------------
# appfinancia/forms.py
from django import forms
from decimal import Decimal, InvalidOperation
from .models import Prestamos

LETTERS = ("A", "B", "C", "D", "E", "F")

class FragmentacionForm(forms.Form):
    """
    Form dinámico: en init recibe 'pago_padre' para limitar querysets de préstamos.
    Campos: prestamo_A ... prestamo_F (ModelChoice) y valor_A ... valor_F (Decimal)
    """

    def __init__(self, *args, pago_padre=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pago_padre = pago_padre

        qs_base = Prestamos.objects.none()
        if pago_padre and pago_padre.cliente_id_real:
            qs_base = Prestamos.objects.filter(cliente_id=pago_padre.cliente_id_real)

        for letter in LETTERS:
            self.fields[f"prestamo_{letter}"] = forms.ModelChoiceField(
                queryset=qs_base,
                required=False,
                label=f"Préstamo {letter}"
            )
            self.fields[f"valor_{letter}"] = forms.DecimalField(
                max_digits=15, decimal_places=2,
                required=False,
                min_value=Decimal("0.00"),
                label=f"Valor {letter}"
            )

    def clean(self):
        cleaned = super().clean()
        suma = Decimal("0.00")
        seleccionados = set()

        for letter in LETTERS:
            prest = cleaned.get(f"prestamo_{letter}")
            val = cleaned.get(f"valor_{letter}")

            # Si se selecciona préstamo, debe venir valor
            if prest and (val is None):
                raise forms.ValidationError(f"Debe indicar valor para el préstamo {letter} si lo selecciona.")

            # Si hay valor sin préstamo, error
            if (val is not None) and (not prest):
                raise forms.ValidationError(f"Debe seleccionar un préstamo para el valor en {letter}.")

            if val is not None and val != "":
                try:
                    val_dec = Decimal(val)
                except (InvalidOperation, TypeError):
                    raise forms.ValidationError(f"Valor inválido para {letter}.")
                if val_dec <= Decimal("0"):
                    raise forms.ValidationError(f"El valor para {letter} debe ser mayor que 0.")
                suma += val_dec

            if prest:
                if prest.pk in seleccionados:
                    raise forms.ValidationError("No puede seleccionar el mismo préstamo en más de un campo.")
                seleccionados.add(prest.pk)

        # Si pagó padre está presente, comparar suma: sólo si se ingresó al menos un fragmento
        padre_valor = getattr(self.pago_padre, "valor_pago", None)
        if padre_valor is not None:
            if suma > 0 and Decimal(suma) != Decimal(str(padre_valor)):
                raise forms.ValidationError(
                    f"La suma de fragmentos ({suma}) debe ser igual al valor del pago padre ({padre_valor})."
                )

        return cleaned


#=============================================
#Regularización de pagos: clientes y préstamos
#=============================================
from django import forms
from .models import InBox_PagosDetalle, Clientes, Prestamos


class RegularizarPagoForm(forms.ModelForm):

    class Meta:
        model = InBox_PagosDetalle
        fields = (
            "cliente_id_real",
            "prestamo_id_real",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si ya hay cliente, filtrar préstamos
        if self.instance and self.instance.cliente_id_real:
            self.fields["prestamo_id_real"].queryset = Prestamos.objects.filter(
                cliente_id=self.instance.cliente_id_real,
                saldo__gt=0
            )
        else:
            self.fields["prestamo_id_real"].queryset = Prestamos.objects.none()

# appfinancia/forms.py

#
#Class CausacionInteresesForm(forms.Form):
#   fecha_inicio = forms.DateField(
#       label="Fecha de inicio",
#       widget=forms.DateInput(attrs={'type': 'date'}),
#       help_text="Desde esta fecha (inclusive) se causarán intereses."
#   )
#   fecha_fin = forms.DateField(
#       label="Fecha de fin",
#       widget=forms.DateInput(attrs={'type': 'date'}),
#       help_text="Hasta esta fecha (inclusive) se causarán intereses."
#   )
#  
# 
# appfinancia/forms.py
# ------------------------------------------------------------------------------
# Formulario para Consulta de Causación (El formulario ajustado)
# ------------------------------------------------------------------------------
# forms.py
# appfinancia/forms.py
# appfinancia/forms.py
# appfinancia/forms.py
from django import forms
from datetime import date

class ConsultaCausacionForm(forms.Form):
    REPORTE_OPCIONES = [
        ('pantalla', 'Solo Totales por pantalla'),
        ('excel', 'Detalle y Totales a Excel'),
    ]

    fecha_inicio = forms.DateField(
        label="Fecha de inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'fecha-campo'})
    )
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'fecha-campo'})
    )
    tipo_reporte = forms.ChoiceField(
        choices=REPORTE_OPCIONES,
        label="Tipo de reporte",
        widget=forms.RadioSelect,
        initial='pantalla'
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError("La fecha de inicio no puede ser mayor que la fecha de fin.")
            if fecha_inicio < date(2020, 12, 31):
                raise forms.ValidationError("La fecha de inicio no puede ser anterior a 2020-12-31.")
            from .models import Fechas_Sistema
            fechas_sistema = Fechas_Sistema.objects.first()
            if fechas_sistema:
                if fecha_fin > fechas_sistema.fecha_proceso_actual:
                    raise forms.ValidationError(
                        f"La fecha de fin no puede ser posterior a la fecha de proceso del sistema ({fechas_sistema.fecha_proceso_actual})."
                    )
            else:
                raise forms.ValidationError("No se ha configurado la fecha de proceso del sistema.")
        return cleaned_data
    
class BalanceOperacionesForm(forms.Form):
    fecha_corte = forms.DateField(
        label='Fecha de Corte',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField'}),
        initial=date.today
    )
# forms.py
from django import forms

class PrestamosVencidosForm(forms.Form):
    # Sin campos: la fecha es fija (hoy = fecha_proceso_actual)
    pass
