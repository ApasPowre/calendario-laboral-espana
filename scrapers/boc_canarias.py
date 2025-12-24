"""
Scraper para el Boletín Oficial de Canarias (BOC)
Extrae festivos locales de los 88 municipios canarios
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import re

class BOCCanariasScraper:
    """
    Extrae festivos locales de Canarias del BOC
    """
    
    def __init__(self, year=2026):
        self.year = year
        self.base_url = "https://www.gobiernodecanarias.org/boc"
        self.festivos = []
        
    def get_boc_url_for_year(self):
        """Construye la URL del BOC para el año especificado"""
        if self.year == 2026:
            return "https://www.gobiernodecanarias.org/boc/2025/165/3029.html"
        elif self.year == 2025:
            return "https://www.gobiernodecanarias.org/boc/2024/238/3029.html"
        else:
            raise NotImplementedError(f"URL para año {self.year} no implementada aún")
    
    def fetch_boc_content(self, url):
        """Descarga el contenido del BOC con encoding correcto"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"❌ Error al descargar BOC: {e}")
            return None
    
    def parse_fecha(self, fecha_texto):
        """
        Convierte texto de fecha como '20 de enero' a formato ISO con el año
        """
        meses = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
        
        # Extraer día y mes del texto
        match = re.search(r'(\d+)\s+(?:de\s+)?(\w+)', fecha_texto)
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2).lower()
            mes = meses.get(mes_texto)
            
            if mes:
                try:
                    fecha = datetime(self.year, mes, dia)
                    return fecha.strftime('%Y-%m-%d')
                except ValueError:
                    return None
        
        return None
    
    def limpiar_municipio(self, nombre):
        """Limpia el nombre del municipio"""
        nombre = ' '.join(nombre.split())
        nombre = nombre.rstrip('.')
        return nombre.strip()
    
    def parse_festivos(self, html_content):
        """
        Parsea el HTML del BOC y extrae los festivos por municipio
        """
        soup = BeautifulSoup(html_content, 'lxml')
        festivos = []
        
        # Encontrar el contenido principal
        contenido = soup.get_text()
        
        # Buscar ANEXO
        anexo_pos = contenido.find("ANEXO")
        if anexo_pos == -1:
            print("❌ No se encontró el ANEXO en el documento")
            return []
        
        # Extraer solo la parte del anexo
        contenido_anexo = contenido[anexo_pos:]
        
        # Dividir en líneas
        lineas = contenido_anexo.split('\n')
        
        municipio_actual = None
        festivos_municipio_actual = []
        
        print("📊 Procesando líneas...")
        
        for i, linea in enumerate(lineas):
            linea = linea.strip()
            
            # Detectar municipio (línea con solo mayúsculas, espacios y punto final)
            if linea and linea.isupper() and linea.endswith('.') and ':' not in linea:
                # Si había un municipio anterior, guardarlo
                if municipio_actual and festivos_municipio_actual:
                    # Solo tomar los primeros 2 festivos
                    for fecha_texto, descripcion in festivos_municipio_actual[:2]:
                        fecha_iso = self.parse_fecha(fecha_texto)
                        if fecha_iso:
                            festivo = {
                                'municipio': municipio_actual,
                                'fecha': fecha_iso,
                                'fecha_texto': fecha_texto,
                                'descripcion': descripcion,
                                'tipo': 'local',
                                'ambito': 'municipal',
                                'ccaa': 'Canarias',
                                'provincia': self.detectar_provincia(municipio_actual),
                                'year': self.year
                            }
                            festivos.append(festivo)
                
                # Nuevo municipio
                municipio_actual = self.limpiar_municipio(linea)
                festivos_municipio_actual = []
            
            # Detectar festivo (línea con fecha: descripción)
            elif linea and ':' in linea and 'de' in linea:
                match = re.match(r'(\d+\s+(?:de\s+)?\w+):\s*(.+)', linea)
                if match:
                    fecha_texto = match.group(1)
                    descripcion = match.group(2).rstrip('.')
                    festivos_municipio_actual.append((fecha_texto, descripcion))
        
        # No olvidar el último municipio
        if municipio_actual and festivos_municipio_actual:
            for fecha_texto, descripcion in festivos_municipio_actual[:2]:
                fecha_iso = self.parse_fecha(fecha_texto)
                if fecha_iso:
                    festivo = {
                        'municipio': municipio_actual,
                        'fecha': fecha_iso,
                        'fecha_texto': fecha_texto,
                        'descripcion': descripcion,
                        'tipo': 'local',
                        'ambito': 'municipal',
                        'ccaa': 'Canarias',
                        'provincia': self.detectar_provincia(municipio_actual),
                        'year': self.year
                    }
                    festivos.append(festivo)
        
        municipios_unicos = set([f['municipio'] for f in festivos])
        print(f"✅ Encontrados {len(municipios_unicos)} municipios")
        
        return festivos
    
    def detectar_provincia(self, municipio):
        """
        Detecta la provincia del municipio
        """
        # Municipios de Santa Cruz de Tenerife
        tenerife = [
            'ADEJE', 'ARAFO', 'ARICO', 'ARONA', 'BUENAVISTA DEL NORTE',
            'CANDELARIA', 'FASNIA', 'GARACHICO', 'GRANADILLA DE ABONA',
            'GUÍA DE ISORA', 'GÜÍMAR', 'ICOD DE LOS VINOS', 'LA GUANCHA',
            'LA MATANZA DE ACENTEJO', 'LA OROTAVA', 'LA VICTORIA DE ACENTEJO',
            'LOS REALEJOS', 'LOS SILOS', 'PUERTO DE LA CRUZ', 'EL ROSARIO',
            'SAN CRISTÓBAL DE LA LAGUNA', 'SAN JUAN DE LA RAMBLA',
            'SAN MIGUEL DE ABONA', 'SANTA CRUZ DE TENERIFE', 'SANTA ÚRSULA',
            'SANTIAGO DEL TEIDE', 'EL SAUZAL', 'TACORONTE', 'EL TANQUE',
            'TEGUESTE', 'VILAFLOR DE CHASNA',
            # La Palma
            'BARLOVENTO', 'BREÑA ALTA', 'BREÑA BAJA', 'FUENCALIENTE DE LA PALMA',
            'GARAFÍA', 'LOS LLANOS DE ARIDANE', 'EL PASO', 'PUNTAGORDA',
            'PUNTALLANA', 'SAN ANDRÉS Y SAUCES', 'SANTA CRUZ DE LA PALMA',
            'TAZACORTE', 'TIJARAFE', 'VILLA DE MAZO',
            # La Gomera
            'AGULO', 'ALAJERÓ', 'HERMIGUA', 'SAN SEBASTIÁN DE LA GOMERA',
            'VALLE GRAN REY', 'VALLEHERMOSO',
            # El Hierro
            'LA FRONTERA', 'EL PINAR DE EL HIERRO', 'VALVERDE'
        ]
        
        if municipio in tenerife:
            return 'Santa Cruz de Tenerife'
        else:
            return 'Las Palmas'
    
    def scrape(self):
        """Ejecuta el scraping completo"""
        print(f"🔍 Iniciando scraping BOC Canarias para {self.year}...")
        
        url = self.get_boc_url_for_year()
        print(f"📄 URL: {url}")
        
        html = self.fetch_boc_content(url)
        
        if html:
            self.festivos = self.parse_festivos(html)
            municipios_unicos = len(set([f['municipio'] for f in self.festivos]))
            print(f"✅ Scraping completado:")
            print(f"   - {municipios_unicos} municipios")
            print(f"   - {len(self.festivos)} festivos extraídos")
        else:
            print("❌ Error en el scraping")
        
        return self.festivos
    
    def to_dataframe(self):
        """Convierte los festivos a DataFrame de pandas"""
        df = pd.DataFrame(self.festivos)
        if not df.empty:
            df = df.sort_values(['provincia', 'municipio', 'fecha'])
        return df
    
    def save_to_json(self, filepath):
        """Guarda los festivos en formato JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.festivos, f, ensure_ascii=False, indent=2)
        print(f"💾 Guardado en: {filepath}")
    
    def save_to_excel(self, filepath):
        """Guarda los festivos en formato Excel"""
        df = self.to_dataframe()
        df.to_excel(filepath, index=False)
        print(f"💾 Guardado en: {filepath}")
    
    def print_summary(self):
        """Imprime un resumen de los datos extraídos"""
        df = self.to_dataframe()
        if not df.empty:
            print("\n📊 RESUMEN:")
            print(f"   Total municipios: {df['municipio'].nunique()}")
            print(f"   Total festivos: {len(df)}")
            print(f"\n   Por provincia:")
            print(df.groupby('provincia')['municipio'].nunique())
            
            # Verificar municipios con festivos incorrectos
            festivos_por_municipio = df.groupby('municipio').size()
            incorrectos = festivos_por_municipio[festivos_por_municipio != 2]
            
            if len(incorrectos) > 0:
                print(f"\n⚠️  Municipios con número incorrecto de festivos:")
                for muni, count in incorrectos.items():
                    print(f"   {muni}: {count} festivos")
            else:
                print(f"\n✅ Todos los municipios tienen exactamente 2 festivos")
            
            print(f"\n🔝 Primeros 10 registros:")
            print(df.head(10).to_string(index=False))


if __name__ == "__main__":
    # Test del scraper
    scraper = BOCCanariasScraper(year=2026)
    festivos = scraper.scrape()
    
    if festivos:
        scraper.print_summary()
        
        # Guardar resultados
        scraper.save_to_json('data/canarias_2026.json')
        scraper.save_to_excel('data/canarias_2026.xlsx')