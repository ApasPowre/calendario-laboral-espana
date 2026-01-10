"""
Andalucía Locales Scraper
Extrae festivos locales desde el BOJA (Boletín Oficial de la Junta de Andalucía)
"""

from typing import List, Dict, Optional
import re
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper


class AndaluciaLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Andalucía"""
    
    KNOWN_URLS = {
        2026: "https://www.juntadeandalucia.es/boja/2025/197/28",
        # Añadir más años según se publiquen
    }
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='andalucia', tipo='locales')
        
        # Si se especifica municipio, hacer fuzzy matching UNA VEZ contra la lista de municipios
        if municipio:
            import json
            from utils.normalizer import find_municipio
            
            # Cargar todos los municipios de Andalucía
            with open('config/andalucia_municipios.json', 'r', encoding='utf-8') as f:
                provincias_data = json.load(f)
            
            # Crear lista plana de todos los municipios Y normalizarlos
            from utils.normalizer import normalize_municipio
            todos_municipios = []
            for munis in provincias_data.values():
                # Normalizar cada municipio (resuelve "Ejido, el" → "El Ejido")
                todos_municipios.extend([normalize_municipio(m) for m in munis])
            
            # Buscar el mejor match
            mejor_match = find_municipio(municipio, todos_municipios, threshold=80)
            
            if mejor_match:
                self.municipio = mejor_match
                if mejor_match.lower() != municipio.lower():
                    print(f"   🔍 Fuzzy match: '{municipio}' → '{mejor_match}'")
            else:
                self.municipio = municipio
        else:
            self.municipio = None
    
    def get_source_url(self) -> str:
        """Devuelve la URL del BOJA para el año especificado"""
        from scrapers.discovery.ccaa.andalucia_discovery import get_cached_url, auto_discover_andalucia, save_to_cache
        
        # 1. Intentar desde KNOWN_URLS
        if self.year in self.KNOWN_URLS:
            return self.KNOWN_URLS[self.year]
        
        # 2. Intentar desde caché
        url = get_cached_url(self.year)
        if url:
            return url
        
        # 3. Auto-discovery
        url = auto_discover_andalucia(self.year)
        if url:
            save_to_cache(self.year, url)
            return url
        
        # 4. Error si no se encuentra
        raise ValueError(f"No se pudo encontrar URL del BOJA para Andalucía locales {self.year}")

    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos locales desde el contenido del BOJA.
        
        Formato secuencial:
        MUNICIPIO
        DD DE MES
        DD DE MES
        """
        print(f"🔍 Parseando festivos locales de Andalucía...")
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        soup = BeautifulSoup(content, 'html.parser')
        texto = soup.get_text()
        
        lineas = texto.split('\n')
        lineas = [l.strip() for l in lineas]  # Limpiar espacios
        
        provincias = ['ALMERÍA', 'CÁDIZ', 'CÓRDOBA', 'GRANADA', 'HUELVA', 'JAÉN', 'MÁLAGA', 'SEVILLA']
        provincia_actual = None
        festivos = []
        
        i = 0
        while i < len(lineas):
            linea = lineas[i]
            
            # Detectar provincia SOLO si no tiene fechas después
            if linea in provincias:
                # Verificar si las 2 líneas siguientes son fechas
                tiene_fechas = False
                if i + 2 < len(lineas):
                    siguiente1 = lineas[i + 1].strip()
                    siguiente2 = lineas[i + 2].strip()
                    if re.match(r'^\d{1,2}\s+DE\s+[A-Z]+$', siguiente1) and re.match(r'^\d{1,2}\s+DE\s+[A-Z]+$', siguiente2):
                        tiene_fechas = True
                
                # Si tiene fechas, NO es provincia sino municipio capital
                if not tiene_fechas:
                    provincia_actual = linea
                    i += 1
                    continue
                # Si tiene fechas, continuar para procesarla como municipio
            
            # Detectar municipio (mayúsculas, no vacío, no es fecha)
            if linea and linea.isupper() and not re.match(r'^\d{1,2}\s+DE\s+[A-Z]+$', linea) and 'FIESTAS' not in linea and 'ANEXO' not in linea and 'RESOLV' not in linea:
                nombre_municipio = linea
                
                # Normalizar nombre del municipio
                nombre_municipio_normalizado = self._normalizar_municipio(nombre_municipio)
                
                # Si se especificó un municipio, filtrar
                if self.municipio:
                    # Intento 1: Comparación exacta normalizada (rápido)
                    municipio_busqueda = self._normalizar_municipio(self.municipio).lower()
                    municipio_encontrado = self._normalizar_municipio(nombre_municipio).lower()
                    
                    if municipio_busqueda == municipio_encontrado:
                        # Match exacto, continuar procesando
                        pass
                    else:
                        # Intento 2: Fuzzy matching (más lento pero flexible)
                        from utils.normalizer import MunicipioNormalizer
                        
                        if not MunicipioNormalizer.are_equivalent(
                            self.municipio, 
                            nombre_municipio, 
                            threshold=85
                        ):
                            i += 1
                            continue  # No hace match, saltar este municipio
                
                # Las dos líneas siguientes deberían ser las fechas
                if i + 2 < len(lineas):
                    fecha1_texto = lineas[i + 1].strip()
                    fecha2_texto = lineas[i + 2].strip()
                    
                    # Verificar que son fechas válidas
                    if re.match(r'^\d{1,2}\s+DE\s+[A-Z]+$', fecha1_texto) and re.match(r'^\d{1,2}\s+DE\s+[A-Z]+$', fecha2_texto):
                        # Convertir fechas a formato ISO
                        fecha1_iso = self._convertir_fecha(fecha1_texto)
                        fecha2_iso = self._convertir_fecha(fecha2_texto)
                        
                        if fecha1_iso and fecha2_iso:
                            # Crear festivos
                            festivos.append({
                                'fecha': fecha1_iso,
                                'fecha_texto': fecha1_texto.lower(),
                                'descripcion': f'Festivo local de {nombre_municipio_normalizado.title()}',
                                'tipo': 'local',
                                'ambito': nombre_municipio_normalizado,
                                'municipio': nombre_municipio_normalizado,
                                'provincia': provincia_actual,
                                'sustituible': False,
                                'year': self.year
                            })
                            
                            festivos.append({
                                'fecha': fecha2_iso,
                                'fecha_texto': fecha2_texto.lower(),
                                'descripcion': f'Festivo local de {nombre_municipio_normalizado.title()}',
                                'tipo': 'local',
                                'ambito': nombre_municipio_normalizado,
                                'municipio': nombre_municipio_normalizado,
                                'provincia': provincia_actual,
                                'sustituible': False,
                                'year': self.year
                            })
                        
                        i += 3  # Saltar municipio + 2 fechas
                        continue
            
            i += 1
        
        print(f"   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def _convertir_fecha(self, fecha_texto: str) -> Optional[str]:
        """Convierte 'DD DE MES' a 'YYYY-MM-DD'"""
        meses = {
            'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
            'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
            'SEPTIEMBRE': 9, 'SPTIEMBRE': 9,  # Typo en el BOJA
            'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
        }
        
        match = re.match(r'^(\d{1,2})\s+DE\s+([A-Z]+)$', fecha_texto.upper())
        if not match:
            return None
        
        dia = int(match.group(1))
        mes_texto = match.group(2)
        mes = meses.get(mes_texto)
        
        if not mes:
            return None
        
        return f"{self.year}-{mes:02d}-{dia:02d}"
    
    def _normalizar_municipio(self, nombre: str) -> str:
        """Normaliza el nombre del municipio"""
        # Convertir a title case
        nombre = nombre.title()
        
        # Casos especiales de artículos y preposiciones
        nombre = re.sub(r'\bDe\b', 'de', nombre)
        nombre = re.sub(r'\bDel\b', 'del', nombre)
        nombre = re.sub(r'\bLa\b', 'la', nombre)
        nombre = re.sub(r'\bLas\b', 'las', nombre)
        nombre = re.sub(r'\bEl\b', 'el', nombre)
        nombre = re.sub(r'\bLos\b', 'los', nombre)
        nombre = re.sub(r'\bY\b', 'y', nombre)
        
        # Excepciones: artículos al inicio van en mayúscula
        if nombre.startswith('la '):
            nombre = 'La' + nombre[2:]
        if nombre.startswith('las '):
            nombre = 'Las' + nombre[3:]
        if nombre.startswith('el '):
            nombre = 'El' + nombre[2:]
        if nombre.startswith('los '):
            nombre = 'Los' + nombre[3:]
        
        return nombre


# Para testing
if __name__ == "__main__":
    import sys
    
    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    print(f"{'='*80}")
    print(f"🧪 TEST: Andalucía Locales - {municipio or 'TODOS'} {year}")
    print(f"{'='*80}\n")
    
    scraper = AndaluciaLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN - ANDALUCÍA {year}")
    print(f"{'='*80}")
    print(f"Total festivos: {len(festivos)}\n")
    
    if festivos:
        print("📅 Festivos:")
        for f in festivos[:10]:  # Mostrar solo primeros 10
            print(f"   • {f['fecha']} - {f['descripcion']}")
        
        if len(festivos) > 10:
            print(f"\n   ... y {len(festivos) - 10} más")