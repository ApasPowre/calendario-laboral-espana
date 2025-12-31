"""
Madrid Autonómicos Scraper - Festivos de ámbito autonómico
Extrae festivos desde el BOCM (Boletín Oficial de la Comunidad de Madrid)
"""

from typing import List, Dict
import re
from scrapers.core.base_scraper import BaseScraper


class MadridAutonomicosScraper(BaseScraper):
    """
    Scraper para festivos autonómicos de Madrid desde el BOCM
    
    Fuente: Decreto del Consejo de Gobierno
    Publicación: Septiembre del año anterior
    """
    
    # URLs conocidas de decretos de festivos autonómicos
    KNOWN_URLS = {
        2026: "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/09/25/BOCM-20250925-16.PDF",
    }
    CACHE_FILE = "config/madrid_urls_cache.json"
    
    def __init__(self, year: int):
        super().__init__(year=year, ccaa='madrid', tipo='autonomicos')
        self._load_cache()
    
    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json
        
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
        import os
        import json
        
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

    def get_source_url(self) -> str:
        """Devuelve URL del BOCM (con sistema de cache)"""
        year_str = str(self.year)
        
        # 1. KNOWN_URLS (oficial)
        if self.year in self.KNOWN_URLS:
            url = self.KNOWN_URLS[self.year]
            print(f"✅ URL oficial (KNOWN_URLS) para {self.year}: {url}")
            return url
        
        # 2. Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url
        
        # 3. Si no existe, dar instrucciones
        raise ValueError(
            f"\n❌ No se encontró URL para {self.year}.\n\n"
            f"Para añadirla:\n"
            f"1. Busca en https://www.bocm.es 'fiestas laborales {self.year}'\n"
            f"2. Encuentra el Decreto (publicado en sept {self.year-1})\n"
            f"3. Ejecuta este scraper pasando la URL:\n"
            f"   python -m scrapers.ccaa.madrid.autonomicos {self.year} --url=URL_AQUI\n"
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos autonómicos desde el contenido del BOCM.
        Lee las fechas REALES del texto (incluyendo traslados)
        """
        print("🔍 Parseando festivos autonómicos de Madrid...")
        
        festivos = []
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Parsear línea por línea buscando patrón: "DD de MMMM (día), Descripción"
        # Ejemplo: "2 de noviembre (lunes), traslado de Todos los Santos."
        patron = r'—?\s*(\d{1,2})de(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?:\([^)]+\))?,(.+?)\.'
        
        lineas = content.split('\n')
        
        for linea in lineas:
            linea_lower = linea.lower().strip()
            
            match = re.search(patron, linea_lower)
            
            if match:
                dia = int(match.group(1))
                mes_texto = match.group(2)
                descripcion_raw = match.group(3).strip()

                # Diccionario de correcciones conocidas (texto sin espacios → texto correcto)
                correcciones = {
                    'añonuevo': 'Año Nuevo',
                    'epifaníadelseñor': 'Epifanía del Señor',
                    'juevessanto': 'Jueves Santo',
                    'viernessanto': 'Viernes Santo',
                    'fiestadeltrabajo': 'Fiesta del Trabajo',
                    'fiestadelacomunidaddemadrid': 'Fiesta de la Comunidad de Madrid',
                    'asuncióndelavirgen': 'Asunción de la Virgen',
                    'fiestanacionaldeespaña': 'Fiesta Nacional de España',
                    'trasladodetodoslossantos': 'Día siguiente a Todos los Santos',
                    'trasladodeldíadelaConstituciónespañola': 'Lunes siguiente al Día de la Constitución Española',
                    'trasladodeldíadelaconstituciónespañola': 'Lunes siguiente al Día de la Constitución Española',
                    'díadelainmaculadaconcepción': 'Inmaculada Concepción',
                    'natividaddelseñor': 'Natividad del Señor'
                }

                descripcion_lower = descripcion_raw.lower()
                descripcion = correcciones.get(descripcion_lower, descripcion_raw.title())
                
                mes = meses[mes_texto]
                fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
                fecha_texto_completo = f"{dia} de {mes_texto}"
                
                festivos.append({
                    'fecha': fecha_iso,
                    'fecha_texto': fecha_texto_completo,
                    'descripcion': descripcion,
                    'tipo': 'autonomico',
                    'ambito': 'Madrid',
                    'sustituible': False,
                    'year': self.year
                })
        
        print(f"   ✅ Extraídos {len(festivos)} festivos autonómicos de Madrid")
        
        return festivos


def main():
    """Test del scraper"""
    import sys
    
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("❌ Año inválido. Uso: python -m scrapers.ccaa.madrid.autonomicos [año]")
            return
    else:
        year = 2026
    
    print("=" * 80)
    print(f"🧪 TEST: Madrid Autonómicos Scraper - Festivos {year}")
    print("=" * 80)
    
    scraper = MadridAutonomicosScraper(year=year)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json(f"data/madrid_autonomicos_{year}.json")
        scraper.save_to_excel(f"data/madrid_autonomicos_{year}.xlsx")
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()