"""
Script de diagnóstico para ver el contenido del BOC
"""

import requests
from bs4 import BeautifulSoup
import re

url = "https://www.gobiernodecanarias.org/boc/2025/165/3029.html"

print("📥 Descargando BOC...")
response = requests.get(url, timeout=30)
response.encoding = 'utf-8'
html = response.text

print("✅ Descargado\n")

# Extraer el texto
soup = BeautifulSoup(html, 'lxml')
contenido = soup.get_text()

# Buscar ANEXO
anexo_pos = contenido.find("ANEXO")
print(f"Posición de ANEXO: {anexo_pos}")

if anexo_pos > 0:
    # Mostrar texto alrededor del anexo
    print("\n📄 Texto alrededor de ANEXO:")
    print(contenido[anexo_pos:anexo_pos+500])
    print("\n" + "="*80 + "\n")
    
    # Buscar los primeros municipios manualmente
    contenido_anexo = contenido[anexo_pos:]
    
    # Buscar las primeras líneas que podrían ser municipios
    lineas = contenido_anexo.split('\n')[:100]
    
    print("🔍 Primeras 100 líneas después de ANEXO:")
    for i, linea in enumerate(lineas):
        if linea.strip():  # Solo líneas no vacías
            print(f"{i:3d}: '{linea}'")
else:
    print("❌ No se encontró ANEXO")
    print("\n🔍 Primeras 1000 caracteres del documento:")
    print(contenido[:1000])