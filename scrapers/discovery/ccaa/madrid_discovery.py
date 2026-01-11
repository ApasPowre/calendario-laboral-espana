"""
Auto-discovery para BOCM Madrid scrapeando resultados de búsqueda
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
import re


def scrapear_resultados_bocm(year_publicacion: int, keywords: list) -> Optional[str]:
    """
    Scrapea resultados del buscador avanzado del BOCM
    
    Args:
        year_publicacion: Año de publicación
        keywords: Palabras clave a buscar en resultados
        
    Returns:
        URL del PDF encontrado o None
    """
    
    # Construir URL del buscador (simplificada)
    # Buscar "fiestas laborales" en año específico
    url_busqueda = f"https://www.bocm.es/advanced-search/p/field_buletin_field_date_y_hidden/year__{year_publicacion}"
    
    try:
        print(f"   📡 Consultando: {url_busqueda}")
        
        response = requests.get(url_busqueda, timeout=15)
        
        if response.status_code != 200:
            print(f"   ⚠️  Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar en todos los resultados
        # Los resultados suelen estar en divs o artículos con clase específica
        resultados = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'resultado|result|item|entry'))
        
        if not resultados:
            # Intentar encontrar todos los enlaces
            resultados = soup.find_all('a', href=True)
        
        for resultado in resultados:
            texto = resultado.get_text().lower()
            
            # Verificar que contenga todas las keywords
            if all(kw.lower() in texto for kw in keywords):
                # Buscar enlace al PDF
                link = resultado.find('a', href=re.compile(r'\.PDF|\.pdf'))
                
                if not link:
                    link = resultado if resultado.name == 'a' else resultado.find('a')
                
                if link and 'href' in link.attrs:
                    href = link['href']
                    
                    # Construir URL completa
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        return f"https://www.bocm.es{href}"
                    else:
                        return f"https://www.bocm.es/{href}"
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None


def buscar_orden_autonomicos(year: int) -> Optional[str]:
    """
    Busca festivos autonómicos en el BOCM
    
    Args:
        year: Año objetivo (ej: 2026)
        
    Returns:
        URL del PDF o None
    """
    
    year_publicacion = year - 1
    
    print(f"🔍 Buscando Decreto autonómicos Madrid {year}...")
    print(f"   📅 Año de publicación: {year_publicacion}")
    
    # Keywords específicos
    keywords = ['fiestas', 'laborales', str(year), 'decreto']
    
    url = scrapear_resultados_bocm(year_publicacion, keywords)
    
    if url:
        print(f"   ✅ Encontrado")
        return url
    
    # Si no encontrado, probar búsqueda más amplia
    keywords = ['fiestas', 'laborales', str(year)]
    url = scrapear_resultados_bocm(year_publicacion, keywords)
    
    if url:
        print(f"   ✅ Encontrado (búsqueda amplia)")
        return url
    
    print(f"   ❌ No encontrado")
    return None


def buscar_orden_locales(year: int) -> Optional[str]:
    """
    Busca festivos locales en el BOCM
    
    Args:
        year: Año objetivo (ej: 2026)
        
    Returns:
        URL del PDF o None
    """
    
    year_publicacion = year - 1
    
    print(f"🔍 Buscando Resolución locales Madrid {year}...")
    print(f"   📅 Año de publicación: {year_publicacion}")
    
    # Keywords específicos
    keywords = ['fiestas', 'locales', str(year)]
    
    url = scrapear_resultados_bocm(year_publicacion, keywords)
    
    if url:
        print(f"   ✅ Encontrado")
        return url
    
    print(f"   ❌ No encontrado")
    return None


def auto_discover_madrid(year: int) -> Dict[str, Optional[str]]:
    """
    Descubre automáticamente las URLs para Madrid
    
    Returns:
        Dict con 'autonomicos' y 'locales' URLs
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY BOCM MADRID {year}")
    print("=" * 80)
    
    # Paralelizar búsquedas de autonómicos y locales
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    start_time = time.time()
    urls = {'autonomicos': None, 'locales': None}
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Lanzar ambas búsquedas en paralelo
        future_autonomicos = executor.submit(buscar_orden_autonomicos, year)
        future_locales = executor.submit(buscar_orden_locales, year)
        
        # Recoger resultados
        for future in as_completed([future_autonomicos, future_locales]):
            try:
                if future == future_autonomicos:
                    urls['autonomicos'] = future.result()
                else:
                    urls['locales'] = future.result()
            except Exception as e:
                print(f"   ⚠️  Error en búsqueda: {e}")
    
    elapsed = time.time() - start_time
    
    print("=" * 80)
    print("📋 RESULTADOS:")
    print(f"   Autonómicos: {urls['autonomicos'] or 'NO ENCONTRADO'}")
    print(f"   Locales: {urls['locales'] or 'NO ENCONTRADO'}")
    print(f"   ⏱️  Tiempo: {elapsed:.2f}s")
    print("=" * 80)
    
    return urls


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    
    urls = auto_discover_madrid(year)