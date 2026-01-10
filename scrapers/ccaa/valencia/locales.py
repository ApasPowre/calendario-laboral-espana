"""
Valencia Locales Scraper
Extrae festivos locales desde el DOGV (Diari Oficial de la Generalitat Valenciana)
Parsea PDFs con formato: "MUNICIPIO: DD de mes, descripción; DD de mes, descripción."
"""

from typing import List, Dict, Optional
import re
import requests
from pypdf import PdfReader
from scrapers.core.base_scraper import BaseScraper


class ValenciaLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Valencia"""
    
    KNOWN_URLS = {
        2026: "https://dogv.gva.es/datos/2025/11/14/pdf/2025_46326_es.pdf",
        # Añadir más años según se publiquen
    }
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='valencia', tipo='locales')
        
        # Si se especifica municipio, hacer fuzzy matching UNA VEZ contra la lista de municipios
        if municipio:
            import json
            from utils.normalizer import find_municipio
            
            # Cargar todos los municipios de Valencia
            with open('config/valencia_municipios.json', 'r', encoding='utf-8') as f:
                provincias_data = json.load(f)
            
            # Crear lista plana de todos los municipios
            todos_municipios = []
            for munis in provincias_data.values():
                if isinstance(munis, list):
                    todos_municipios.extend(munis)
            
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
        """Devuelve la URL del DOGV para el año especificado"""
        from scrapers.discovery.ccaa.valencia_discovery import get_cached_url, auto_discover_valencia, save_to_cache
        
        # 1. Intentar desde KNOWN_URLS
        if self.year in self.KNOWN_URLS:
            return self.KNOWN_URLS[self.year]
        
        # 2. Intentar desde caché
        url = get_cached_url(self.year)
        if url:
            return url
        
        # 3. Auto-discovery
        url = auto_discover_valencia(self.year)
        if url:
            save_to_cache(self.year, url)
            return url
        
        # 4. Error si no se encuentra
        raise ValueError(f"No se pudo encontrar URL del DOGV para Valencia locales {self.year}")
    
    def download_content(self, url: str) -> str:
        """Descarga y extrae texto del PDF"""
        print(f"📥 Descargando PDF: {url}")
        
        r = requests.get(url, timeout=30)
        
        if r.status_code != 200:
            raise Exception(f"Error descargando PDF: {r.status_code}")
        
        # Guardar temporalmente
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(r.content)
            tmp_path = tmp.name
        
        try:
            # Extraer texto con pypdf
            reader = PdfReader(tmp_path)
            texto_completo = ""
            
            for page in reader.pages:
                texto_completo += page.extract_text() + "\n"
            
            print(f"✅ PDF extraído ({len(reader.pages)} páginas, {len(texto_completo)} caracteres)")
            
            return texto_completo
        finally:
            os.unlink(tmp_path)
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el texto del PDF.
        
        Formato:
        MUNICIPIO: DD de mes, descripción; DD de mes, descripción.
        """
        print(f"🔍 Parseando festivos locales de Valencia...")
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        lineas = content.split('\n')
        
        provincias = ['ALICANTE', 'CASTELLÓN', 'VALENCIA']
        provincia_actual = None
        festivos = []
        
        # Patrón: MUNICIPIO en mayúsculas seguido de ":"
        patron_municipio = r'^([A-ZÁÉÍÓÚÑÜÀÈÌÒÙ\',\s]+):\s*(.+)'
        
        i = 0
        while i < len(lineas):
            linea = lineas[i].strip()
            
            # Detectar provincia
            if any(f'PROVINCIA DE {prov}' in linea.upper() for prov in provincias):
                for prov in provincias:
                    if prov in linea.upper():
                        provincia_actual = prov
                        print(f"\n📍 {provincia_actual}:")
                        break
                i += 1
                continue
            
            # Intentar parsear municipio
            match = re.match(patron_municipio, linea)
            if match:
                nombre_municipio = match.group(1).strip()
                fechas_texto = match.group(2).strip()
                
                # Continuar leyendo si la línea no termina en punto
                while not fechas_texto.endswith('.') and i + 1 < len(lineas):
                    i += 1
                    siguiente = lineas[i].strip()
                    if siguiente and not re.match(patron_municipio, siguiente):
                        fechas_texto += " " + siguiente
                    else:
                        i -= 1
                        break
                
                # Normalizar nombre del municipio
                nombre_municipio_normalizado = self._normalizar_municipio(nombre_municipio)
                
                # Filtrar por municipio si se especificó
                if self.municipio:
                    municipio_busqueda = self._normalizar_municipio(self.municipio).replace(' ', '').lower()
                    municipio_encontrado = nombre_municipio_normalizado.replace(' ', '').lower()
                    
                    if municipio_busqueda not in municipio_encontrado:
                        i += 1
                        continue
                
                # Extraer fechas
                fechas_extraidas = self._extraer_fechas(fechas_texto)
                
                if fechas_extraidas:
                    print(f"   • {nombre_municipio_normalizado}: {len(fechas_extraidas)} festivos")
                    
                    for fecha_iso, fecha_texto in fechas_extraidas:
                        festivos.append({
                            'fecha': fecha_iso,
                            'fecha_texto': fecha_texto,
                            'descripcion': f'Festivo local de {nombre_municipio_normalizado}',
                            'tipo': 'local',
                            'ambito': nombre_municipio_normalizado,
                            'municipio': nombre_municipio_normalizado,
                            'provincia': provincia_actual,
                            'sustituible': False,
                            'year': self.year
                        })
            
            i += 1
        
        print(f"\n   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def _extraer_fechas(self, texto: str) -> List[tuple]:
        """Extrae fechas del formato 'DD de mes' incluyendo compuestas '27 y 28 de agosto'"""
        fechas = []
        
        # Normalizar texto
        texto = texto.lower()
        
        # Expandir fechas compuestas: "27 y 28 de agosto" → "27 de agosto y 28 de agosto"
        patron_expandir = r'(\d{1,2})\s+y\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        
        def expandir_fechas(match):
            dia1 = match.group(1)
            dia2 = match.group(2)
            mes = match.group(3)
            return f"{dia1} de {mes} y {dia2} de {mes}"
        
        texto = re.sub(patron_expandir, expandir_fechas, texto)
        
        # Patrón básico: DD de mes
        patron_fecha = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        
        for match in re.finditer(patron_fecha, texto):
            dia = int(match.group(1))
            mes_texto = match.group(2)
            
            fecha_iso = self._convertir_fecha(dia, mes_texto)
            if fecha_iso:
                fechas.append((fecha_iso, f"{dia} de {mes_texto}"))
        
        return fechas
    
    def _convertir_fecha(self, dia: int, mes_texto: str) -> Optional[str]:
        """Convierte día y mes a formato ISO"""
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        mes = meses.get(mes_texto.lower())
        if not mes:
            return None
        
        return f"{self.year}-{mes:02d}-{dia:02d}"
    
    def _normalizar_municipio(self, nombre: str) -> str:
        """Normaliza el nombre del municipio"""
        # Limpiar caracteres especiales
        nombre = nombre.strip()
        
        # Casos especiales EATIMs
        if 'eatim' in nombre.lower():
            # "Eatim de La Xara, dependiente de Dènia" → "La Xara"
            match = re.search(r'eatim\s+de\s+([^,]+)', nombre, re.IGNORECASE)
            if match:
                nombre = match.group(1).strip()
        
        # Title case
        nombre = nombre.title()
        
        # Artículos y preposiciones en minúscula
        nombre = re.sub(r'\bDe\b', 'de', nombre)
        nombre = re.sub(r'\bDel\b', 'del', nombre)
        nombre = re.sub(r'\bLa\b', 'la', nombre)
        nombre = re.sub(r'\bLas\b', 'las', nombre)
        nombre = re.sub(r'\bEl\b', 'el', nombre)
        nombre = re.sub(r'\bLos\b', 'los', nombre)
        nombre = re.sub(r'\bY\b', 'y', nombre)
        
        # Excepciones: artículos al inicio en mayúscula
        if nombre.startswith('la '): nombre = 'La' + nombre[2:]
        if nombre.startswith('las '): nombre = 'Las' + nombre[3:]
        if nombre.startswith('el '): nombre = 'El' + nombre[2:]
        if nombre.startswith('los '): nombre = 'Los' + nombre[3:]
        
        # Casos especiales valencianos
        nombre = nombre.replace("L'", "l'")  # l'Alfàs
        if nombre.startswith("l'"): nombre = "L'" + nombre[2:]
        
        return nombre


# Para testing
if __name__ == "__main__":
    import sys
    
    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    print(f"{'='*80}")
    print(f"🧪 TEST: Valencia Locales - {municipio or 'TODOS'} {year}")
    print(f"{'='*80}\n")
    
    scraper = ValenciaLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN - VALENCIA {year}")
    print(f"{'='*80}")
    print(f"Total festivos: {len(festivos)}\n")
    
    if festivos:
        print("📅 Festivos:")
        for f in festivos[:10]:
            print(f"   • {f['fecha']} - {f['descripcion']}")
        
        if len(festivos) > 10:
            print(f"\n   ... y {len(festivos) - 10} más")