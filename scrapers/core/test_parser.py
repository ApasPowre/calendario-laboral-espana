"""
Test del parser de festivos - Debug detallado
"""

from scrapers.core.boe_scraper import BOEScraper

# Crear scraper para 2023
scraper = BOEScraper(2023)

# Obtener contenido
url = scraper.get_source_url()
print(f"URL: {url}\n")

content = scraper.fetch_content(url)
print(f"Contenido descargado: {len(content)} caracteres\n")

print("="*80)
print("ESTRATEGIA 1: Tabla HTML")
print("="*80)
festivos_tabla = scraper._parse_tabla_html(content)
print(f"Festivos encontrados: {len(festivos_tabla)}")
for f in festivos_tabla:
    print(f"  - {f['fecha']} | {f['descripcion']}")

print("\n" + "="*80)
print("ESTRATEGIA 2: Texto con patrones")
print("="*80)
festivos_texto = scraper._parse_texto_patrones(content)
print(f"Festivos encontrados: {len(festivos_texto)}")
for f in festivos_texto:
    print(f"  - {f['fecha']} | {f['descripcion']}")

print("\n" + "="*80)
print("ESTRATEGIA 3: Patrones conocidos (fallback)")
print("="*80)
festivos_conocidos = scraper._parse_patrones_conocidos(content)
print(f"Festivos encontrados: {len(festivos_conocidos)}")
for f in festivos_conocidos:
    print(f"  - {f['fecha']} | {f['descripcion']}")

print("\n" + "="*80)
print("FESTIVOS QUE DEBERÍAN ESTAR (2023):")
print("="*80)
esperados = [
    "2023-01-06 - Epifanía del Señor",
    "2023-04-06 - Jueves Santo",
    "2023-04-07 - Viernes Santo",
    "2023-05-01 - Fiesta del Trabajo",
    "2023-08-15 - Asunción de la Virgen",
    "2023-10-12 - Fiesta Nacional de España",
    "2023-11-01 - Todos los Santos",
    "2023-12-06 - Día de la Constitución",
    "2023-12-08 - Inmaculada Concepción",
    "2023-12-25 - Natividad del Señor"
]

for esp in esperados:
    print(f"  {esp}")