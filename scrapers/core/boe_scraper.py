"""
BOE Scraper - Festivos nacionales de España
Extrae festivos desde el Boletín Oficial del Estado con parser robusto
Usa BOEAutoDiscovery para encontrar URLs automáticamente
"""

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re
from .base_scraper import BaseScraper
from scrapers.discovery.boe_discovery import BOEAutoDiscovery


class BOEScraper(BaseScraper):
    """
    Scraper para festivos nacionales desde el BOE
    Parsea la Resolución de fiestas laborales con múltiples estrategias
    """
    
    def __init__(self, year: int, ccaa: Optional[str] = None, municipio: Optional[str] = None):
        """
        Args:
            year: Año del calendario
            ccaa: Comunidad autónoma para filtrar (None = solo nacionales)
            municipio: Municipio para filtrar festivos insulares (Canarias)
        """
        super().__init__(year=year, ccaa=ccaa or 'nacional', tipo='nacionales')
        self.filter_ccaa = ccaa
        self.filter_municipio = municipio
        self.discovery = BOEAutoDiscovery()
    
    def get_source_url(self) -> str:
        """Devuelve URL del BOE usando discovery automático"""
        try:
            return self.discovery.get_url(self.year, try_auto_discovery=True)
        except ValueError as e:
            print(f"❌ Error: {e}")
            return ""
    
    def parse_festivos(self, content: str) -> List[Dict]:
        """
        Parsea festivos desde el contenido del BOE.
        Usa múltiples estrategias en orden de confiabilidad.
        """
        print("🔍 Parseando festivos...")
        
        # ESTRATEGIA 0: Tabla CCAA (MÁS PRECISO - para años con traslados)
        if self.year >= 2026:  # Para años futuros usar tabla
            print(f"   🔍 Intentando parsear tabla CCAA para {self.year}...")
            festivos_tabla_ccaa = self.parse_tabla_ccaa(content, self.filter_ccaa)
            if festivos_tabla_ccaa and len(festivos_tabla_ccaa) >= 9:
                print(f"   ✅ Método: Tabla CCAA ({len(festivos_tabla_ccaa)} festivos)")
                return festivos_tabla_ccaa
        
        # ESTRATEGIA 1: Patrones conocidos (más confiable para años antiguos)
        festivos_conocidos = self._parse_patrones_conocidos(content)
        if festivos_conocidos and len(festivos_conocidos) >= 9:
            print(f"   ✅ Método: Patrones conocidos ({len(festivos_conocidos)} festivos)")
            return festivos_conocidos
        
        # ESTRATEGIA 2: Tabla HTML
        festivos_tabla = self._parse_tabla_html(content)
        if festivos_tabla and len(festivos_tabla) >= 9:
            print(f"   ✅ Método: Tabla HTML ({len(festivos_tabla)} festivos)")
            return festivos_tabla
        
        # ESTRATEGIA 3: Texto con patrones
        festivos_texto = self._parse_texto_patrones(content)
        if festivos_texto and len(festivos_texto) >= 9:
            print(f"   ✅ Método: Patrones de texto ({len(festivos_texto)} festivos)")
            return festivos_texto
        
        # Si llegamos aquí, usar lo mejor que tengamos
        if festivos_conocidos:
            print(f"   ⚠️  Usando patrones conocidos ({len(festivos_conocidos)} festivos)")
            return festivos_conocidos
        
        return []
    
    def _parse_patrones_conocidos(self, content: str) -> List[Dict]:
        """
        Patrones conocidos de festivos nacionales.
        Busca Semana Santa con patrones específicos.
        """
        festivos = []
        
        # Festivos fijos
        festivos_fijos = [
            (1, 'enero', 'Año Nuevo', False),
            (6, 'enero', 'Epifanía del Señor', True),
            (1, 'mayo', 'Fiesta del Trabajo', False),
            (15, 'agosto', 'Asunción de la Virgen', True),
            (12, 'octubre', 'Fiesta Nacional de España', False),
            (1, 'noviembre', 'Todos los Santos', True),
            (6, 'diciembre', 'Día de la Constitución Española', False),
            (8, 'diciembre', 'Inmaculada Concepción', True),
            (25, 'diciembre', 'Natividad del Señor', False),
        ]
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Añadir festivos fijos
        for dia, mes_texto, descripcion, sustituible in festivos_fijos:
            mes = meses[mes_texto]
            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
            fecha_texto = f"{dia} de {mes_texto}"
            
            festivos.append({
                'fecha': fecha_iso,
                'fecha_texto': fecha_texto,
                'descripcion': descripcion,
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': sustituible,
                'year': self.year
            })
        
        # Buscar Semana Santa con patrones específicos
        content_lower = content.lower()
        
        # Patrón: ">6 Jueves Santo" o "6 Jueves Santo"
        patron_jueves = r'(\d{1,2})\s+jueves\s+santo'
        match_jueves = re.search(patron_jueves, content_lower)
        
        if match_jueves:
            dia = int(match_jueves.group(1))
            # Buscar el mes en contexto amplio
            idx = match_jueves.start()
            contexto = content_lower[max(0, idx-500):min(len(content_lower), idx+500)]
            
            # Determinar mes (buscar "abril", "marzo", etc.)
            mes = None
            for mes_nombre, mes_num in meses.items():
                if mes_nombre in contexto:
                    mes = mes_num
                    mes_texto = mes_nombre
                    break
            
            # Si no encontramos mes en contexto, asumir marzo/abril (Semana Santa)
            if mes is None:
                # Semana Santa suele ser marzo o abril
                if dia <= 15:
                    mes = 4  # abril
                    mes_texto = 'abril'
                else:
                    mes = 3  # marzo
                    mes_texto = 'marzo'
            
            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
            fecha_texto = f"{dia} de {mes_texto}"
            
            festivos.append({
                'fecha': fecha_iso,
                'fecha_texto': fecha_texto,
                'descripcion': 'Jueves Santo',
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': True,
                'year': self.year
            })
        
        # Patrón: ">7 Viernes Santo" o "7 Viernes Santo"
        patron_viernes = r'(\d{1,2})\s+viernes\s+santo'
        match_viernes = re.search(patron_viernes, content_lower)
        
        if match_viernes:
            dia = int(match_viernes.group(1))
            # Buscar el mes en contexto
            idx = match_viernes.start()
            contexto = content_lower[max(0, idx-500):min(len(content_lower), idx+500)]
            
            mes = None
            for mes_nombre, mes_num in meses.items():
                if mes_nombre in contexto:
                    mes = mes_num
                    mes_texto = mes_nombre
                    break
            
            if mes is None:
                # Viernes Santo = Jueves Santo + 1 día
                if dia <= 15:
                    mes = 4
                    mes_texto = 'abril'
                else:
                    mes = 3
                    mes_texto = 'marzo'
            
            fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
            fecha_texto = f"{dia} de {mes_texto}"
            
            festivos.append({
                'fecha': fecha_iso,
                'fecha_texto': fecha_texto,
                'descripcion': 'Viernes Santo',
                'tipo': 'nacional',
                'ambito': 'nacional',
                'sustituible': False,
                'year': self.year
            })
        
        return festivos
    
    def _parse_tabla_html(self, content: str) -> List[Dict]:
        """Parsea tabla HTML del BOE"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            festivos = []
            
            tablas = soup.find_all('table')
            
            for tabla in tablas:
                filas = tabla.find_all('tr')
                
                for fila in filas:
                    celdas = fila.find_all(['td', 'th'])
                    if len(celdas) < 2:
                        continue
                    
                    texto_fila = ' '.join([c.get_text(strip=True) for c in celdas])
                    
                    fecha_match = self._extraer_fecha_de_texto(texto_fila)
                    
                    if fecha_match:
                        fecha_iso, fecha_texto = fecha_match
                        
                        descripcion = texto_fila.replace(fecha_texto, '').strip()
                        descripcion = re.sub(r'^\d+\s*', '', descripcion)
                        descripcion = descripcion.strip('.,;:-')
                        
                        if descripcion and len(descripcion) > 3:
                            festivos.append({
                                'fecha': fecha_iso,
                                'fecha_texto': fecha_texto,
                                'descripcion': descripcion.title(),
                                'tipo': 'nacional',
                                'ambito': 'nacional',
                                'sustituible': False,
                                'year': self.year
                            })
            
            # Deduplicar
            fechas_vistas = set()
            festivos_unicos = []
            for f in festivos:
                if f['fecha'] not in fechas_vistas:
                    fechas_vistas.add(f['fecha'])
                    festivos_unicos.append(f)
            
            return festivos_unicos
            
        except Exception:
            return []
    
    def _parse_texto_patrones(self, content: str) -> List[Dict]:
        """Parsea texto buscando patrones de fecha + descripción"""
        try:
            festivos = []
            lineas = content.split('\n')
            
            for linea in lineas:
                fecha_match = self._extraer_fecha_de_texto(linea)
                
                if fecha_match:
                    fecha_iso, fecha_texto = fecha_match
                    
                    resto = linea.replace(fecha_texto, '')
                    resto = re.sub(r'^\d+\s*[.)\-:]\s*', '', resto)
                    resto = resto.strip('.,;:-()[]')
                    
                    if resto and len(resto) > 3:
                        descripcion = resto.split('.')[0][:100].strip()
                        
                        if descripcion:
                            festivos.append({
                                'fecha': fecha_iso,
                                'fecha_texto': fecha_texto,
                                'descripcion': descripcion.title(),
                                'tipo': 'nacional',
                                'ambito': 'nacional',
                                'sustituible': False,
                                'year': self.year
                            })
            
            # Deduplicar
            fechas_vistas = set()
            festivos_unicos = []
            for f in festivos:
                if f['fecha'] not in fechas_vistas:
                    fechas_vistas.add(f['fecha'])
                    festivos_unicos.append(f)
            
            return festivos_unicos
            
        except Exception:
            return []
    
    def _extraer_fecha_de_texto(self, texto: str) -> Optional[tuple]:
        """
        Extrae fecha de un texto en formato español.
        Retorna (fecha_iso, fecha_texto) o None
        """
        texto_lower = texto.lower()
        
        patron = r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        match = re.search(patron, texto_lower)
        
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2)
            fecha_texto = f"{dia} de {mes_texto}"
            
            meses = {
                'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
            }
            
            mes = meses.get(mes_texto)
            if mes:
                fecha_iso = f"{self.year}-{mes:02d}-{dia:02d}"
                return (fecha_iso, fecha_texto)
        
        return None

    def parse_tabla_ccaa(self, content: str, ccaa_filtro: Optional[str] = None) -> List[Dict]:
        """
        Parsea la tabla completa del BOE con todas las CCAA.
        
        Símbolos en tabla:
        - * (con guión abajo): Fiesta Nacional no sustituible
        - ** (con guiones abajo): Fiesta Nacional sin sustitución
        - *** (con guiones abajo): Fiesta de Comunidad Autónoma
        - (vacío): No aplica
        
        Args:
            content: HTML del BOE
            ccaa_filtro: Si se especifica, solo devuelve festivos de esa CCAA
        
        Returns:
            Lista de festivos con CCAA aplicables
        """
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("   ⚠️  No se encontró tabla en el BOE")
            return []
        
        # PASO 1: Extraer headers (CCAA)
        thead = table.find('thead')
        header_row = thead.find_all('tr')[1]  # Segunda fila tiene nombres CCAA
        headers = []
        
        for th in header_row.find_all('th'):
            ccaa_nombre = th.get_text(strip=True)
            headers.append(ccaa_nombre)
        
        # Mapeo nombre BOE → código interno
        CCAA_MAP = {
            'Andalucía': 'andalucia',
            'Aragón': 'aragon',
            'Asturias': 'asturias',
            'Illes Balears': 'baleares',
            'Canarias (1)': 'canarias',
            'Cantabria': 'cantabria',
            'Castilla y León': 'castilla_leon',
            'Castilla-La Mancha': 'castilla_la_mancha',
            'Cataluña (2)': 'cataluna',
            'Comunitat Valenciana': 'valencia',
            'Extremadura': 'extremadura',
            'Galicia': 'galicia',
            'Com. Madrid': 'madrid',  # ← CORREGIDO
            'Región Murcia': 'murcia',  # ← CORREGIDO
            'C. Foral Navarra': 'navarra',  # ← CORREGIDO
            'País Vasco': 'pais_vasco',
            'La Rioja': 'rioja',
            'Ciudad de Ceuta': 'ceuta',  # ← CORREGIDO
            'Ciudad de Melilla': 'melilla'  # ← CORREGIDO
        }
        
        headers_normalized = [CCAA_MAP.get(h, h.lower()) for h in headers]
        
        print(f"   📊 Tabla con {len(headers)} CCAA detectadas")
        
        # PASO 2: Parsear filas de festivos
        tbody = table.find('tbody')
        rows = tbody.find_all('tr')
        
        festivos = []
        mes_actual = None
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            
            if not cells:
                continue
            
            fecha_cell = cells[0].get_text(strip=True)
            
            # Detectar header de mes
            if len(cells) == 20 and not any(cells[i].get_text(strip=True) for i in range(1, 20)):
                mes_actual = fecha_cell
                continue
            
            # Parsear festivo
            match = re.match(r'(\d+)\s+(.+?)\.?$', fecha_cell)
            if not match:
                continue
            
            dia = int(match.group(1))
            descripcion = match.group(2).strip()
            
            # Construir fecha
            try:
                mes_num = self._mes_a_numero(mes_actual)
                fecha = f"{self.year:04d}-{mes_num:02d}-{dia:02d}"
            except:
                continue
            
            # PASO 3: Ver qué CCAA aplican
            ccaa_aplicables = []

            for i, ccaa in enumerate(headers_normalized):
                if i + 1 >= len(cells):
                    break
                
                # Obtener contenido de la celda
                celda = cells[i + 1].get_text(strip=True)
                
                # Si la celda tiene CUALQUIER contenido → festivo APLICA
                if celda:
                    ccaa_aplicables.append(ccaa)

            # Determinar tipo: si aplica a TODAS las CCAA = nacional, si solo a algunas = autonomico
            total_ccaa = len(headers_normalized)
            tipo_festivo = 'nacional' if len(ccaa_aplicables) == total_ccaa else 'autonomico'
            
            # PASO 4: Filtrar por CCAA si se especificó
            if ccaa_filtro:
                if ccaa_filtro.lower() not in ccaa_aplicables:
                    continue  # Este festivo no aplica a la CCAA solicitada
                # Si filtramos, solo queremos esta CCAA específica
                ccaa_aplicables = [ccaa_filtro.lower()]
            
            # Crear festivo(s)
            if tipo_festivo == 'nacional':
                # Nacional: crear un solo festivo para todas las CCAA
                festivo = {
                    'fecha': fecha,
                    'fecha_texto': f"{dia} de {mes_actual.lower()}",
                    'descripcion': descripcion,
                    'tipo': tipo_festivo,
                    'ambito': 'nacional',
                    'sustituible': False,
                    'year': self.year
                }
                festivos.append(festivo)
            else:
                # Autonómico: crear un festivo POR CADA CCAA aplicable
                for ccaa_codigo in ccaa_aplicables:
                    festivo = {
                        'fecha': fecha,
                        'fecha_texto': f"{dia} de {mes_actual.lower()}",
                        'descripcion': descripcion,
                        'tipo': tipo_festivo,
                        'ambito': ccaa_codigo,  # ← CCAA específica
                        'ccaa': ccaa_codigo,     # ← CAMPO ccaa
                        'sustituible': False,
                        'year': self.year
                    }
                    festivos.append(festivo)
        
        print(f"   ✅ Extraídos {len(festivos)} festivos de la tabla")
        
        if ccaa_filtro:
            print(f"   🎯 Filtrados para {ccaa_filtro}: {len(festivos)} festivos")
        
        return festivos


    def _mes_a_numero(self, mes_nombre: str) -> int:
        """Convierte nombre de mes a número"""
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        return meses.get(mes_nombre.lower(), 1)
    
    def parse_festivos_autonomicos(self, content: str, ccaa: str) -> List[Dict]:
        """
        Extrae festivos autonómicos de una CCAA específica del BOE
        
        Args:
            content: Contenido del BOE
            ccaa: Código de CCAA (madrid, canarias, valencia, etc)
        
        Returns:
            Lista de festivos autonómicos
        """
        
        festivos = []
        
        # Mapa de nombres de CCAA en el BOE
        ccaa_nombres = {
            'madrid': 'Comunidad de Madrid',
            'canarias': 'Comunidad Autónoma de Canarias',
            'valencia': 'Comunitat Valenciana',
            'cataluna': 'Comunidad Autónoma de Cataluña',
            'andalucia': 'Comunidad Autónoma de Andalucía',
            # Añadir más según se necesiten
        }
        
        nombre_ccaa = ccaa_nombres.get(ccaa.lower())
        if not nombre_ccaa:
            print(f"   ⚠️  CCAA '{ccaa}' no reconocida para extracción del BOE")
            return []
        
        print(f"   🔍 Extrayendo festivos autonómicos de: {nombre_ccaa}")
        
        # Buscar sección de la CCAA en el texto
        # Formato: "1. En la Comunidad Autónoma de ..., el Decreto ..."
        
        # Encontrar inicio de la sección
        patron_inicio = rf'\d+\.\s*En\s+la\s+{re.escape(nombre_ccaa)}'
        match_inicio = re.search(patron_inicio, content, re.IGNORECASE)
        
        if not match_inicio:
            print(f"   ❌ No se encontró sección para {nombre_ccaa}")
            return []
        
        # Extraer texto desde el inicio hasta la siguiente CCAA o final
        inicio = match_inicio.start()
        
        # Buscar siguiente CCAA
        patron_siguiente = r'\d+\.\s*En\s+la\s+Comunidad'
        siguiente_match = re.search(patron_siguiente, content[inicio+100:], re.IGNORECASE)
        
        if siguiente_match:
            fin = inicio + 100 + siguiente_match.start()
        else:
            fin = len(content)
        
        texto_ccaa = content[inicio:fin]
        
        print(f"   📄 Texto extraído: {len(texto_ccaa)} caracteres")
        
        # Extraer festivos específicos de la CCAA
        # Patrón para fechas como "2 de mayo" o "el 15 de septiembre"
        patron_fecha = r'(?:el\s+)?(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
        
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Para Canarias: buscar festivos insulares
        if ccaa.lower() == 'canarias':
            # Patrón específico para islas
            patron_insular = r'en\s+([^:]+):\s+el\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre),\s+(?:festividad de\s+)?(.+?)(?:;|\.|\n)'
            
            matches = re.finditer(patron_insular, texto_ccaa, re.IGNORECASE)
            
            for match in matches:
                isla = match.group(1).strip()
                dia = int(match.group(2))
                mes_texto = match.group(3).lower()
                descripcion = match.group(4).strip()
                
                mes = meses.get(mes_texto)
                if mes:
                    fecha = f"{self.year}-{mes:02d}-{dia:02d}"
                    
                    festivo = {
                        'fecha': fecha,
                        'fecha_texto': f"{dia} de {mes_texto}",
                        'descripcion': f"Festividad de {descripcion}",
                        'tipo': 'autonomico',
                        'ambito': 'insular',
                        'ccaa': 'Canarias',
                        'isla': isla,
                        'year': self.year
                    }
                    festivos.append(festivo)
                    print(f"   ✅ {isla}: {dia} de {mes_texto}")
        
        # Buscar festivo autonómico general (como Día de Madrid, Día de Canarias, etc)
        # Estos suelen estar mencionados como "sustituir" o "además"
        # Para Madrid: buscar "2 de mayo"
        # Para Canarias: buscar "30 de mayo, Día de Canarias"
        
        if ccaa.lower() == 'madrid':
            # Buscar "2 de mayo"
            if '2 de mayo' in texto_ccaa.lower():
                festivos.append({
                    'fecha': f'{self.year}-05-02',
                    'fecha_texto': '2 de mayo',
                    'descripcion': 'Fiesta de la Comunidad de Madrid',
                    'tipo': 'autonomico',
                    'ambito': 'autonomico',
                    'ccaa': 'Madrid',
                    'year': self.year
                })
                print(f"   ✅ 2 de mayo - Fiesta de la Comunidad de Madrid")
        
        elif ccaa.lower() == 'canarias':
            # Buscar "30 de mayo"
            if '30 de mayo' in texto_ccaa.lower():
                festivos.append({
                    'fecha': f'{self.year}-05-30',
                    'fecha_texto': '30 de mayo',
                    'descripcion': 'Día de Canarias',
                    'tipo': 'autonomico',
                    'ambito': 'autonomico',
                    'ccaa': 'Canarias',
                    'year': self.year
                })
                print(f"   ✅ 30 de mayo - Día de Canarias")
        
        return festivos

    def scrape(self) -> List[Dict]:
        """
        Ejecuta el proceso completo de scraping.
        Sobrescribe el método base para añadir festivos autonómicos.
        """
        print(f"\n{'='*80}")
        print(f"🔍 Iniciando scraping: {self.ccaa.upper()} - {self.tipo.upper()} - {self.year}")
        print(f"{'='*80}")
        
        # 1. Obtener URL
        url = self.get_source_url()
        if not url:
            print("❌ No se pudo obtener URL de la fuente")
            return []
        
        self.metadata['fuente'] = url
        
        # 2. Descargar contenido
        content = self.fetch_content(url)
        if not content:
            print("❌ No se pudo descargar el contenido")
            return []
        
        # 3. Parsear festivos NACIONALES
        festivos = self.parse_festivos(content)
        
        # 4. Si se especificó CCAA, añadir festivos AUTONÓMICOS del BOE
        # SOLO si la CCAA no tiene scraper específico
        if self.filter_ccaa and self.filter_ccaa.lower() != 'nacional':
    
            # CCAA con scrapers específicos del BOC (no usar BOE para autonómicos)
            CCAA_CON_SCRAPER_PROPIO = ['canarias', 'madrid']
    
            if self.filter_ccaa.lower() not in CCAA_CON_SCRAPER_PROPIO:
                festivos_auto = self.parse_festivos_autonomicos(content, self.filter_ccaa)
                festivos.extend(festivos_auto)
        
        # 5. Validar festivos
        festivos_validos = []
        for festivo in festivos:
            if self.validate_festivo(festivo):
                festivos_validos.append(festivo)
        
        self.festivos = festivos_validos
        self.metadata['num_festivos'] = len(self.festivos)
        
        # 6. Resumen
        print(f"\n✅ Scraping completado:")
        print(f"   • Festivos extraídos: {len(self.festivos)}")
        print(f"   • Fuente: {url}")
        print(f"{'='*80}\n")
        
        return self.festivos

def main():
    """Test del scraper"""
    import sys
    
    if len(sys.argv) > 1:
        try:
            year = int(sys.argv[1])
        except ValueError:
            print("❌ Año inválido. Uso: python -m scrapers.core.boe_scraper [año]")
            return
    else:
        year = 2026
    
    print("=" * 80)
    print(f"🧪 TEST: BOE Scraper - Festivos {year}")
    print("=" * 80)
    
    scraper_boe = BOEScraper(year=year, ccaa=ccaa)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        scraper.save_to_json(f"data/nacionales_{year}.json")
        scraper.save_to_excel(f"data/nacionales_{year}.xlsx")
        
        print(f"\n✅ Test completado para {year}")
    else:
        print(f"\n❌ No se pudieron extraer festivos para {year}")

if __name__ == "__main__":
    main()