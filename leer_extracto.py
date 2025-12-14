# leer_extracto.py
import pdfplumber
import sys

pdf_path ='/root/CoreFinancia/corefinancia_pedro/ejemplo_extracto_bancolombia.pdf'

def leer_pdf_a_texto(pdf_path):
    """
    Lee todas las páginas de un PDF y devuelve el texto completo.
    """
    texto_completo = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"🔍 Leyendo PDF: {pdf_path}")
            print(f"📄 Número de páginas: {len(pdf.pages)}\n")

            for i, pagina in enumerate(pdf.pages, 1):
                print(f"--- Página {i} ---")
                # Extraer texto manteniendo layout (espacios y saltos de línea)
                texto_pagina = pagina.extract_text(
                    layout=True,           # respeta espacios y alineación
                    x_tolerance=1,         # tolerancia horizontal baja → mejora columnas
                    y_tolerance=2          # tolerancia vertical
                ) or ""
                texto_pagina = texto_pagina.strip()
                if texto_pagina:
                    print(texto_pagina)
                    texto_completo.append(texto_pagina)
                else:
                    print("(Página vacía)")

        return "\n\n".join(texto_completo)

    except Exception as e:
        print(f"❌ Error al leer el PDF: {e}", file=sys.stderr)
        raise


def guardar_texto(texto, salida_txt):
    """
    Guarda el texto en un archivo .txt
    """
    try:
        with open(salida_txt, 'w', encoding='utf-8') as f:
            f.write(texto)
        print(f"\n✅ Texto guardado en: {salida_txt}")
    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    pdf_file = "ejemplo_extracto_bancolombia.pdf"
    txt_file = "extracto_bancolombia.txt"

    try:
        # 1. Leer PDF y mostrar en consola
        texto = leer_pdf_a_texto(pdf_file)

        # 2. Guardar en archivo .txt
        guardar_texto(texto, txt_file)

        print("\n🎉 Lectura completada con éxito.")
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: '{pdf_file}'", file=sys.stderr)
        print("➡️  Asegúrate de que el PDF esté en la misma carpeta que este script.")
    except Exception as e:
        print(f"💥 Error inesperado: {e}", file=sys.stderr)