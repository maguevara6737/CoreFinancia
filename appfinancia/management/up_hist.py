# update_historia_prestamos.py
import os
import sys
import django
from decimal import Decimal

#Ajustar la ruta y el módulo de configuración de Django
# if __name__ == "__main__":
   # Añadir el directorio del proyecto al path
    # sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    #Establecer la configuración de Django
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "corefinancia_miguel.settings")
    
    # django.setup()

    # Ahora podemos importar los modelos
    from appfinancia.models import Historia_Prestamos

    # Actualizar registro 1
    try:
        registro1 = Historia_Prestamos.objects.get(id=1208)
        registro1.capital_aplicado_periodo = Decimal('1000000.00')
        registro1.numero_pago_referencia = "PAGO_059"
        registro1.save()
        print("✅ Registro ID=1208 actualizado: capital_aplicado_periodo=1000000.00, numero_pago_referencia='PAGO_059'")
    except Historia_Prestamos.DoesNotExist:
        print("❌ Registro ID=1208 no encontrado.")

    # Actualizar registro 2
    try:
        registro2 = Historia_Prestamos.objects.get(id=1565)
        registro2.capital_aplicado_periodo = Decimal('218333.33')
        registro2.numero_pago_referencia = "PAGO_100"
        registro2.save()
        print("✅ Registro ID=1565 actualizado: capital_aplicado_periodo=218333.33, numero_pago_referencia='PAGO_100'")
    except Historia_Prestamos.DoesNotExist:
        print("❌ Registro ID=1565 no encontrado.")

    print("✔️ Actualización completada.")   