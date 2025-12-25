"""
Madrid Locales Scraper - Festivos de ámbito local
Extrae festivos locales de los 179 municipios de Madrid desde el BOCM
"""

from typing import List, Dict, Optional
import re
from scrapers.core.base_scraper import BaseScraper


class MadridLocalesScraper(BaseScraper):
    """
    Scraper para festivos locales de Madrid desde el BOCM
    
    Fuente: Resolución de la Dirección General de Trabajo
    Publicación: Diciembre del año anterior
    Municipios: 179
    """
    
    # URLs conocidas de resoluciones de festivos locales
    KNOWN_URLS = {
        2026: "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/12/12/BOCM-20251212-34.PDF",
    }
    CACHE_FILE = "config/madrid_urls_cache.json"
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        """
        Args:
            year: Año del calendario
            municipio: Municipio específico (None = todos)
        """
        super().__init__(year=year, ccaa='madrid', tipo='locales')
        self.municipio = municipio
        self._load_cache()
    
    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json
        
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
            cache['locales'][str(year)] = url
            
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
            f"1. Busca en https://www.bocm.es 'fiestas locales {self.year}'\n"
            f"2. Encuentra la Resolución (publicada en dic {self.year-1})\n"
            f"3. Añade la URL al cache ejecutando este scraper\n"
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos locales desde el contenido del BOCM.
        Formato: "— Municipio: fecha1 y fecha2."
        """
        print(f"🔍 Parseando festivos locales de Madrid...")
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        festivos = []
        
        # Buscar todas las líneas con el patrón "— Municipio: fechas"
        patron = r'—\s*([^:]+):\s*([^.]+)\.'
        matches = re.finditer(patron, content)
        
        municipios_encontrados = 0
        municipios_sin_datos = 0
        
        for match in matches:
            nombre_municipio = match.group(1).strip()
            fechas_texto = match.group(2).strip()
            
            # Normalizar nombre del municipio
            nombre_municipio = self._normalizar_municipio(nombre_municipio)
            
            municipios_encontrados += 1
            
            # Verificar si hay datos
            if 'no comunicado' in fechas_texto.lower():
                municipios_sin_datos += 1
                continue
            
            # Si se especificó un municipio, filtrar
            if self.municipio:
                if self._normalizar_municipio(self.municipio).lower() != nombre_municipio.lower():
                    continue
            
            # Extraer las fechas
            fechas_extraidas = self._extraer_fechas(fechas_texto)
            
            for fecha_iso, fecha_texto in fechas_extraidas:
                festivos.append({
                    'fecha': fecha_iso,
                    'fecha_texto': fecha_texto,
                    'descripcion': f'Festivo local de {nombre_municipio}',
                    'tipo': 'local',
                    'ambito': nombre_municipio,
                    'municipio': nombre_municipio,
                    'sustituible': False,
                    'year': self.year
                })
        
        print(f"   📊 Municipios encontrados: {municipios_encontrados}")
        print(f"   ⚠️  Municipios sin datos: {municipios_sin_datos}")
        print(f"   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def _normalizar_municipio(self, nombre: str) -> str:
        """Normaliza el nombre del municipio"""
        nombre = ' '.join(nombre.split())
        
        palabras = nombre.split()
        resultado = []
        
        articulos = {'de', 'del', 'la', 'el', 'las', 'los', 'y'}
        
        for i, palabra in enumerate(palabras):
            if i == 0 or palabra.lower() not in articulos:
                resultado.append(palabra.capitalize())
            else:
                resultado.append(palabra.lower())
        
        return ' '.join(resultado)
    
    def _extraer_fechas(self, texto: str) -> List[tuple]:
        """
        Extrae fechas de un texto.
        Formatos: "3defebreroy15demayo" o "3 de febrero y 15 de mayo"
        """
        fechas = []
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Normalizar texto: añadir espacios antes de "de"
        texto_normalizado = re.sub(r'(\d+)de', r'\1 de ', texto.lower())
        texto_normalizado = re.sub(r'y(\d+)', r'y \1', texto_normalizado)
        
        # Patrón: "3 de febrero y 15 de mayo" (ahora normalizado)
        patron = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        matches = re.finditer(patron, texto_normalizado)
        
        for match in matches:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            mes = meses[mes_texto]
            
            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
            fecha_texto = f"{dia} de {mes_texto}"
            
            if (fecha_iso, fecha_texto) not in fechas:
                fechas.append((fecha_iso, fecha_texto))
        
        return fechas[:2]  # Máximo 2 festivos locales

def main():
    """Test del scraper"""
    import sys
    
    year = 2026
    municipio = None
    
    # Argumentos: python -m scrapers.ccaa.madrid.locales [año] [municipio]
    # O: python -m scrapers.ccaa.madrid.locales [municipio] [año]
    
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
        print(f"🧪 TEST: Madrid Locales - {municipio} {year}")
    else:
        print(f"🧪 TEST: Madrid Locales - Todos los municipios {year}")
    print("=" * 80)
    
    scraper = MadridLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        
        if municipio:
            filename = f"data/madrid_{municipio.lower().replace(' ', '_')}_{year}"
        else:
            filename = f"data/madrid_locales_{year}"
        
        scraper.save_to_json(f"{filename}.json")
        scraper.save_to_excel(f"{filename}.xlsx")
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()