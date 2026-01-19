#!/bin/bash

# ===== CONFIG =====
PROJECT_DIR="/root/CoreFinancia/corefinancia_pedro"
VENV_DIR="/root/CoreFinancia/venv"
LOG_DIR="/root/CoreFinancia/logs"
LOG_FILE="$LOG_DIR/financiacion_email.log"

# ===== LOGS =====
mkdir -p $LOG_DIR
echo "========================================" >> $LOG_FILE
echo "$(date) - INICIO PROCESO FINANCIACION" >> $LOG_FILE

# ===== ACTIVAR ENTORNO =====
cd $PROJECT_DIR || exit
source $VENV_DIR/bin/activate

# ===== EJECUTAR PROCESO =====
python manage.py financiacion_leer_email >> $LOG_FILE 2>&1

# ===== FIN =====
echo "$(date) - FIN PROCESO FINANCIACION" >> $LOG_FILE
