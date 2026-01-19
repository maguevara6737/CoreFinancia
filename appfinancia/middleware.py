from .models import Fechas_Sistema

class FechaSistemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
<<<<<<< HEAD
        if request.path.startswith('/admin/appfinancia/'):
            from .models import Fechas_Sistema  # ← dentro del método
            Fechas_Sistema.load()
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
=======
        fecha = Fechas_Sistema.load()

        if fecha.modo_fecha_sistema == 'AUTOMATICO':
            fecha.actualizar_fechas_automaticas()
            fecha.save()

        request.fecha_sistema = fecha

        return self.get_response(request)
>>>>>>> ec18317bfe68f0329fb6b89084b6350a4792a973
