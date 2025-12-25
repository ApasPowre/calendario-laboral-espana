"""
Debug de Semana Santa - ¿Por qué no se extraen?
"""

from scrapers.core.boe_scraper import BOEScraper

scraper = BOEScraper(2023)
url = scraper.get_source_url()
content = scraper.fetch_content(url)

content_lower = content.lower()

print("="*80)
print("BÚSQUEDA DE SEMANA SANTA EN EL CONTENIDO")
print("="*80)

# ¿Está "jueves santo"?
if 'jueves santo' in content_lower:
    print("\n✅ 'jueves santo' ENCONTRADO en el contenido")
    idx = content_lower.find('jueves santo')
    contexto = content[max(0, idx-300):min(len(content), idx+300)]
    print(f"\nContexto alrededor de 'jueves santo':")
    print(contexto)
    print("\n" + "-"*80)
else:
    print("\n❌ 'jueves santo' NO encontrado")

# ¿Está "viernes santo"?
if 'viernes santo' in content_lower:
    print("\n✅ 'viernes santo' ENCONTRADO en el contenido")
    idx = content_lower.find('viernes santo')
    contexto = content[max(0, idx-300):min(len(content), idx+300)]
    print(f"\nContexto alrededor de 'viernes santo':")
    print(contexto)
    print("\n" + "-"*80)
else:
    print("\n❌ 'viernes santo' NO encontrado")

# Buscar patrones con "6 de abril" y "7 de abril"
print("\n" + "="*80)
print("BÚSQUEDA DE FECHAS DE ABRIL")
print("="*80)

import re
patron = r'(\d{1,2})\s+de\s+abril'
matches = re.findall(patron, content_lower)

if matches:
    print(f"\n✅ Encontradas fechas de abril: {set(matches)}")
    
    for dia in set(matches):
        idx = content_lower.find(f"{dia} de abril")
        contexto = content[max(0, idx-200):min(len(content), idx+200)]
        print(f"\nContexto de '{dia} de abril':")
        print(contexto[:300])
        print("-"*80)
else:
    print("\n❌ No se encontraron fechas de abril")