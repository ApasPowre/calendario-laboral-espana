"""Scraper para festivos locales de Galicia"""

from scrapers.core.base_scraper import BaseScraper
from typing import List, Dict, Optional
import re


class GaliciaLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Galicia desde el DOG"""
    
    CACHE_FILE = "config/galicia_urls_cache.json"
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='galicia', tipo='locales')
        self._load_cache()
        
        # Si se especifica municipio, hacer fuzzy matching
        if municipio:
            import json
            from utils.normalizer import find_municipio
            
            # Cargar todos los municipios de Galicia
            with open('config/galicia_municipios.json', 'r', encoding='utf-8') as f:
                provincias_data = json.load(f)
            
            # Crear lista plana
            todos_municipios = []
            for munis in provincias_data.values():
                todos_municipios.extend(munis)
            
            # Buscar mejor match
            mejor_match = find_municipio(municipio, todos_municipios, threshold=95)
            
            if mejor_match:
                self.municipio = mejor_match
                if mejor_match.lower() != municipio.lower():
                    print(f"   🔍 Fuzzy match: '{municipio}' → '{mejor_match}'")
            else:
                self.municipio = municipio
        else:
            self.municipio = None
    
    def _load_cache(self):
        """Carga URLs del cache"""
        import os
        import json
        
        self.cached_urls = {}
        
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cached_urls = json.load(f)
                print(f"📦 Cache cargado: {len(self.cached_urls)} URLs")
            except:
                self.cached_urls = {}
        else:
            self.cached_urls = {}
    
    def get_source_url(self) -> str:
        """Devuelve la URL del DOG"""
        year_str = str(self.year)
        
        # 1. Cache
        if year_str in self.cached_urls:
            url = self.cached_urls[year_str]
            print(f"📦 URL en cache para {self.year}: {url}")
            return url
        
        # 2. Auto-discovery
        print(f"🔍 Auto-discovery para {self.year} (no está en cache)...")
        
        from scrapers.discovery.ccaa.galicia_discovery import auto_discover_galicia
        url = auto_discover_galicia(self.year)
        
        if url:
            print(f"✅ URL encontrada via discovery: {url}")
            return url
        
        raise ValueError(
            f"No se encontró URL para Galicia {self.year}.\n"
            f"Por favor:\n"
            f"1. Busca manualmente en: https://www.xunta.gal/dog\n"
            f"2. Busca 'fiestas locales {self.year}'\n"
            f"3. Añade la URL a {self.CACHE_FILE}"
        )
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """Parsea festivos desde el HTML del DOG"""
        from bs4 import BeautifulSoup
        
        print("🔍 Parseando festivos locales de Galicia...")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Buscar contenido principal
        contenido = soup.find('div', class_='textoNormal') or soup.find('div', id='texto') or soup.find('body')
        
        if not contenido:
            print("   ❌ No se encontró contenido")
            return []
        
        texto = contenido.get_text()
        
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        festivos = []
        provincia_actual = None
        
        # Patrón de provincia: "Provincia: NOMBRE."
        patron_provincia = r'Provincia:\s*(.+?)\.'
        
        # Patrón de municipio: "Número. Municipio: festivos..."
        patron_municipio = r'^\d+\.\s*([^:]+):\s*(.+)$'
        
        lineas = texto.split('\n')
        
        for linea in lineas:
            linea_clean = linea.strip()
            
            # Detectar provincia
            match_prov = re.match(patron_provincia, linea_clean)
            if match_prov:
                provincia_actual = match_prov.group(1).strip()
                print(f"\n📍 {provincia_actual.upper()}:")
                continue
            
            # Detectar municipio
            match_mun = re.match(patron_municipio, linea_clean)
            if match_mun:
                nombre_municipio = match_mun.group(1).strip()
                festivos_texto = match_mun.group(2).strip()
                
                # Filtrar por municipio si se especificó
                if self.municipio:
                    from utils.normalizer import MunicipioNormalizer
                    if not MunicipioNormalizer.are_equivalent(self.municipio, nombre_municipio, threshold=95):
                        continue
                    print(f"   ✅ Encontrado: {nombre_municipio}")
                
                # Parsear los festivos (separados por ";")
                festivos_lista = festivos_texto.split(';')
                
                for festivo_str in festivos_lista:
                    festivo_str = festivo_str.strip()
                    if not festivo_str:
                        continue
                    
                    # Extraer TODAS las fechas del string
                    fechas = re.findall(r'(\d{1,2})\s+de\s+(\w+)', festivo_str)
                    
                    if not fechas:
                        continue
                    
                    # Ver si hay texto después de la última fecha (descripción)
                    ultima_fecha_pos = festivo_str.rfind(f"{fechas[-1][0]} de {fechas[-1][1]}")
                    resto_texto = festivo_str[ultima_fecha_pos + len(f"{fechas[-1][0]} de {fechas[-1][1]}"):].strip()
                    
                    # Limpiar resto_texto (quitar puntos, comas)
                    resto_texto = resto_texto.lstrip(',.:;').strip()
                    
                    # Si el resto_texto es otra fecha, no es descripción
                    es_descripcion = resto_texto and not re.match(r'^\d{1,2}\s+de\s+\w+', resto_texto)
                    
                    descripcion_final = resto_texto if es_descripcion else None
                    
                    # Convertir meses
                    meses = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    
                    # Procesar cada fecha
                    for i, (dia_str, mes_texto) in enumerate(fechas):
                        dia = int(dia_str)
                        mes_texto_lower = mes_texto.lower()
                        mes = meses.get(mes_texto_lower)
                        
                        if mes:
                            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
                            
                            # Solo el último festivo lleva la descripción (si existe)
                            if i == len(fechas) - 1 and descripcion_final:
                                descripcion = descripcion_final
                            else:
                                descripcion = f"Festivo local de {nombre_municipio}"
                            
                            festivos.append({
                                'fecha': fecha_iso,
                                'fecha_texto': f"{dia} de {mes_texto_lower}",
                                'descripcion': descripcion,
                                'tipo': 'local',
                                'ambito': 'local',
                                'municipio': nombre_municipio,
                                'provincia': provincia_actual,
                                'year': self.year
                            })
        
        print(f"\n   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
