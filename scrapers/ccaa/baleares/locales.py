"""
Baleares Locales Scraper
Extrae festivos locales desde la página oficial del Govern de les Illes Balears
Parsea tablas HTML organizadas por islas (Mallorca, Menorca, Ibiza, Formentera)
"""

from typing import List, Dict, Optional
import re
import requests
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper


class BalearesLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Baleares"""
    
    KNOWN_URLS = {
        2026: "https://www.caib.es/sites/calendarilaboral/es/aao_2026/",
        2025: "https://www.caib.es/sites/calendarilaboral/es/aao_2025/",
        2024: "https://www.caib.es/sites/calendarilaboral/es/aao_2024/",
        # El patrón es predecible: cambiar el año en la URL
    }
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='baleares', tipo='locales')
        self.municipio = municipio
    
    def get_source_url(self) -> str:
        """Devuelve la URL de la página oficial para el año especificado"""
        if self.year in self.KNOWN_URLS:
            return self.KNOWN_URLS[self.year]
        
        # Si no está en KNOWN_URLS, construir URL basándose en el patrón
        return f"https://www.caib.es/sites/calendarilaboral/es/aao_{self.year}/"
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde las tablas HTML.
        
        Estructura:
        - Tabla 1: Festivos autonómicos (no los procesamos aquí)
        - Tabla 2: Mallorca (municipios con formato: MUNICIPIO | Fechas)
        - Tabla 3: Menorca
        - Tabla 4: Ibiza
        - Tabla 5: Formentera
        """
        print(f"🔍 Parseando festivos locales de Baleares...")
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        soup = BeautifulSoup(content, 'html.parser')
        tablas = soup.find_all('table')
        
        if len(tablas) < 2:
            print(f"   ⚠️  No se encontraron suficientes tablas")
            return []
        
        # Tablas 2-5 contienen festivos locales por isla
        # Tabla 1 son festivos autonómicos (saltarla)
        islas = {
            1: 'Mallorca',
            2: 'Menorca', 
            3: 'Ibiza',
            4: 'Formentera'
        }
        
        festivos = []
        
        for i in range(1, min(5, len(tablas))):
            tabla = tablas[i]
            isla = islas.get(i, f'Isla {i+1}')
            
            print(f"\n📍 {isla}:")
            
            filas = tabla.find_all('tr')
            
            for fila in filas:
                celdas = fila.find_all(['th', 'td'])
                
                if len(celdas) < 2:
                    continue
                
                # Primera celda: nombre del municipio (puede tener múltiples núcleos)
                nombre_municipio_raw = celdas[0].get_text(strip=True)
                
                # Segunda celda: fechas de festivos
                fechas_texto = celdas[1].get_text()
                
                # Parsear municipio principal (antes de saltos de línea o espacios múltiples)
                nombre_municipio = self._extraer_municipio_principal(nombre_municipio_raw)
                
                # Normalizar nombre
                nombre_municipio_normalizado = self._normalizar_municipio(nombre_municipio)
                
                # Filtrar por municipio si se especificó
                if self.municipio:
                    municipio_busqueda = self._normalizar_municipio(self.municipio).lower()
                    municipio_encontrado = nombre_municipio_normalizado.lower()
                    
                    # Comparación EXACTA (no subcadenas)
                    if municipio_busqueda != municipio_encontrado:
                        continue
                
                # Extraer fechas
                fechas_extraidas = self._extraer_fechas(fechas_texto)
                
                if fechas_extraidas:
                    print(f"   • {nombre_municipio_normalizado}: {len(fechas_extraidas)} festivos")
                    
                    for fecha_iso, fecha_texto, descripcion in fechas_extraidas:
                        festivos.append({
                            'fecha': fecha_iso,
                            'fecha_texto': fecha_texto,
                            'descripcion': descripcion or f'Festivo local de {nombre_municipio_normalizado}',
                            'tipo': 'local',
                            'ambito': nombre_municipio_normalizado,
                            'municipio': nombre_municipio_normalizado,
                            'isla': isla,
                            'sustituible': False,
                            'year': self.year
                        })
        
        print(f"\n   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def _extraer_municipio_principal(self, texto: str) -> str:
        """
        Extrae el nombre del municipio principal del texto.
        Ej: "ANDRATX\nAndratx\n Port d'Andratx" → "ANDRATX"
        """
        # Tomar la primera línea/palabra en mayúsculas
        lineas = texto.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if linea and linea.isupper():
                return linea
        
        # Si no hay líneas en mayúsculas, tomar la primera línea
        return lineas[0].strip() if lineas else texto.strip()
    
    def _extraer_fechas(self, texto: str) -> List[tuple]:
        """
        Extrae fechas del formato:
        "DD de mes: Descripción\nDD de mes: Descripción"
        o simplemente "DD de mes\nDD de mes"
        
        Returns:
            Lista de tuplas (fecha_iso, fecha_texto, descripcion)
        """
        fechas = []
        
        # Separar por saltos de línea
        lineas = texto.split('\n')
        
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            
            # Patrón: "DD de mes" opcionalmente seguido de ": descripción"
            # Ejemplos:
            # "17 de enero: San Antonio"
            # "4 de diciembre"
            # "7 de diciembre"
            patron = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?:\s*:\s*(.+))?'
            
            match = re.search(patron, linea, re.IGNORECASE)
            if match:
                dia = int(match.group(1))
                mes_texto = match.group(2).lower()
                descripcion = match.group(3).strip() if match.group(3) else None
                
                fecha_iso = self._convertir_fecha(dia, mes_texto)
                if fecha_iso:
                    fecha_texto = f"{dia} de {mes_texto}"
                    fechas.append((fecha_iso, fecha_texto, descripcion))
        
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
        # Title case
        nombre = nombre.title()
        
        # Casos especiales catalanes/mallorquines
        nombre = re.sub(r'\bDe\b', 'de', nombre)
        nombre = re.sub(r'\bDel\b', 'del', nombre)
        nombre = re.sub(r'\bDes\b', 'des', nombre)
        nombre = re.sub(r'\bSa\b', 'sa', nombre)
        nombre = re.sub(r'\bSes\b', 'ses', nombre)
        nombre = re.sub(r"D'", "d'", nombre)
        nombre = re.sub(r"S'", "s'", nombre)
        nombre = re.sub(r"L'", "l'", nombre)
        
        # Excepciones: nombres que empiezan con artículo
        if nombre.lower().startswith("es "):
            nombre = "Es" + nombre[2:]
        if nombre.lower().startswith("sa "):
            nombre = "Sa" + nombre[2:]
        if nombre.lower().startswith("ses "):
            nombre = "Ses" + nombre[3:]
        if nombre.lower().startswith("d'"):
            nombre = "D'" + nombre[2:]
        if nombre.lower().startswith("s'"):
            nombre = "S'" + nombre[2:]
        if nombre.lower().startswith("l'"):
            nombre = "L'" + nombre[2:]
        
        # Sant/Santa
        nombre = re.sub(r'\bSant\b', 'Sant', nombre)
        nombre = re.sub(r'\bSanta\b', 'Santa', nombre)
        nombre = re.sub(r'\bSan\b', 'San', nombre)
        
        return nombre


# Para testing
if __name__ == "__main__":
    import sys
    
    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    print(f"{'='*80}")
    print(f"🧪 TEST: Baleares Locales - {municipio or 'TODOS'} {year}")
    print(f"{'='*80}\n")
    
    scraper = BalearesLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN - BALEARES {year}")
    print(f"{'='*80}")
    print(f"Total festivos: {len(festivos)}\n")
    
    if festivos:
        print("📅 Festivos:")
        for f in festivos[:10]:
            desc = f['descripcion'][:50] if f['descripcion'] else 'Sin descripción'
            print(f"   • {f['fecha']} - {desc}")
        
        if len(festivos) > 10:
            print(f"\n   ... y {len(festivos) - 10} más")