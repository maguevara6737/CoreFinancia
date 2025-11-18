from django import forms
from .models import Comentarios_Prestamos, Comentarios

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