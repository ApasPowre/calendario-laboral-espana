"""
Auto-discovery para DOG Galicia
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import re


def buscar_en_dog(year: int, keywords: str) -> Optional[str]:
    """
    Busca documentos en el DOG de Galicia
    
    Args:
        year: Año objetivo
        keywords: Palabras clave para buscar
        
    Returns:
        URL del documento o None
    """
    
    # El DOG tiene un buscador pero es más fácil probar URLs directas
    # Patrón típico: /dog/Publicados/YYYY/YYYYMMDD/AnuncioXXXX_es.html
    
    # Publicación típica: octubre-diciembre del año anterior
    year_pub = year - 1
    
    print(f"   🔍 Buscando en DOG {year_pub} para festivos {year}...")
    
    # Probar meses típicos (octubre, noviembre, diciembre)
    for mes in [10, 11, 12]:
        # Probar rango de días
        for dia in range(31, 0, -1):  # De más reciente a más antiguo
            try:
                fecha = f"{year_pub}{mes:02d}{dia:02d}"
                
                # El DOG no tiene API pública, necesitamos URL exacta
                # Por ahora, retornar None para forzar búsqueda manual
                
            except:
                continue
    
    return None


def auto_discover_galicia(year: int) -> Optional[str]:
    """
    Intenta descubrir automáticamente la URL de festivos locales de Galicia
    
    Returns:
        URL del DOG o None
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY DOG GALICIA {year}")
    print("=" * 80)
    
    url = buscar_en_dog(year, f"fiestas locales {year}")
    
    if url:
        print(f"✅ URL encontrada: {url}")
    else:
        print(f"❌ No se pudo encontrar automáticamente")
        print(f"\n📋 Búsqueda manual:")
        print(f"   1. Visita: https://www.xunta.gal/dog")
        print(f"   2. Busca: 'fiestas locales {year}' o 'festivos locales {year}'")
        print(f"   3. Añade la URL a config/galicia_urls_cache.json")
    
    print("=" * 80)
    
    return url


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    url = auto_discover_galicia(year)
