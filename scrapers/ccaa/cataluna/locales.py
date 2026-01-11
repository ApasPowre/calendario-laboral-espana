"""
Cataluña Locales Scraper
Extrae festivos locales desde el DOGC (Diari Oficial de la Generalitat de Catalunya)
Parsea XML en formato Akoma Ntoso con HTML escapado
"""

from typing import List, Dict, Optional
import re
import requests
import xml.etree.ElementTree as ET
import html
from bs4 import BeautifulSoup
from scrapers.core.base_scraper import BaseScraper
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CatalunaLocalesScraper(BaseScraper):
    """Scraper para festivos locales de Cataluña"""
    
    # Cada año necesita documentId y versionId
    KNOWN_URLS = {
        2026: {
            'documentId': '1032232',
            'versionId': '2125486',
        },
        # Añadir más años según se publiquen
    }
    
    def __init__(self, year: int, municipio: Optional[str] = None):
        super().__init__(year=year, ccaa='cataluna', tipo='locales')
        
        # Si se especifica municipio, hacer fuzzy matching UNA VEZ contra la lista de municipios
        if municipio:
            import json
            from utils.normalizer import find_municipio
            
            # Cargar todos los municipios de Cataluña
            with open('config/cataluna_municipios.json', 'r', encoding='utf-8') as f:
                comarcas_data = json.load(f)
            
            # Crear lista plana de todos los municipios
            todos_municipios = []
            for munis in comarcas_data.values():
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
        """Construye la URL del XML del DOGC para el año especificado"""
        if self.year not in self.KNOWN_URLS:
            raise ValueError(
                f"No hay datos disponibles para Cataluña {self.year}.\n"
                f"Años disponibles: {list(self.KNOWN_URLS.keys())}"
            )
        
        doc_info = self.KNOWN_URLS[self.year]
        document_id = doc_info['documentId']
        version_id = doc_info['versionId']
        
        url = f"https://portaldogc.gencat.cat/utilsEADOP/AppJava/AkomaNtoso?idNumber={document_id}&idVersion={version_id}&format=xml"
        
        return url
    
    def scrape(self) -> List[Dict]:
        """Ejecuta el proceso completo de scraping con fallback a archivo local"""
        import os
        
        print(f"\n{'='*80}")
        print(f"🔍 Iniciando scraping: {self.ccaa.upper()} - {self.tipo.upper()} - {self.year}")
        print(f"{'='*80}")
        
        # Intentar descargar desde URL
        try:
            url = self.get_source_url()
            content = self.download_content(url)
            festivos = self.parse_festivos(content)
            
            print(f"\n✅ Scraping completado:")
            print(f"   • Festivos extraídos: {len(festivos)}")
            print(f"   • Fuente: {url}")
            print(f"{'='*80}\n")
            
            return festivos
            
        except Exception as e:
            # Si falla la descarga, intentar leer desde archivo local
            local_file = f"examples/cataluna/festivos_locales_{self.year}.xml"
            
            if os.path.exists(local_file):
                print(f"\n⚠️  Descarga falló, usando archivo local: {local_file}")
                with open(local_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                festivos = self.parse_festivos(content)
                
                print(f"\n✅ Scraping completado:")
                print(f"   • Festivos extraídos: {len(festivos)}")
                print(f"   • Fuente: Archivo local")
                print(f"{'='*80}\n")
                
                return festivos
            else:
                print(f"\n❌ Error: {e}")
                print(f"❌ No existe archivo local: {local_file}")
                print(f"{'='*80}\n")
                return []
    
    def download_content(self, url: str) -> str:
        """Descarga el XML del DOGC (intentando múltiples métodos por problemas SSL)"""
        print(f"📥 Descargando XML: {url}")
        
        # Método 1: curl (suele funcionar mejor con SSL problemático)
        import subprocess
        
        try:
            result = subprocess.run(
                ['curl', '-k', '-L', url],  # -k ignora SSL, -L sigue redirects
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and len(result.stdout) > 1000:
                print(f"✅ XML descargado con curl ({len(result.stdout)} caracteres)")
                return result.stdout
        except Exception as e:
            print(f"⚠️  curl falló: {e}")
        
        # Método 2: requests con SSL verify=False
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            r = requests.get(url, timeout=30, verify=False, headers=headers)
            
            if r.status_code == 200:
                print(f"✅ XML descargado con requests ({len(r.text)} caracteres)")
                return r.text
        except Exception as e:
            print(f"⚠️  requests falló: {e}")
        
        raise Exception(f"No se pudo descargar el XML con ningún método")
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el XML Akoma Ntoso.
        
        Estructura:
        - XML contiene HTML escapado en el campo 'period'
        - HTML tiene formato: "MUNICIPIO, DD de mes y DD de mes."
        - Líneas indentadas son agregados/núcleos
        """
        print(f"🔍 Parseando festivos locales de Cataluña...")
        if self.municipio:
            print(f"   🎯 Filtrando por municipio: {self.municipio}")
        
        # Parsear XML
        root = ET.fromstring(content)
        
        # Buscar el campo 'period' que contiene el HTML
        ns = {'akn': 'http://docs.oasis-open.org/legaldocml/ns/akn/3.0'}
        content_elem = root.find('.//akn:content', ns)
        
        if content_elem is None:
            raise Exception("No se encontró el elemento 'content' en el XML")
        
        html_content = content_elem.get('period', '')
        
        if not html_content:
            raise Exception("El campo 'period' está vacío")
        
        # Decodificar HTML escapado
        html_decoded = html.unescape(html_content)
        
        # Parsear HTML con BeautifulSoup
        soup = BeautifulSoup(html_decoded, 'html.parser')
        
        # Extraer todo el texto
        texto = soup.get_text('\n')
        lineas = [l for l in texto.split('\n') if l.strip()]
        
        festivos = []
        provincia_actual = None
        municipio_principal = None
        
        for linea in lineas:
            linea_original = linea
            linea_strip = linea.strip()
            
            # Detectar provincias (en mayúsculas solas)
            provincias = ['ALT CAMP', 'ALT EMPORDÀ', 'ALT PENEDÈS', 'ALT URGELL', 'ALTA RIBAGORÇA', 
                         'ANOIA', 'BAGES', 'BAIX CAMP', 'BAIX EBRE', 'BAIX EMPORDÀ', 'BAIX LLOBREGAT',
                         'BAIX PENEDÈS', 'BARCELONÈS', 'BERGUEDÀ', 'CERDANYA', 'CONCA DE BARBERÀ',
                         'GARRAF', 'GARRIGUES', 'GARROTXA', 'GIRONÈS', 'MARESME', 'MOIANÈS',
                         'MONTSIÁ', 'NOGUERA', 'OSONA', 'PALLARS JUSSÀ', 'PALLARS SOBIRÀ',
                         'PLA DE L\'URGELL', 'PLA D\'URGELL', 'PRIORAT', 'RIBERA D\'EBRE',
                         'RIPOLLÈS', 'SEGARRA', 'SEGRIÀ', 'SELVA', 'SOLSONÈS', 'TARRAGONÈS',
                         'TERRA ALTA', 'URGELL', 'VAL D\'ARAN', 'VALLÈS OCCIDENTAL', 'VALLÈS ORIENTAL']
            
            if linea_strip.upper() in provincias:
                provincia_actual = linea_strip.title()
                print(f"\n📍 {provincia_actual}:")
                continue
            
            # Buscar líneas con fechas (formato: DD de mes)
            if re.search(r'\d{1,2}\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', linea_strip, re.IGNORECASE):
                
                # Determinar si es municipio principal o agregado
                es_agregado = linea_original.startswith('    ') or linea_original.startswith('\t')
                
                if not es_agregado:
                    # Es un municipio principal
                    nombre_municipio = self._extraer_nombre_municipio(linea_strip)
                    municipio_principal = nombre_municipio
                else:
                    # Es un agregado/núcleo
                    nombre_municipio = self._extraer_nombre_municipio(linea_strip)
                    # Si el municipio principal es conocido, incluirlo en el nombre
                    if municipio_principal:
                        nombre_municipio = f"{municipio_principal} - {nombre_municipio}"
                
                # Normalizar nombre
                nombre_normalizado = self._normalizar_municipio(nombre_municipio if not es_agregado else nombre_municipio.split(' - ')[-1])
                
                # Filtrar por municipio si se especificó
                if self.municipio:
                    municipio_busqueda = self._normalizar_municipio(self.municipio).lower()
                    municipio_encontrado = nombre_normalizado.lower()
                    
                    # Comparación exacta
                    if municipio_busqueda != municipio_encontrado:
                        continue
                
                # Extraer fechas
                fechas_extraidas = self._extraer_fechas(linea_strip)
                
                if fechas_extraidas:
                    if not es_agregado or not self.municipio:  # Solo contar municipios principales en el log
                        print(f"   • {nombre_normalizado}: {len(fechas_extraidas)} festivos")
                    
                    for fecha_iso, fecha_texto, descripcion in fechas_extraidas:
                        festivos.append({
                            'fecha': fecha_iso,
                            'fecha_texto': fecha_texto,
                            'descripcion': descripcion or f'Festivo local de {nombre_normalizado}',
                            'tipo': 'local',
                            'ambito': nombre_normalizado,
                            'municipio': nombre_normalizado,
                            'provincia': provincia_actual,
                            'sustituible': False,
                            'year': self.year
                        })
        
        print(f"\n   ✅ Festivos locales extraídos: {len(festivos)}")
        
        return festivos
    
    def _extraer_nombre_municipio(self, linea: str) -> str:
        """
        Extrae el nombre del municipio de la línea.
        Formato: "MUNICIPIO, DD de mes y DD de mes."
        """
        # Separar por la primera coma
        partes = linea.split(',', 1)
        if partes:
            return partes[0].strip()
        return linea.strip()
    
    def _extraer_fechas(self, texto: str) -> List[tuple]:
        """
        Extrae fechas del formato:
        "DD de mes y DD de mes" o "DD de mes, DD de mes"
        Ignora fechas con año explícito (como firmas)
        
        Returns:
            Lista de tuplas (fecha_iso, fecha_texto, descripcion)
        """
        fechas = []
        
        # Patrón: DD de mes (sin año, para evitar la firma "11 de diciembre de 2025")
        patron = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?!\s+de\s+\d{4})'
        
        matches = re.findall(patron, texto, re.IGNORECASE)
        
        for dia, mes_texto in matches:
            dia = int(dia)
            fecha_iso = self._convertir_fecha(dia, mes_texto)
            
            if fecha_iso:
                fecha_texto = f"{dia} de {mes_texto}"
                fechas.append((fecha_iso, fecha_texto, None))
        
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
        
        # Casos especiales catalanes
        nombre = re.sub(r'\bDe\b', 'de', nombre)
        nombre = re.sub(r'\bDel\b', 'del', nombre)
        nombre = re.sub(r'\bDels\b', 'dels', nombre)
        nombre = re.sub(r'\bDes\b', 'des', nombre)
        nombre = re.sub(r'\bDe La\b', 'de la', nombre)
        nombre = re.sub(r'\bDe Les\b', 'de les', nombre)
        nombre = re.sub(r"D'", "d'", nombre)
        nombre = re.sub(r"L'", "l'", nombre)
        nombre = re.sub(r'\bEl\b', 'el', nombre)
        nombre = re.sub(r'\bLa\b', 'la', nombre)
        nombre = re.sub(r'\bLes\b', 'les', nombre)
        nombre = re.sub(r'\bEls\b', 'els', nombre)
        
        # Artículos al inicio en mayúscula
        if nombre.lower().startswith("el "):
            nombre = "El" + nombre[2:]
        if nombre.lower().startswith("la "):
            nombre = "La" + nombre[2:]
        if nombre.lower().startswith("les "):
            nombre = "Les" + nombre[3:]
        if nombre.lower().startswith("els "):
            nombre = "Els" + nombre[3:]
        if nombre.lower().startswith("l'"):
            nombre = "L'" + nombre[2:]
        if nombre.lower().startswith("d'"):
            nombre = "D'" + nombre[2:]
        
        # Sant/Santa
        nombre = re.sub(r'\bSant\b', 'Sant', nombre)
        nombre = re.sub(r'\bSanta\b', 'Santa', nombre)
        
        return nombre


# Para testing
if __name__ == "__main__":
    import sys
    
    municipio = sys.argv[1] if len(sys.argv) > 1 else None
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    
    print(f"{'='*80}")
    print(f"🧪 TEST: Cataluña Locales - {municipio or 'TODOS'} {year}")
    print(f"{'='*80}\n")
    
    scraper = CatalunaLocalesScraper(year=year, municipio=municipio)
    festivos = scraper.scrape()
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN - CATALUÑA {year}")
    print(f"{'='*80}")
    print(f"Total festivos: {len(festivos)}\n")
    
    if festivos:
        print("📅 Festivos:")
        for f in festivos[:10]:
            print(f"   • {f['fecha']} - {f['descripcion']}")
        
        if len(festivos) > 10:
            print(f"\n   ... y {len(festivos) - 10} más")