from django.apps import AppConfig


class AppfinanciaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appfinancia'

#Para la Fragmentación de pago 2025/12/10
class FragmentacionConfig:
    verbose_name = "Fragmentación de Pagos"