#!/bin/bash
set -e  # Detener si hay error

echo "📍 Cargando municipios..."
psql -h localhost -U postgres -d corefinancia_db -f "/root/CoreFinancia/scripts_load/catalogo_municipios.sql" -w
echo "✅ ¡Municipios cargados exitosamente!"