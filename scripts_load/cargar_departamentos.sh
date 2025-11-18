#!/bin/bash
set -e  # Detener si hay error

echo "📍 Cargando departamentos..."
psql -h localhost -U postgres -d corefinancia_db -f "/root/CoreFinancia/scripts_load/catalogo_departamentos.sql" -w
echo "✅ ¡Departamentos cargados exitosamente!"