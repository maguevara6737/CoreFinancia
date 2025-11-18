#!/bin/bash

# Cambia a la ruta del proyecto (ajusta si es necesario)
cd /root/CoreFinancia/

# Activa el entorno virtual
source  /root/CoreFinancia/venv/bin

python manage.py makemigrations
# Aplica migraciones
python manage.py migrate

# Ejecuta el servidor de desarrollo en 0.0.0.0:8000
python manage.py runserver 0.0.0.0:8000
