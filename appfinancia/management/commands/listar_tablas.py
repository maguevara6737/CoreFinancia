# listar_tablas.py
import os
import sys
import django

# Añadir la raíz del proyecto al path (por si acaso)
sys.path.append('/root/CoreFinancia')

# Configurar Django con el nombre correcto del módulo de settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corefinancia_miguel.settings')

django.setup()

from django.db import connection

tablas = connection.introspection.table_names()

print("=== Tablas en la base de datos ===")
for tabla in sorted(tablas):
    print(tabla)

# Buscar tablas relacionadas con 'detalle'
detalle_tablas = [t for t in tablas if 'detalle' in t.lower()]
if detalle_tablas:
    print("\n=== Tablas con 'detalle' ===")
    for t in sorted(detalle_tablas):
        print(t)
else:
    print("\n⚠️ No se encontraron tablas con 'detalle' en el nombre.")