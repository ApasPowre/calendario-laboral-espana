"""
Auto-discovery para BOCM Madrid usando búsqueda avanzada
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from urllib.parse import urlencode
import pdfplumber
from io import BytesIO


def buscar_en_bocm(year_publicacion: int, keywords: str, validar_contenido: list) -> Optional[str]:
    """
    Busca documentos en el BOCM usando el buscador avanzado
    
    Args:
        year_publicacion: Año de publicación
        keywords: Palabras clave para la búsqueda
        validar_contenido: Lista de palabras que deben aparecer en el PDF
        
    Returns:
        URL del PDF encontrado o None
    """
    
    # Construir URL de búsqueda con parámetros
    params = {
        'search_api_views_fulltext_1': keywords,
        'field_bulletin_field_date_y_hidden[year]': str(year_publicacion),
    }
    
    url_busqueda = "https://www.bocm.es/advanced-search?" + urlencode(params)
    
    try:
        print(f"   📡 Buscando: '{keywords}' en {year_publicacion}")
        
        response = requests.get(url_busqueda, timeout=15)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer resultados (divs con clase views-row)
        resultados = soup.find_all('div', class_='views-row')
        
        print(f"   📋 {len(resultados)} resultados encontrados")
        
        # Probar cada resultado
        for i, resultado in enumerate(resultados[:10], 1):  # Máximo 10
            # Buscar enlace al PDF
            pdf_link = resultado.find('a', href=lambda x: x and '.PDF' in x)
            
            if not pdf_link:
                continue
            
            pdf_url = pdf_link['href']
            
            # Validar contenido del PDF
            try:
                pdf_r = requests.get(pdf_url, timeout=10)
                
                if pdf_r.status_code != 200:
                    continue
                
                # Extraer texto de las primeras páginas
                with pdfplumber.open(BytesIO(pdf_r.content)) as pdf:
                    texto = ""
                    for page in pdf.pages[:3]:
                        texto += page.extract_text()
                    
                    texto_upper = texto.upper()
                    
                    # Verificar que contenga todas las palabras de validación
                    if all(palabra.upper() in texto_upper for palabra in validar_contenido):
                        print(f"   ✅ Encontrado: {pdf_url}")
                        return pdf_url
                        
            except Exception as e:
                continue
        
        print(f"   ❌ No se encontró documento válido")
        return None
        
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None


def buscar_orden_autonomicos(year: int) -> Optional[str]:
    """
    Busca Decreto de festivos autonómicos en el BOCM
    
    Args:
        year: Año objetivo (ej: 2026)
        
    Returns:
        URL del PDF o None
    """
    
    print(f"🔍 Buscando Decreto autonómicos Madrid {year}...")
    
    year_publicacion = year - 1
    
    # Buscar decreto de fiestas laborales
    keywords = f'decreto fiestas laborales {year}'
    validar = [str(year), 'decreto', 'fiestas', 'laborales', 'comunidad']
    
    url = buscar_en_bocm(year_publicacion, keywords, validar)
    
    return url


def buscar_orden_locales(year: int) -> Optional[str]:
    """
    Busca Resolución de festivos locales en el BOCM
    
    Args:
        year: Año objetivo (ej: 2026)
        
    Returns:
        URL del PDF o None
    """
    
    print(f"🔍 Buscando Resolución locales Madrid {year}...")
    
    year_publicacion = year - 1
    
    # Buscar orden/resolución de fiestas locales
    keywords = f'festivos locales {year}'
    validar = [str(year), 'locales', 'fiestas', 'madrid']
    
    url = buscar_en_bocm(year_publicacion, keywords, validar)
    
    return url


def auto_discover_madrid(year: int) -> Dict[str, Optional[str]]:
    """
    Descubre automáticamente las URLs para Madrid (paralelizado)
    
    Returns:
        Dict con 'autonomicos' y 'locales' URLs
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY BOCM MADRID {year}")
    print("=" * 80)
    
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    start_time = time.time()
    urls = {'autonomicos': None, 'locales': None}
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_autonomicos = executor.submit(buscar_orden_autonomicos, year)
        future_locales = executor.submit(buscar_orden_locales, year)
        
        for future in as_completed([future_autonomicos, future_locales]):
            try:
                if future == future_autonomicos:
                    urls['autonomicos'] = future.result()
                else:
                    urls['locales'] = future.result()
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
    
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
