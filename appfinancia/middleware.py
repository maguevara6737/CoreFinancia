# appfinancia/middleware.py   ----2025/11/26 pam - para cargar Fechas del Sistema
from .models import Fechas_Sistema
from django.utils import timezone

class ActualizarFechasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo en modo AUTOMATICO y en URLs de appfinancia (opcional)
        if hasattr(request, 'user') and request.path.startswith('/admin/appfinancia/'):
            Fechas_Sistema.load()  # Esto dispara la lógica de actualización en save()
        return self.get_response(request)
            
'''
# appfinancia/middleware.py   ----2025/11/26 pam - para cargar Fechas del Sistema
from .models import Fechas_Sistema
from django.utils import timezone

class ActualizarFechasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo en modo AUTOMATICO y en URLs de appfinancia (opcional)
        if hasattr(request, 'user') and request.path.startswith('/admin/appfinancia/'):
            Fechas_Sistema.load()  # Esto dispara la lógica de actualización en save()
        return self.get_response(request)
'''