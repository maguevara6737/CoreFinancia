# appfinancia/admin_consultas.py

from django.contrib.admin import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Fechas_Sistema

class ConsultasReportesAdminSite(AdminSite):
    site_header = "Consultas y Reportes - CoreFinancia"
    site_title = "Consultas y Reportes"
    index_title = "Panel de Consultas Financieras"

    def has_permission(self, request):
        # Verificar permiso personalizado
        return request.user.has_perm('appfinancia.puede_consultar_causacion')

# Crear instancia
consultas_admin_site = ConsultasReportesAdminSite(name='consultas_admin')