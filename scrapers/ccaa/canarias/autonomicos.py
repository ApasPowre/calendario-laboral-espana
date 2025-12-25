"""
Canarias Autonómicos Scraper
Extrae festivos autonómicos e insulares desde el Decreto del BOC
"""

from typing import List, Dict
import re
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper
import json
import os
import html


class CanariasAutonomicosScraper(BaseScraper):
    """Scraper para festivos autonómicos de Canarias"""
    
    # URLs conocidas (añadir más según se descubran)
    KNOWN_URLS = {
        2025: "https://www.gobiernodecanarias.org/boc/2024/187/3013.html",
    }
    
    CACHE_FILE = "config/canarias_urls_cache.json"
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='canarias', tipo='autonomicos')
        self.municipio = municipio
        self.municipios_islas = self._load_municipios_islas()  # ← Esta línea
        self._load_cache()

    def _load_cache(self):
        """Carga URLs del cache"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    self.cached_urls = cache.get('autonomicos', {})
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs autonómicas")
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
            cache['autonomicos'][str(year)] = url
            
            # Guardar
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            
            print(f"💾 URL guardada en cache: {year} → {url}")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar en cache: {e}")
    
    def _load_municipios_islas(self) -> Dict[str, List[str]]:
        """Carga mapping de municipios a islas desde configuración o hardcoded"""
        return {
            'Tenerife': [
                'ADEJE', 'ARAFO', 'ARICO', 'ARONA', 'BUENAVISTA DEL NORTE',
                'CANDELARIA', 'FASNIA', 'GARACHICO', 'GRANADILLA DE ABONA',
                'GUÍA DE ISORA', 'GÜÍMAR', 'ICOD DE LOS VINOS', 'LA GUANCHA',
                'LA MATANZA DE ACENTEJO', 'LA OROTAVA', 'LA VICTORIA DE ACENTEJO',
                'LOS REALEJOS', 'LOS SILOS', 'PUERTO DE LA CRUZ', 'EL ROSARIO',
                'SAN CRISTÓBAL DE LA LAGUNA', 'SAN JUAN DE LA RAMBLA',
                'SAN MIGUEL DE ABONA', 'SANTA CRUZ DE TENERIFE', 'SANTA ÚRSULA',
                'SANTIAGO DEL TEIDE', 'EL SAUZAL', 'TACORONTE', 'EL TANQUE',
                'TEGUESTE', 'VILAFLOR DE CHASNA'
            ],
            'La Palma': [
                'BARLOVENTO', 'BREÑA ALTA', 'BREÑA BAJA', 'FUENCALIENTE DE LA PALMA',
                'GARAFÍA', 'LOS LLANOS DE ARIDANE', 'EL PASO', 'PUNTAGORDA',
                'PUNTALLANA', 'SAN ANDRÉS Y SAUCES', 'SANTA CRUZ DE LA PALMA',
                'TAZACORTE', 'TIJARAFE', 'VILLA DE MAZO'
            ],
            'La Gomera': [
                'AGULO', 'ALAJERÓ', 'HERMIGUA', 'SAN SEBASTIÁN DE LA GOMERA',
                'VALLE GRAN REY', 'VALLEHERMOSO'
            ],
            'El Hierro': [
                'LA FRONTERA', 'EL PINAR DE EL HIERRO', 'VALVERDE'
            ],
            'Gran Canaria': [
                'AGAETE', 'AGÜIMES', 'ARTENARA', 'ARUCAS', 'FIRGAS', 'GÁLDAR',
                'INGENIO', 'LA ALDEA DE SAN NICOLÁS', 'LAS PALMAS DE GRAN CANARIA',
                'MOGÁN', 'MOYA', 'SAN BARTOLOMÉ DE TIRAJANA', 'SANTA BRÍGIDA',
                'SANTA LUCÍA', 'SANTA MARÍA DE GUÍA', 'TELDE', 'TEJEDA', 'TEROR',
                'VALLESECO', 'VALSEQUILLO', 'VEGA DE SAN MATEO'
            ],
            'Lanzarote': [
                'ARRECIFE', 'HARÍA', 'SAN BARTOLOMÉ DE LANZAROTE', 'TEGUISE',
                'TÍAS', 'TINAJO', 'YAIZA'
            ],
            'La Graciosa': [],
            'Fuerteventura': [
                'ANTIGUA', 'BETANCURIA', 'LA OLIVA', 'PÁJARA', 
                'PUERTO DEL ROSARIO', 'TUINEJE'
            ]
        }
    
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
    
    def get_isla_municipio(self, municipio: str) -> str:
        """Devuelve la isla a la que pertenece un municipio"""
        for isla, municipios in self.municipios_islas.items():
            if municipio in municipios:
                return isla
        return None
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea el Decreto del BOC y extrae festivos autonómicos e insulares
        """
        # Decodificar HTML entities
        content = html.unescape(content)
        
        soup = BeautifulSoup(content, 'lxml')
        festivos = []
        
        # Extraer texto completo
        texto = soup.get_text()
        
        # NORMALIZAR: eliminar \xa0, Â y otros caracteres raros
        texto = texto.replace('\xa0', ' ')  # Espacio no-rompible
        texto = texto.replace('Â', '')      # Caracter extraño
        texto = re.sub(r'\s+', ' ', texto)  # Múltiples espacios → uno solo
        
        print(f"   🔍 Buscando festivos en texto normalizado...")
        
        # 1. Buscar Día de Canarias (30 de mayo)
        if '30 de mayo' in texto.lower() or '30 mayo' in texto.lower():
            print(f"   ✅ Encontrado Día de Canarias")
            festivos.append({
                'fecha': f'{self.year}-05-30',
                'fecha_texto': '30 de mayo',
                'descripcion': 'Día de Canarias',
                'tipo': 'autonomico',
                'ambito': 'autonomico',
                'ccaa': 'Canarias',
                'islas': 'Todas',
                'municipios_aplicables': 'Todos',
                'year': self.year
            })
        
        # 2. Buscar festivos insulares
        # Patrón flexible para manejar variaciones
        patron_insular = r'En\s+([^:]+?):\s+el\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre),\s+festividad\s+de\s+(.+?)(?:\.|(?=\s+En\s+)|$)'
        
        matches = list(re.finditer(patron_insular, texto, re.IGNORECASE | re.DOTALL))
        print(f"   🔍 Matches insulares encontrados: {len(matches)}")
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        for match in matches:
            isla = match.group(1).strip()
            dia = int(match.group(2))
            mes_texto = match.group(3).lower()
            descripcion_virgen = match.group(4).strip()
            
            # Limpiar descripción
            descripcion_virgen = descripcion_virgen.split('\n')[0].strip()
            
            print(f"   ✅ {isla}: {dia} de {mes_texto} - {descripcion_virgen}")
            
            # Normalizar isla
            isla_normalizada = self._normalizar_isla(isla)
            
            mes = meses.get(mes_texto)
            if mes:
                fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
                fecha_texto_completo = f"{dia} de {mes_texto}"
                
                festivos.append({
                    'fecha': fecha_iso,
                    'fecha_texto': fecha_texto_completo,
                    'descripcion': f'Festividad de {descripcion_virgen}',
                    'tipo': 'autonomico',
                    'ambito': 'insular',
                    'ccaa': 'Canarias',
                    'islas': isla_normalizada,
                    'municipios_aplicables': [isla_normalizada] if '/' not in isla_normalizada else isla_normalizada.split('/'),
                    'year': self.year
                })
        
        if festivos:
            print(f"   ✅ Total festivos extraídos: {len(festivos)}")
        
        # Filtrar festivos insulares si se especificó municipio
        if self.municipio:
            isla_municipio = self.get_isla_municipio(self.municipio.upper())
            
            if isla_municipio:
                print(f"   🏝️  Filtrando festivos para isla: {isla_municipio}")
                festivos_filtrados = []
                
                for fest in festivos:
                    # Mantener festivos de toda Canarias
                    if fest.get('ambito') == 'autonomico':
                        festivos_filtrados.append(fest)
                    # Mantener festivos de la isla del municipio
                    elif fest.get('ambito') == 'insular':
                        municipios_aplicables = fest.get('municipios_aplicables', [])
                        if isinstance(municipios_aplicables, str):
                            municipios_aplicables = [municipios_aplicables]
                        
                        if isla_municipio in municipios_aplicables:
                            festivos_filtrados.append(fest)
                
                festivos = festivos_filtrados
                print(f"   ✅ Festivos tras filtrar por isla: {len(festivos)}")
        
        return festivos
    
    def _normalizar_isla(self, isla: str) -> str:
        """Normaliza nombres de islas"""
        if 'Hierro' in isla:
            return 'El Hierro'
        elif 'Palma' in isla and 'Gran' not in isla:
            return 'La Palma'
        elif 'Gomera' in isla:
            return 'La Gomera'
        elif 'Tenerife' in isla:
            return 'Tenerife'
        elif 'Gran Canaria' in isla:
            return 'Gran Canaria'
        elif 'Lanzarote' in isla or 'Graciosa' in isla:
            return 'Lanzarote/La Graciosa'
        elif 'Fuerteventura' in isla:
            return 'Fuerteventura'
        return isla

def main():
    """Test del scraper"""
    import sys
    
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("❌ Año inválido. Uso: python -m scrapers.ccaa.canarias.autonomicos [año]")
            return
    else:
        year = 2025  # Por defecto
    
    print("=" * 80)
    print(f"🧪 TEST: Canarias Autonómicos Scraper - Festivos {year}")
    print("=" * 80)
    
    scraper = CanariasAutonomicosScraper(year=year)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json(f'data/canarias_autonomicos_{year}.json')
        scraper.save_to_excel(f'data/canarias_autonomicos_{year}.xlsx')
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()