"""
Auto-discovery para BOC Canarias
Busca Decretos y Órdenes de festivos laborales automáticamente
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict
import time


def buscar_en_boc(year_publicacion: int, numero_inicio: int, numero_fin: int, 
                  palabras_clave: list, tipo: str) -> Optional[str]:
    """
    Busca en el BOC por rango de números
    
    Args:
        year_publicacion: Año de publicación del BOC
        numero_inicio: Número BOC inicial
        numero_fin: Número BOC final
        palabras_clave: Lista de palabras a buscar
        tipo: 'decreto' o 'orden'
    
    Returns:
        URL del documento o None
    """
    
    print(f"   🔍 Buscando en BOC {numero_inicio}-{numero_fin}/{year_publicacion}...")
    
    for numero_boc in range(numero_inicio, numero_fin + 1):
        try:
            # URL del índice del boletín
            url_indice = f"https://www.gobiernodecanarias.org/boc/{year_publicacion}/{numero_boc:03d}/"
            
            response = requests.get(url_indice, timeout=10)
            if response.status_code != 200:
                continue
            
            contenido_lower = response.text.lower()
            
            # Verificar si contiene todas las palabras clave
            contiene_todas = all(palabra.lower() in contenido_lower for palabra in palabras_clave)
            
            if contiene_todas:
                # Parsear HTML para encontrar el enlace exacto
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar enlaces que contengan las palabras clave
                for link in soup.find_all('a', href=True):
                    texto_link = link.get_text().lower()
                    
                    # Verificar tipo de documento
                    if tipo == 'decreto' and 'decreto' in texto_link:
                        href = link['href']
                    elif tipo == 'orden' and 'orden' in texto_link:
                        href = link['href']
                    else:
                        continue
                    
                    # Verificar que el enlace contenga las palabras clave
                    if all(palabra.lower() in texto_link for palabra in palabras_clave):
                        # Construir URL completa
                        if href.startswith('http'):
                            url_completa = href
                        else:
                            # Extraer número de anuncio del href
                            match = re.search(r'/(\d+)\.html', href)
                            if match:
                                num_anuncio = match.group(1)
                                url_completa = f"https://www.gobiernodecanarias.org/boc/{year_publicacion}/{numero_boc}/{num_anuncio}.html"
                            else:
                                continue
                        
                        print(f"   ✅ Encontrado: BOC {numero_boc}/{year_publicacion}")
                        
                        # Convertir PDF a HTML si es necesario
                        if '.pdf' in url_completa:
                            url_html = convertir_pdf_a_html_url(url_completa)
                            if url_html:
                                print(f"   🔄 Convirtiendo a HTML: {url_html}")
                                return url_html
                        
                        return url_completa
            
            # Rate limiting
            time.sleep(0.1)
        
        except Exception as e:
            continue
    
    return None

def convertir_pdf_a_html_url(url_pdf: str) -> Optional[str]:
    """
    Convierte URL de PDF del BOC a URL HTML
    
    Ejemplo:
    IN:  https://sede.gobiernodecanarias.org/boc/boc-a-2024-187-3013.pdf
    OUT: https://www.gobiernodecanarias.org/boc/2024/187/3013.html
    """
    
    # Patrón: boc-a-{año}-{numero}-{anuncio}.pdf
    match = re.search(r'boc-a-(\d{4})-(\d+)-(\d+)\.pdf', url_pdf)
    
    if match:
        year = match.group(1)
        numero = match.group(2)
        anuncio = match.group(3)
        
        url_html = f"https://www.gobiernodecanarias.org/boc/{year}/{numero}/{anuncio}.html"
        return url_html
    
    return None

def buscar_decreto_autonomicos(year: int) -> Optional[str]:
    """
    Busca el Decreto de festivos autonómicos en el BOC
    Publicado típicamente en septiembre del año anterior
    
    Args:
        year: Año objetivo (ej: 2025)
        
    Returns:
        URL del decreto o None
    """
    
    year_publicacion = year - 1
    
    print(f"🔍 Buscando Decreto autonómicos Canarias {year}...")
    print(f"   📅 Publicación esperada: septiembre {year_publicacion}")
    
    # Palabras clave a buscar
    palabras_clave = ['fiestas', 'laborales', str(year)]
    
    # Buscar en septiembre-octubre (BOC 50-250)
    url = buscar_en_boc(year_publicacion, 50, 250, palabras_clave, 'decreto')
    
    if url:
        return url
    
    print(f"   ❌ No encontrado en BOC {year_publicacion}")
    return None


def buscar_orden_locales(year: int) -> Optional[str]:
    """
    Busca la Orden de festivos locales en el BOC
    Publicado típicamente en noviembre-diciembre del año anterior
    
    Args:
        year: Año objetivo (ej: 2025)
        
    Returns:
        URL de la orden o None
    """
    
    year_publicacion = year - 1
    
    print(f"🔍 Buscando Orden locales Canarias {year}...")
    print(f"   📅 Publicación esperada: noviembre-diciembre {year_publicacion}")
    
    # Palabras clave
    palabras_clave = ['fiestas', 'locales', str(year)]
    
    # Buscar en noviembre-diciembre (BOC 130-280)
    url = buscar_en_boc(year_publicacion, 130, 280, palabras_clave, 'orden')
    
    if url:
        return url
    
    print(f"   ❌ No encontrado en BOC {year_publicacion}")
    return None


def auto_discover_canarias(year: int) -> Dict[str, Optional[str]]:
    """
    Descubre automáticamente las URLs para Canarias
    
    Returns:
        Dict con 'autonomicos' y 'locales' URLs
    """
    
    print("=" * 80)
    print(f"🔎 AUTO-DISCOVERY BOC CANARIAS {year}")
    print("=" * 80)
    
    urls = {
        'autonomicos': buscar_decreto_autonomicos(year),
        'locales': buscar_orden_locales(year)
    }
    
    print("=" * 80)
    print("📋 RESULTADOS:")
    print(f"   Autonómicos: {urls['autonomicos'] or 'NO ENCONTRADO'}")
    print(f"   Locales: {urls['locales'] or 'NO ENCONTRADO'}")
    print("=" * 80)
    
    return urls


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    
    urls = auto_discover_canarias(year)