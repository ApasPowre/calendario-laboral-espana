"""
Debug del parser de festivos locales
"""

from scrapers.ccaa.madrid.locales import MadridLocalesScraper

scraper = MadridLocalesScraper(2026)
url = scraper.get_source_url()
content = scraper.fetch_content(url)

print("="*80)
print("PRIMERAS 2000 CARACTERES DEL CONTENIDO:")
print("="*80)
print(content[:2000])

print("\n" + "="*80)
print("BUSCAR PATRÓN '— Madrid:'")
print("="*80)

import re
patron = r'—\s*([^:]+):\s*([^.]+)\.'
matches = list(re.finditer(patron, content))

print(f"Total matches encontrados: {len(matches)}")

# Mostrar primeros 5 matches
for i, match in enumerate(matches[:5]):
    print(f"\nMatch {i+1}:")
    print(f"  Municipio: {match.group(1).strip()}")
    print(f"  Fechas: {match.group(2).strip()}")