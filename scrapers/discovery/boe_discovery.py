"""
BOE Auto-Discovery usando la API oficial de datos abiertos
Sistema de cache automático para URLs descubiertas
"""

import requests
from typing import Optional
import json
import os
import re


class BOEAutoDiscovery:
    """
    Sistema de descubrimiento de URLs del BOE
    Guarda automáticamente URLs descubiertas en cache JSON
    """
    
    # URLs conocidas hardcoded (base de datos oficial)
    KNOWN_URLS = {
        2026: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667",
        2025: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-21234",
        2024: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-22014",
        # Las URLs descubiertas dinámicamente se guardan en config/boe_urls_cache.json
    }
    
    CACHE_FILE = "config/boe_urls_cache.json"
    
    def __init__(self):
        self.base_url = "https://www.boe.es"
        self.api_url = f"{self.base_url}/datosabiertos/api"
        self._load_cache()
    
    def _load_cache(self):
        """Carga URLs descubiertas previamente desde el cache JSON"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs descubiertas previamente")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}
    
    def _save_to_cache(self, year: int, url: str):
        """Guarda una URL recién descubierta en el cache"""
        try:
            # Actualizar cache en memoria
            self.cached_urls[str(year)] = url
            
            # Asegurar que existe el directorio
            os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
            
            # Guardar a disco
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cached_urls, f, ensure_ascii=False, indent=2)
            
            print(f"💾 URL guardada en cache: {year} → {url}")
            print(f"💡 Próximas ejecuciones usarán el cache (instantáneo)")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar en cache: {e}")
    
    def get_url(self, year: int, try_auto_discovery: bool = True) -> str:
        """
        Obtiene la URL de la Resolución de festivos.
        
        Orden de búsqueda:
        1. KNOWN_URLS (hardcoded, oficial)
        2. Cache JSON (URLs descubiertas previamente)
        3. Auto-discovery (API del BOE)
        """
        year_str = str(year)
        
        # 1. Primero, intentar KNOWN_URLS (oficial)
        if year in self.KNOWN_URLS:
            url = self.KNOWN_URLS[year]
            print(f"✅ URL oficial (KNOWN_URLS) para {year}: {url}")
            
            if self.validate_url(url, year):
                return url
            else:
                print(f"⚠️  URL oficial no válida, buscando alternativa...")
        
        # 2. Segundo, intentar cache de URLs descubiertas
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache (descubierta previamente) para {year}: {url}")
            
            if self.validate_url(url, year):
                return url
            else:
                print(f"⚠️  URL en cache no válida, re-descubriendo...")
        
        # 3. Tercero, intentar auto-discovery
        if try_auto_discovery:
            print(f"🔍 Auto-discovery para {year} (no está en cache)...")
            url = self._try_auto_discovery(year)
            
            if url and self.validate_url(url, year):
                print(f"✅ URL encontrada por auto-discovery: {url}")
                
                # Guardar en cache para futuras ejecuciones
                self._save_to_cache(year, url)
                
                return url
        
        # 4. Si todo falla, dar instrucciones
        raise ValueError(
            f"\n❌ No se encontró URL para {year}.\n\n"
            f"Para añadirla manualmente:\n"
            f"1. Busca en https://www.boe.es 'fiestas laborales {year}'\n"
            f"2. Encuentra la Resolución (suele publicarse en oct-nov {year-1})\n"
            f"3. Añade a {self.CACHE_FILE}:\n"
            f'   "{year}": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-{year-1}-XXXXX"\n'
        )
    
    def _try_auto_discovery(self, year: int) -> Optional[str]:
        """
        Intenta auto-discovery usando la API del BOE (paralelizado)
        Busca en TODOS los días de septiembre-diciembre del año anterior
        """
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            search_year = year - 1
            
            print(f"   🔍 Buscando en API del BOE (sept-dic {search_year}) con paralelismo...")
            print(f"   ⏱️  Búsqueda paralelizada activada...")
            
            # Función worker para buscar un día específico
            def buscar_dia(fecha_tuple):
                year_search, mes, dia = fecha_tuple
                fecha = f"{year_search}{mes:02d}{dia:02d}"
                api_url = f"{self.api_url}/boe/sumario/{fecha}"
                
                try:
                    response = requests.get(api_url, timeout=5, headers={'Accept': 'application/json'})
                    if response.status_code != 200:
                        return None
                    
                    data = response.json()
                    doc_id = self._search_in_json(data, year)
                    
                    if doc_id:
                        return (fecha, f"{self.base_url}/diario_boe/txt.php?id={doc_id}")
                    
                    return None
                except:
                    return None
            
            # Buscar en TODOS los días de septiembre a diciembre (paralelizado)
            for mes in [9, 10, 11, 12]:  # Sept, Oct, Nov, Dic
                # Determinar días del mes
                if mes == 2:
                    max_day = 29 if search_year % 4 == 0 else 28
                elif mes in [4, 6, 9, 11]:
                    max_day = 30
                else:
                    max_day = 31
                
                print(f"   → Buscando en {search_year}/{mes:02d} ({max_day} días en paralelo)...", end=" ", flush=True)
                
                # Crear lista de días a buscar (de más reciente a más antiguo)
                dias_buscar = [(search_year, mes, dia) for dia in range(max_day, 0, -1)]
                
                # Buscar todos los días del mes en paralelo
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(buscar_dia, dia_tuple): dia_tuple for dia_tuple in dias_buscar}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            fecha, url = result
                            print(f"✅ (encontrado en {fecha})")
                            return url
                
                print("❌")
            
            print(f"   ❌ No encontrado en sept-dic {search_year}")
            
            # Fallback: enero-febrero del año objetivo (publicación muy tardía)
            print(f"   🔄 Intentando en enero-febrero {year} (publicación tardía)...")
            
            for mes in [1, 2]:
                max_day = 29 if mes == 2 and year % 4 == 0 else (28 if mes == 2 else 31)
                
                print(f"   → Buscando en {year}/{mes:02d} ({max_day} días en paralelo)...", end=" ", flush=True)
                
                dias_buscar = [(year, mes, dia) for dia in range(max_day, 0, -1)]
                
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(buscar_dia, dia_tuple): dia_tuple for dia_tuple in dias_buscar}
                    
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            fecha, url = result
                            print(f"✅ (encontrado en {fecha})")
                            return url
                
                print("❌")
            
            return None
        
        except Exception as e:
            print(f"   ⚠️  Error en auto-discovery: {e}")
            return None
    
    def _search_in_json(self, data: dict, year: int) -> Optional[str]:
        """
        Busca el documento en el JSON del sumario iterando el diccionario nativo.
        Mucho más eficiente que convertir a string y usar regex.
        """
        def buscar_recursivo(obj, year_str):
            """Busca recursivamente en el objeto JSON"""
            # Si es un diccionario
            if isinstance(obj, dict):
                # Verificar si este objeto tiene identificador y título
                identificador = obj.get('identificador', '').upper()
                titulo = obj.get('titulo', '').lower()
                
                # Verificar patrón BOE-A-YYYY-XXXXX
                if identificador.startswith('BOE-A-'):
                    # Verificar que el título contenga "fiestas laborales" y el año
                    if 'fiestas laborales' in titulo and year_str in titulo:
                        # Verificar tipo de documento (resolución o relación)
                        if 'resolución' in titulo or 'relación' in titulo:
                            return identificador
                
                # Buscar recursivamente en todos los valores
                for value in obj.values():
                    result = buscar_recursivo(value, year_str)
                    if result:
                        return result
            
            # Si es una lista, buscar en cada elemento
            elif isinstance(obj, list):
                for item in obj:
                    result = buscar_recursivo(item, year_str)
                    if result:
                        return result
            
            return None
        
        try:
            year_str = str(year)
            return buscar_recursivo(data, year_str)
        except Exception:
            return None
    
    def validate_url(self, url: str, year: int) -> bool:
        """Valida que una URL contiene la Resolución de festivos"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Verificar palabras clave
            required = ['fiestas laborales', str(year), 'año nuevo']
            
            return all(kw in content for kw in required)
            
        except:
            return False


def main():
    """Test del auto-discovery con cache"""
    discovery = BOEAutoDiscovery()
    
    # Probar con 2026
    url_2026 = discovery.get_url(2026)
    print(f"\n{'='*80}")
    print(f"📄 URL final para 2026: {url_2026}")


if __name__ == "__main__":
    main()