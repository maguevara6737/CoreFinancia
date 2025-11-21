#!/bin/bash

# Cambia a la ruta del proyecto (ajusta si es necesario)
#cd /root/CoreFinancia/

# Activa el entorno virtual
#source ../venv/bin/activate

#python3 manage.py makemigrations
# Aplica migraciones
#python3 manage.py migrate

# Ejecuta el servidor de desarrollo en 0.0.0.0:8000
python3 manage.py runserver 0.0.0.0:8000
