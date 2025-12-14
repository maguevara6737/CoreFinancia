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