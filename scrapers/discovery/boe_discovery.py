"""
BOE Discovery - Sistema híbrido mantenible
Prioriza URLs conocidas, con auto-discovery como fallback opcional
"""

import requests
from typing import Optional
import json


class BOEAutoDiscovery:
    """
    Sistema de descubrimiento de URLs del BOE
    Enfoque pragmático: URLs conocidas + auto-discovery opcional
    """
    
    # URLs conocidas (actualizar manualmente cada año)
    KNOWN_URLS = {
        2026: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-21667",
        2025: "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-21234",
        # Añadir nuevos años aquí cuando se publiquen
    }
    
    def __init__(self):
        self.base_url = "https://www.boe.es"
        self.api_url = f"{self.base_url}/datosabiertos/api"
    
    def get_url(self, year: int, try_auto_discovery: bool = False) -> str:
        """
        Obtiene la URL de la Resolución de festivos.
        
        Args:
            year: Año del calendario
            try_auto_discovery: Intentar auto-discovery si no está en KNOWN_URLS
            
        Returns:
            URL válida
            
        Raises:
            ValueError: Si no se encuentra URL
        """
        # 1. Primero, intentar URLs conocidas
        if year in self.KNOWN_URLS:
            url = self.KNOWN_URLS[year]
            print(f"✅ URL conocida para {year}: {url}")
            
            # Validar que sigue siendo válida
            if self.validate_url(url, year):
                return url
            else:
                print(f"⚠️  URL conocida no válida, buscando alternativa...")
        
        # 2. Si no está en conocidas y se permite, intentar auto-discovery
        if try_auto_discovery:
            print(f"🔍 Intentando auto-discovery para {year}...")
            url = self._try_auto_discovery(year)
            if url and self.validate_url(url, year):
                print(f"✅ URL encontrada por auto-discovery: {url}")
                print(f"💡 Tip: Añádela a KNOWN_URLS en boe_discovery.py")
                return url
        
        # 3. Si todo falla, dar instrucciones
        raise ValueError(
            f"\n❌ No se encontró URL para {year}.\n\n"
            f"Para añadirla manualmente:\n"
            f"1. Busca en https://www.boe.es 'fiestas laborales {year}'\n"
            f"2. Encuentra la Resolución (suele publicarse en octubre-noviembre del año {year-1})\n"
            f"3. Copia el ID del documento (ej: BOE-A-{year-1}-XXXXX)\n"
            f"4. Añade a scrapers/discovery/boe_discovery.py:\n"
            f"   {year}: 'https://www.boe.es/diario_boe/txt.php?id=BOE-A-{year-1}-XXXXX'\n"
        )
    
    def _try_auto_discovery(self, year: int) -> Optional[str]:
        """
        Intenta auto-discovery usando la API del BOE
        Best-effort, puede fallar sin romper nada
        """
        try:
            # Buscar en octubre del año anterior
            search_year = year - 1
            
            # Solo buscar en días específicos para no hacer 90 peticiones
            # La Resolución suele publicarse a final de mes
            dias_candidatos = [28, 29, 30, 31, 27, 26, 25]
            
            for mes in [10, 11, 12]:  # Oct, Nov, Dic
                for dia in dias_candidatos:
                    fecha = f"{search_year}{mes:02d}{dia:02d}"
                    api_url = f"{self.api_url}/boe/sumario/{fecha}"
                    
                    try:
                        response = requests.get(api_url, timeout=5, headers={'Accept': 'application/json'})
                        if response.status_code != 200:
                            continue
                        
                        data = response.json()
                        doc_id = self._search_in_json(data, year)
                        
                        if doc_id:
                            return f"{self.base_url}/diario_boe/txt.php?id={doc_id}"
                    
                    except:
                        continue
            
            return None
            
        except:
            return None
    
    def _search_in_json(self, data: dict, year: int) -> Optional[str]:
        """Busca el documento en el JSON del sumario"""
        # Convertir todo el JSON a string y buscar
        json_str = json.dumps(data, ensure_ascii=False).lower()
        
        # Buscar el patrón
        if f'fiestas laborales' in json_str and str(year) in json_str:
            # Intentar extraer el ID
            import re
            pattern = r'boe-a-\d{4}-\d{5}'
            matches = re.findall(pattern, json_str)
            if matches:
                return matches[0].upper()
        
        return None
    
    def validate_url(self, url: str, year: int) -> bool:
        """Valida que una URL contiene la Resolución de festivos"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.text.lower()
            
            # Verificar palabras clave
            required = ['fiestas laborales', str(year), 'año nuevo']
            
            return all(kw in content for kw in required)
            
        except:
            return False
    
    @classmethod
    def add_known_url(cls, year: int, url: str):
        """Añade una URL conocida (para uso programático)"""
        cls.KNOWN_URLS[year] = url
        print(f"✅ Añadida URL para {year}")


def main():
    """Test del discovery"""
    discovery = BOEAutoDiscovery()
    
    # Probar con 2026 (está en KNOWN_URLS)
    print("="*80)
    print("TEST 1: Año con URL conocida (2026)")
    print("="*80)
    try:
        url = discovery.get_url(2026)
        print(f"\n✅ Éxito: {url}\n")
    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
    
    # Probar con 2027 (no está en KNOWN_URLS)
    print("="*80)
    print("TEST 2: Año sin URL conocida (2027)")
    print("="*80)
    try:
        url = discovery.get_url(2027, try_auto_discovery=False)
        print(f"\n✅ Éxito: {url}\n")
    except ValueError as e:
        print(f"\n❌ Esperado: {e}\n")


if __name__ == "__main__":
    main()