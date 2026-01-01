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
from scrapers.discovery.ccaa.canarias_discovery import auto_discover_canarias

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
        # Inicializar cache vacío por defecto
        self.cache = {'autonomicos': {}, 'locales': {}}
        
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"📦 Cache cargado: {len(self.cache.get('autonomicos', {}))} URLs autonómicas")
            except Exception as e:
                print(f"⚠️  Error cargando cache: {e}")
                self.cache = {'autonomicos': {}, 'locales': {}}
        else:
            print(f"📦 Cache vacío (archivo no existe)")
    
    def _save_to_cache(self, tipo: str, year: int, url: str):
        """
        Guarda URL en el cache
        
        Args:
            tipo: 'autonomicos' o 'locales'
            year: Año
            url: URL a guardar
        """
        try:
            # Cargar cache completo
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            else:
                cache = {"autonomicos": {}, "locales": {}}
            
            # Asegurar que exista la clave del tipo
            if tipo not in cache:
                cache[tipo] = {}
            
            # Actualizar
            cache[tipo][str(year)] = url
            
            # Guardar
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando en cache: {e}")
    
    def get_source_url(self) -> str:
        """
        Obtiene URL de la fuente con 3 niveles:
        1. KNOWN_URLS (oficial)
        2. Cache (descubierto previamente)
        3. Auto-discovery (buscar en BOC)
        """
        
        # Nivel 1: KNOWN_URLS
        if self.year in self.KNOWN_URLS:
            print(f"✅ URL oficial (KNOWN_URLS) para {self.year}")
            return self.KNOWN_URLS[self.year]
        
        # Nivel 2: Cache
        if str(self.year) in self.cache.get('locales', {}):
            url = self.cache['locales'][str(self.year)]
            print(f"📦 URL en cache (descubierta previamente) para {self.year}: {url}")
            return url
        
        # Nivel 3: Auto-discovery
        print(f"🔍 Auto-discovery para {self.year} (no está en cache ni KNOWN_URLS)...")
        print(f"   ⏱️  Esto puede tardar 1-2 minutos...")
        
        urls = auto_discover_canarias(self.year)
        url_locales = urls.get('locales')
        
        if url_locales:
            print(f"✅ URL encontrada por auto-discovery: {url_locales}")
            self._save_to_cache('locales', self.year, url_locales)
            print(f"💾 URL guardada en cache")
            print(f"💡 Próximas ejecuciones usarán el cache (instantáneo)")
            return url_locales
        
        # Error: no encontrada
        raise ValueError(
            f"❌ No se pudo encontrar URL para festivos locales Canarias {self.year}\n"
            f"   Búsqueda realizada en:\n"
            f"   1. KNOWN_URLS ❌\n"
            f"   2. Cache ❌\n"
            f"   3. Auto-discovery BOC ❌\n"
            f"\n"
            f"   Solución: Añade manualmente la URL en KNOWN_URLS o cache."
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea la Orden del BOC y extrae festivos locales por municipio.
        Cada municipio tiene exactamente 2 festivos locales.
        """
        import html as html_lib
        import unicodedata
        
        # CRITICAL: Fix encoding BEFORE BeautifulSoup processes it
        content = content.replace('Ã\x93', 'Ó')
        content = content.replace('Ã\x81', 'Á')
        content = content.replace('Ã\x89', 'É')
        content = content.replace('Ã\x8D', 'Í')
        content = content.replace('Ã\x9A', 'Ú')
        content = content.replace('Ã\x91', 'Ñ')
        content = content.replace('Ã\x9C', 'Ü')
        
        def normalizar_para_comparar(texto):
            """Normaliza texto corrigiendo encoding corrupto del BOC"""
            # SECOND: Normalize Unicode (remove accents)
            texto = unicodedata.normalize('NFKD', texto)
            texto = texto.encode('ASCII', 'ignore').decode('ASCII')
            
            # THIRD: Clean spaces and uppercase
            return texto.upper().strip().replace(' ', '')
        
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
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
            
            # Detectar municipio: termina en punto, mayúsculas, principalmente letras
            if linea and linea[-1] == '.' and linea[0].isupper():
                nombre = linea.rstrip('.')
                # Verificar que sea principalmente letras (permitir tildes, espacios)
                letras = sum(c.isalpha() or c in 'ÁÉÍÓÚÑ' for c in nombre)
                if letras >= len(nombre) * 0.8:  # Al menos 80% letras
                    # Guardar festivos del municipio anterior (con filtro)
                    if municipio_actual and festivos_municipio:
                        # Aplicar filtro de municipio si existe (con normalización flexible)
                        debe_incluir = False
                        
                        if self.municipio is None:
                            debe_incluir = True
                        else:
                            mun_buscado = normalizar_para_comparar(self.municipio)
                            mun_encontrado = normalizar_para_comparar(municipio_actual)
                            
                            print(f"      🔍 Comparando: '{mun_buscado}' vs '{mun_encontrado}' → {mun_buscado == mun_encontrado}")
                            
                            # Coincidencia exacta o parcial
                            if mun_buscado == mun_encontrado:
                                debe_incluir = True
                            elif mun_buscado in mun_encontrado or mun_encontrado in mun_buscado:
                                debe_incluir = True
                        
                        if debe_incluir:
                            for fest in festivos_municipio:
                                festivos.append(fest)
                    
                    # Nuevo municipio
                    municipio_actual = nombre
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
                            
                            # Limpiar encoding corrupto del BOC
                            descripcion = descripcion.replace('Ã±', 'ñ')  # ñ
                            descripcion = descripcion.replace('Ã\x91', 'Ñ')  # Ñ (formato hex)
                            descripcion = descripcion.replace('Ã³', 'ó')  # ó
                            descripcion = descripcion.replace('Ã­', 'í')  # í
                            descripcion = descripcion.replace('Ã¡', 'á')  # á
                            descripcion = descripcion.replace('Ã©', 'é')  # é
                            descripcion = descripcion.replace('Ãº', 'ú')  # ú
                            descripcion = descripcion.replace('Ã¼', 'ü')  # ü
                            descripcion = descripcion.replace('Ã\x9c', 'Ü')  # Ü (formato hex)
                            descripcion = descripcion.replace('Ãsimo', 'ísimo')
                            descripcion = descripcion.replace('Ãrsula', 'Úrsula')

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
            # Aplicar filtro de municipio si existe (con normalización flexible)
            debe_incluir = False
            
            if self.municipio is None:
                debe_incluir = True
            else:
                mun_buscado = normalizar_para_comparar(self.municipio)
                mun_encontrado = normalizar_para_comparar(municipio_actual)
                                
                # Coincidencia exacta o parcial
                if mun_buscado == mun_encontrado:
                    debe_incluir = True
                elif mun_buscado in mun_encontrado or mun_encontrado in mun_buscado:
                    debe_incluir = True
            
            if debe_incluir:
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