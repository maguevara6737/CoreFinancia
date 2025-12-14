#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path

# Detectar la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = BASE_DIR / "CoreFinancia" / "settings.py"
JS_PATH = BASE_DIR / "appfinancia" / "static" / "appfinancia" / "js" / "number-format.js"
#JS_PATH = BASE_DIR / "corefinancia_pedro" / "static" / "appfinancia" / "js" / "number-format.js"
ADMIN_URL = "http://72.60.172.191:9000/admin/appfinancia/desembolsos/add/"

print("🔍 Diagnóstico de formato numérico: coma (miles) y punto (decimal)")
print("=" * 70)

# 1. Verificar settings.py
print("\n1. 📄 Configuración en settings.py")
if not SETTINGS_PATH.exists():
    print(f"❌ settings.py no encontrado en: {SETTINGS_PATH}")
    sys.exit(1)

with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    settings_content = f.read()

# Verificar clave por clave
checks = {
    "USE_THOUSAND_SEPARATOR = True": "USE_THOUSAND_SEPARATOR" in settings_content and "True" in settings_content.split("USE_THOUSAND_SEPARATOR")[1].split("\n")[0],
    "THOUSAND_SEPARATOR = ','": "THOUSAND_SEPARATOR = ','" in settings_content or "THOUSAND_SEPARATOR = \",\"" in settings_content,
    "DECIMAL_SEPARATOR = '.'": "DECIMAL_SEPARATOR = '.'" in settings_content,
    "LANGUAGE_CODE = 'es-co'": "LANGUAGE_CODE" in settings_content and "'es-co'" in settings_content or '"es-co"' in settings_content,
    "USE_L10N = True": "USE_L10N = True" in settings_content,
    "STATIC_URL = 'static/'": "STATIC_URL" in settings_content and "'static/'" in settings_content,
}

for desc, passed in checks.items():
    print(f"   {'✅' if passed else '❌'} {desc}")

# Extraer STATICFILES_DIRS real desde el archivo
import re
match = re.search(r"STATICFILES_DIRS\s*=\s*\[([^\]]+)\]", settings_content, re.DOTALL)
if match:
    dirs_raw = match.group(1)
    staticfiles_dirs = [d.strip().strip('"\'') for d in dirs_raw.split(",") if "os.path.join" in d or "BASE_DIR" in d]
    print(f"   ✅ STATICFILES_DIRS detectado (parcial): {staticfiles_dirs[:2]}...")
else:
    print("   ⚠️  STATICFILES_DIRS no encontrado o formato inusual")

# 2. Verificar archivo JS
print("\n2. 📁 Archivo JS de formato")
if JS_PATH.exists():
    print(f"   ✅ {JS_PATH.relative_to(BASE_DIR)} → EXISTE")
    with open(JS_PATH, "r", encoding="utf-8") as f:
        js_content = f.read()
    if "toLocaleString('en-US')" in js_content or "en-US" in js_content:
        print("   ✅ Usa 'en-US' para 1,000.50")
    else:
        print("   ⚠️  No se detecta 'en-US' en el JS (puede usar otro locale)")

    if "data.raw" in js_content and "onsubmit" in js_content:
        print("   ✅ Incluye lógica de restaurar valor crudo antes del envío")
    else:
        print("   ⚠️  Falta lógica de restaurar valor crudo → ¡Puede fallar el guardado!")
else:
    print(f"   ❌ {JS_PATH.relative_to(BASE_DIR)} → NO EXISTE")

# 3. Verificar que Django >= 4.0 (requisito para formato en admin sin formatos custom)
print("\n3. 🐍 Versión de Django")
try:
    import django
    print(f"   ✅ Django {django.get_version()}")
    from distutils.version import LooseVersion
    if LooseVersion(django.get_version()) >= LooseVersion("4.0"):
        print("   ✅ Versión compatible con USE_THOUSAND_SEPARATOR en admin")
    else:
        print("   ❌ Versión < 4.0: formato en admin puede no aplicarse sin formats.py")
except Exception as e:
    print(f"   ❌ Error al detectar versión: {e}")

# 4. Verificar que admin.py carga el JS
print("\n4. 🧪 Carga del JS en el admin (simulación)")
admin_py = BASE_DIR / "appfinancia" / "admin.py"
if admin_py.exists():
    with open(admin_py, "r", encoding="utf-8") as f:
        admin_content = f.read()
    if "class Media:" in admin_content and "number-format.js" in admin_content:
        print("   ✅ class Media con number-format.js encontrado en admin.py")
    else:
        print("   ❌ Falta 'class Media' o 'number-format.js' en admin.py")
else:
    print("   ⚠️  admin.py no encontrado")

# 5. Diagnóstico final
print("\n" + "=" * 70)
print("✅ DIAGNÓSTICO FINAL")

issues = []

if not all(checks.values()):
    issues.append("🔧 settings.py: faltan valores clave para formato numérico")
if not JS_PATH.exists():
    issues.append("📁 Falta el archivo JS: number-format.js")
if "class Media" not in locals().get("admin_content", "") or "number-format.js" not in locals().get("admin_content", ""):
    issues.append("⚙️  admin.py: no carga el JS personalizado")

if issues:
    print("❌ Se encontraron problemas:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n🛠️  Recomendación: Corrige los puntos arriba y reinicia el servidor.")
else:
    print("🎉 ¡Todo parece configurado correctamente!")
    print("   - Reinicia el servidor y prueba en el formulario.")