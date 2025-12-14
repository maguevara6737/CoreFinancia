#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Configurar Django
BASE_DIR = Path("/root/CoreFinancia")
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CoreFinancia.settings")

import django
django.setup()

from django.conf import settings
import socket

print("=" * 60)
print("🔍 Diagnóstico de configuración de sesión (HTTP/HTTPS)")
print("=" * 60)

# === 1. Detectar entorno ===
server_software = "Desconocido"

# Método robusto: revisar sys.argv y módulos cargados
if 'runserver' in ' '.join(sys.argv).lower():
    server_software = "Django runserver"
elif 'gunicorn' in sys.modules or 'gunicorn' in ' '.join(sys.argv):
    server_software = "Gunicorn (+ nginx/Apache)"
elif 'mod_wsgi' in sys.modules:
    server_software = "Apache/mod_wsgi"

print(f"🌐 Entorno detectado: {server_software}")

# === 2. Protocolo ===
protocol = "HTTP"  # por defecto en desarrollo
if settings.SESSION_COOKIE_SECURE and settings.SECURE_SSL_REDIRECT:
    protocol = "HTTPS"

print(f"🔐 Protocolo inferido: {protocol}")

# === 3. Verificaciones ===
checks = []

# 3.1 SESSION_EXPIRE_AT_BROWSER_CLOSE
if getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False):
    print("✅ SESSION_EXPIRE_AT_BROWSER_CLOSE = True")
else:
    print("❌ SESSION_EXPIRE_AT_BROWSER_CLOSE debe ser True")

# 3.2 SESSION_COOKIE_SECURE
secure_cookie = getattr(settings, 'SESSION_COOKIE_SECURE', False)
expected_secure = (protocol == "HTTPS")
if secure_cookie == expected_secure:
    status = "✅" if expected_secure else "✅ (HTTP → False)"
    print(f"{status} SESSION_COOKIE_SECURE = {secure_cookie}")
else:
    print(f"❌ SESSION_COOKIE_SECURE = {secure_cookie} (esperado: {expected_secure})")

# 3.3 DEBUG
if settings.DEBUG:
    print("ℹ️  DEBUG = True (modo desarrollo)")
else:
    print("ℹ️  DEBUG = False (modo producción)")

print("\n" + "=" * 60)
print("🎉 ¡Configuración de sesión correcta!" if all([
    getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False),
    secure_cookie == expected_secure
]) else "⚠️  Configuración necesita ajustes.")
print("=" * 60)