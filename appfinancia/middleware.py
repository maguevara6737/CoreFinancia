from .models import Fechas_Sistema

class FechaSistemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        fecha = Fechas_Sistema.load()

        if fecha.modo_fecha_sistema == 'AUTOMATICO':
            fecha.actualizar_fechas_automaticas()
            fecha.save()

        request.fecha_sistema = fecha

        return self.get_response(request)
