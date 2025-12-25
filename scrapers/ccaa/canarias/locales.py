"""
Canarias Locales Scraper
Extrae festivos locales por municipio desde la Orden del BOC
"""

from typing import List, Dict
import re
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper
import json
import os


class CanariasLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Canarias
    Extrae desde la Orden publicada en el BOC (2 festivos por municipio)
    """

    CACHE_FILE = "config/canarias_urls_cache.json"

    KNOWN_URLS = {
        2025: "https://www.gobiernodecanarias.org/boc/2024/238/3948.html",
    }

    def __init__(self, year: int, municipio: str = None):
        super().__init__(year=year, ccaa='canarias', tipo='locales')
        self.municipio = municipio
        self._load_cache()
    
    def _load_cache(self):
        """Carga URLs del cache"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    self.cached_urls = cache.get('locales', {})
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs locales")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}
    
    def _save_to_cache(self, year: int, url: str):
        """Guarda URL en el cache"""
        try:
            # Cargar cache completo
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            else:
                cache = {"autonomicos": {}, "locales": {}}
            
            # Actualizar
            cache['locales'][str(year)] = url
            
            # Guardar
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            
            print(f"💾 URL guardada en cache: {year} → {url}")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar en cache: {e}")
    
    def get_source_url(self) -> str:
        """Devuelve URL del BOC (con sistema de cache)"""
        year_str = str(self.year)
        
        # 1. KNOWN_URLS (oficial)
        if self.year in self.KNOWN_URLS:
            url = self.KNOWN_URLS[self.year]
            print(f"✅ URL oficial (KNOWN_URLS) para {self.year}")
            return url
        
        # 2. Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url
        
        # 3. Si no existe, dar instrucciones
        raise ValueError(
            f"\n❌ No se encontró URL para {self.year}.\n\n"
            f"Busca manualmente en https://www.gobiernodecanarias.org/boc/\n"
            f"y añade la URL al archivo {self.CACHE_FILE}\n"
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea la Orden del BOC y extrae festivos locales por municipio.
        Cada municipio tiene exactamente 2 festivos locales.
        """
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
        # Extraer texto y normalizar encoding
        import html as html_lib
        import unicodedata
        
        content = html_lib.unescape(content)
        soup = BeautifulSoup(content, 'lxml')
        texto = soup.get_text()
        
        # Normalizar Unicode: eliminar caracteres de control y normalizar
        texto = ''.join(char for char in texto if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        lineas = texto.split('\n')
        
        municipio_actual = None
        festivos_municipio = []
        
        for linea in lineas:
            linea = linea.strip()
            
            if not linea:
                continue
            
            # Detectar municipio: empieza con mayúscula, solo letras/espacios, termina en punto
            if linea and linea[-1] == '.' and linea[:-1].replace(' ', '').isalpha() and linea[0].isupper():
                # Guardar festivos del municipio anterior (con filtro)
                if municipio_actual and festivos_municipio:
                    # Aplicar filtro de municipio si existe
                    if self.municipio is None or self._normalizar_municipio(municipio_actual) == self._normalizar_municipio(self.municipio):
                        for fest in festivos_municipio:
                            festivos.append(fest)
                
                # Nuevo municipio
                municipio_actual = linea.rstrip('.').strip()
                festivos_municipio = []
                continue
            
            # Detectar festivo (formato: "DD mes: Descripción" o "DD de mes: Descripción")
            if municipio_actual:
                match_festivo = re.match(r'(\d+\s+(?:de\s+)?\w+):\s*(.+)', linea)
                
                if match_festivo:
                    fecha_texto = match_festivo.group(1)
                    descripcion = match_festivo.group(2).strip()
                    
                    fecha_info = self.parse_fecha_espanol(fecha_texto)
                    
                    if fecha_info:
                        # Verificar que no exista ya este festivo para este municipio
                        fecha_existe = any(
                            f['fecha'] == fecha_info['fecha'] and f['municipio'] == municipio_actual
                            for f in festivos_municipio
                        )
                        
                        if not fecha_existe:
                            provincia = self._detectar_provincia(municipio_actual)
                            
                            festivo = {
                                'municipio': municipio_actual,
                                'fecha': fecha_info['fecha'],
                                'fecha_texto': fecha_info['fecha_texto'],
                                'descripcion': descripcion,
                                'tipo': 'local',
                                'ambito': 'municipal',
                                'ccaa': 'Canarias',
                                'provincia': provincia,
                                'year': self.year
                            }
                            festivos_municipio.append(festivo)
        
        # Guardar festivos del último municipio (con filtro)
        if municipio_actual and festivos_municipio:
            if self.municipio is None or self._normalizar_municipio(municipio_actual) == self._normalizar_municipio(self.municipio):
                for fest in festivos_municipio:
                    festivos.append(fest)
        
        return festivos
    
    def _normalizar_municipio(self, municipio: str) -> str:
        """Normaliza nombre de municipio para comparación exacta"""
        import unicodedata
        # Quitar acentos
        municipio = ''.join(
            c for c in unicodedata.normalize('NFD', municipio)
            if unicodedata.category(c) != 'Mn'
        )
        # Lowercase, sin espacios extra, sin puntos
        municipio = municipio.lower().strip().rstrip('.')
        # Normalizar espacios múltiples
        municipio = ' '.join(municipio.split())
        return municipio
    
    def _detectar_provincia(self, municipio: str) -> str:
        """
        Detecta la provincia basándose en el municipio.
        Usa configuración YAML si está disponible.
        """
        # Municipios de Las Palmas
        municipios_las_palmas = [
            'AGAETE', 'AGÜIMES', 'ANTIGUA', 'ARRECIFE', 'ARTENARA', 'ARUCAS',
            'BETANCURIA', 'FIRGAS', 'GÁLDAR', 'HARÍA', 'INGENIO',
            'LA ALDEA DE SAN NICOLÁS', 'LA OLIVA', 'LAS PALMAS DE GRAN CANARIA',
            'MOGÁN', 'MOYA', 'PÁJARA', 'PUERTO DEL ROSARIO',
            'SAN BARTOLOMÉ DE LANZAROTE', 'SAN BARTOLOMÉ DE TIRAJANA',
            'SANTA BRÍGIDA', 'SANTA LUCÍA', 'SANTA MARÍA DE GUÍA', 'TEGUISE',
            'TEJEDA', 'TELDE', 'TEROR', 'TÍAS', 'TINAJO', 'TUINEJE',
            'VALLESECO', 'VALSEQUILLO', 'VEGA DE SAN MATEO', 'YAIZA'
        ]
        
        if municipio in municipios_las_palmas:
            return 'Las Palmas'
        else:
            return 'Santa Cruz de Tenerife'


def main():
    """Test del scraper"""
    import sys
    
    year = 2025
    municipio = None
    
    # Argumentos: python -m scrapers.ccaa.canarias.locales [municipio] [año]
    # O: python -m scrapers.ccaa.canarias.locales [año] [municipio]
    
    if len(sys.argv) > 1:
        # Primer argumento
        try:
            year = int(sys.argv[1])
        except ValueError:
            # No es un año, es un municipio
            municipio = sys.argv[1]
    
    if len(sys.argv) > 2:
        # Segundo argumento
        try:
            year = int(sys.argv[2])
        except ValueError:
            # No es un año, es un municipio
            if municipio is None:
                municipio = sys.argv[2]
    
    print("=" * 80)
    if municipio:
        print(f"🧪 TEST: Canarias Locales - {municipio} {year}")
    else:
        print(f"🧪 TEST: Canarias Locales - Todos los municipios {year}")
    print("=" * 80)
    
    scraper = CanariasLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        
        if municipio:
            filename = f"data/canarias_{municipio.lower().replace(' ', '_')}_{year}"
        else:
            filename = f"data/canarias_locales_{year}"
        
        scraper.save_to_json(f"{filename}.json")
        scraper.save_to_excel(f"{filename}.xlsx")
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()