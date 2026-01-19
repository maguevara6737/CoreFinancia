#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corefinancia_miguel.settings')
django.setup()

# Importar modelos
from appfinancia.models import Historia_Prestamos

def main():
    MESES_SIN_30 = {2}
    registros = Historia_Prestamos.objects.filter(
        prestamo_id__prestamo_id=90035,
        fecha_vencimiento__day=28
    )
    print("🔄 Actualizando fechas a día 30 (excepto febrero)...")
    actualizados = 0

    for reg in registros:
        fv = reg.fecha_vencimiento
        fv_date = fv.date() if hasattr(fv, 'date') else fv
        
        if fv_date.month in MESES_SIN_30:
            print(f"  ℹ️  ID {reg.id}: {fv_date} → febrero, omitido")
            continue

        try:
            nueva_fecha = date(fv_date.year, fv_date.month, 30)
            if nueva_fecha != fv_date:
                reg.fecha_vencimiento = nueva_fecha
                reg.save()
                print(f"  ✅ ID {reg.id}: {fv_date} → {nueva_fecha}")
                actualizados += 1
            else:
                print(f"  ℹ️  ID {reg.id}: ya es {fv_date}")
        except Exception as e:
            print(f"  ❌ Error en ID {reg.id}: {e}")

    print(f"\n✅ Total actualizados: {actualizados}")

if __name__ == '__main__':
    main()