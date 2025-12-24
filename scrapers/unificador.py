"""
Unificador de Festivos - CLI para consultar calendarios laborales
Usa el orquestador para obtener datos actualizados de todas las fuentes oficiales
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

from scrapers.orchestrator import CalendarioOrchestrator


class CalendarioLaboral:
    """
    Interfaz de usuario para consultar el calendario laboral completo
    Usa el orquestador internamente para obtener datos actualizados
    """
    
    def __init__(self, year: int = 2026, ccaa: str = 'canarias'):
        self.year = year
        self.ccaa = ccaa
        self.orchestrator = None
        self.datos_cargados = False
    
    def cargar_datos(self, forzar_scraping: bool = False):
        """
        Carga los datos de festivos.
        
        Args:
            forzar_scraping: Si True, ejecuta scrapers. Si False, intenta cargar desde cache.
        """
        # Verificar si existe archivo combinado reciente
        cache_file = Path(f'data/combined/{self.ccaa}_{self.year}_completo.json')
        
        usar_cache = False
        if cache_file.exists() and not forzar_scraping:
            # Verificar si el cache tiene menos de 24 horas
            edad_cache = datetime.now().timestamp() - cache_file.stat().st_mtime
            if edad_cache < 86400:  # 24 horas
                usar_cache = True
                print(f"📦 Usando datos en cache ({cache_file})")
        
        if not usar_cache:
            print(f"🔄 Ejecutando scrapers para obtener datos actualizados...")
            self.orchestrator = CalendarioOrchestrator(year=self.year, ccaa=self.ccaa)
            self.orchestrator.run_all()
        else:
            # Cargar desde cache
            self.orchestrator = CalendarioOrchestrator(year=self.year, ccaa=self.ccaa)
            with open(cache_file, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                self.orchestrator.festivos_nacionales = datos['festivos']['nacionales']
                self.orchestrator.festivos_autonomicos = datos['festivos']['autonomicos']
                self.orchestrator.festivos_locales = datos['festivos']['locales']
        
        self.datos_cargados = True
    
    def listar_municipios(self):
        """Lista todos los municipios disponibles"""
        if not self.datos_cargados:
            self.cargar_datos()
        
        municipios = sorted(set([
            f['municipio'] 
            for f in self.orchestrator.festivos_locales
        ]))
        return municipios
    
    def buscar_municipio(self, termino_busqueda: str):
        """Busca municipios que coincidan con el término"""
        termino = termino_busqueda.upper()
        municipios = self.listar_municipios()
        coincidencias = [m for m in municipios if termino in m]
        return coincidencias
    
    def obtener_festivos_municipio(self, municipio: str):
        """Obtiene todos los festivos aplicables a un municipio"""
        if not self.datos_cargados:
            self.cargar_datos()
        
        municipio = municipio.upper()
        
        # Verificar que el municipio existe
        if municipio not in self.listar_municipios():
            print(f"❌ Municipio '{municipio}' no encontrado")
            coincidencias = self.buscar_municipio(municipio)
            if coincidencias:
                print(f"   ¿Quisiste decir? {', '.join(coincidencias[:5])}")
            return None
        
        return self.orchestrator.get_festivos_municipio(municipio)
    
    def generar_informe(self, municipio: str):
        """Genera un informe completo del calendario laboral de un municipio"""
        festivos = self.obtener_festivos_municipio(municipio)
        
        if not festivos:
            return None
        
        # Obtener datos del municipio
        festivo_local = next(
            (f for f in self.orchestrator.festivos_locales if f['municipio'] == municipio), 
            None
        )
        provincia = festivo_local.get('provincia', 'Desconocida') if festivo_local else 'Desconocida'
        
        # Separar por tipo
        nacionales = [f for f in festivos if f['tipo'] == 'nacional']
        autonomicos = [f for f in festivos if f['tipo'] == 'autonomico']
        locales = [f for f in festivos if f['tipo'] == 'local']
        
        informe = {
            'municipio': municipio,
            'provincia': provincia,
            'ccaa': self.ccaa.title(),
            'year': self.year,
            'total_festivos': len(festivos),
            'festivos_nacionales': len(nacionales),
            'festivos_autonomicos': len(autonomicos),
            'festivos_locales': len(locales),
            'festivos': festivos
        }
        
        return informe
    
    def imprimir_informe(self, municipio: str):
        """Imprime un informe formateado del calendario laboral"""
        informe = self.generar_informe(municipio)
        
        if not informe:
            return
        
        print("\n" + "="*80)
        print(f"📅 CALENDARIO LABORAL {self.year}")
        print("="*80)
        print(f"📍 Municipio: {informe['municipio']}")
        print(f"📍 Provincia: {informe['provincia']}")
        print(f"📍 Comunidad Autónoma: {informe['ccaa']}")
        print("-"*80)
        print(f"📊 RESUMEN:")
        print(f"   • Festivos nacionales: {informe['festivos_nacionales']}")
        print(f"   • Festivos autonómicos/insulares: {informe['festivos_autonomicos']}")
        print(f"   • Festivos locales: {informe['festivos_locales']}")
        print(f"   • TOTAL: {informe['total_festivos']} días festivos")
        print("-"*80)
        print(f"📆 LISTADO DE FESTIVOS:")
        print()
        
        for festivo in informe['festivos']:
            # Formatear fecha
            fecha_obj = datetime.strptime(festivo['fecha'], '%Y-%m-%d')
            dia_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][fecha_obj.weekday()]
            
            if festivo['tipo'] == 'nacional':
                tipo_emoji = "🇪🇸"
                tipo_texto = "Nacional"
            elif festivo['tipo'] == 'autonomico':
                tipo_emoji = "🏝️"
                tipo_texto = "Autonómico/Insular"
            else:
                tipo_emoji = "🏠"
                tipo_texto = "Local"
            
            print(f"   {tipo_emoji} {festivo['fecha']} ({dia_semana:9s}) - {festivo['descripcion']}")
            print(f"      └─ Tipo: {tipo_texto}")
        
        print("="*80)
        print()
    
    def exportar_excel(self, municipio: str, filepath: str = None):
        """Exporta el calendario de un municipio a Excel"""
        informe = self.generar_informe(municipio)
        
        if not informe:
            return False
        
        if not filepath:
            municipio_clean = municipio.replace(' ', '_')
            filepath = f'data/calendario_{municipio_clean}_{self.year}.xlsx'
        
        # Crear DataFrame
        df = pd.DataFrame(informe['festivos'])
        
        # Añadir día de la semana
        df['dia_semana'] = pd.to_datetime(df['fecha']).dt.day_name()
        
        # Reordenar columnas
        columnas_base = ['fecha', 'dia_semana', 'descripcion', 'tipo', 'ambito']
        columnas = [col for col in columnas_base if col in df.columns]
        
        # Añadir otras columnas disponibles
        otras_columnas = [col for col in df.columns if col not in columnas]
        columnas.extend(otras_columnas)
        
        df = df[columnas]
        
        # Guardar con metadata
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja principal
            df.to_excel(writer, sheet_name='Festivos', index=False)
            
            # Hoja de resumen
            resumen_data = {
                'Concepto': [
                    'Municipio', 'Provincia', 'Comunidad Autónoma', 'Año',
                    'Total festivos', 'Festivos nacionales', 
                    'Festivos autonómicos', 'Festivos locales'
                ],
                'Valor': [
                    informe['municipio'], informe['provincia'], informe['ccaa'],
                    informe['year'], informe['total_festivos'],
                    informe['festivos_nacionales'], informe['festivos_autonomicos'],
                    informe['festivos_locales']
                ]
            }
            resumen_df = pd.DataFrame(resumen_data)
            resumen_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        print(f"💾 Calendario guardado en: {filepath}")
        return True
    
    def exportar_todos_municipios(self, filepath: str = None):
        """Exporta un Excel con todos los municipios"""
        if not filepath:
            filepath = f'data/calendario_{self.ccaa}_todos_{self.year}.xlsx'
        
        municipios = self.listar_municipios()
        print(f"📊 Generando calendario para {len(municipios)} municipios...")
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for i, municipio in enumerate(municipios, 1):
                print(f"   {i}/{len(municipios)} - {municipio}")
                
                festivos = self.obtener_festivos_municipio(municipio)
                if festivos:
                    df = pd.DataFrame(festivos)
                    df['dia_semana'] = pd.to_datetime(df['fecha']).dt.day_name()
                    
                    # Nombre de hoja limitado a 31 caracteres
                    nombre_hoja = municipio[:31]
                    df.to_excel(writer, sheet_name=nombre_hoja, index=False)
        
        print(f"💾 Calendario de todos los municipios guardado en: {filepath}")


def main():
    """Función principal para uso por línea de comandos"""
    
    # Parsear argumentos
    year = 2026
    ccaa = 'canarias'
    
    if len(sys.argv) > 1:
        # Municipio especificado por línea de comandos
        municipio = ' '.join(sys.argv[1:])
        calendario = CalendarioLaboral(year=year, ccaa=ccaa)
        calendario.cargar_datos()
        calendario.imprimir_informe(municipio)
    else:
        # Modo interactivo
        calendario = CalendarioLaboral(year=year, ccaa=ccaa)
        
        print("\n🏝️  CALENDARIO LABORAL CANARIAS 2026")
        print("-" * 50)
        print("Cargando datos...")
        calendario.cargar_datos()
        
        while True:
            print("\nOpciones:")
            print("  1. Consultar municipio específico")
            print("  2. Listar todos los municipios")
            print("  3. Exportar municipio a Excel")
            print("  4. Exportar todos los municipios a Excel")
            print("  5. Refrescar datos (ejecutar scrapers)")
            print("  6. Salir")
            
            opcion = input("\nElige una opción (1-6): ").strip()
            
            if opcion == '1':
                municipio = input("Nombre del municipio: ").strip()
                calendario.imprimir_informe(municipio)
            
            elif opcion == '2':
                print("\n📋 MUNICIPIOS DISPONIBLES:")
                municipios = calendario.listar_municipios()
                for i, muni in enumerate(municipios, 1):
                    print(f"   {i:2d}. {muni}")
            
            elif opcion == '3':
                municipio = input("Nombre del municipio: ").strip()
                if calendario.exportar_excel(municipio):
                    print("✅ Exportación completada")
            
            elif opcion == '4':
                calendario.exportar_todos_municipios()
                print("✅ Exportación completada")
            
            elif opcion == '5':
                print("🔄 Refrescando datos...")
                calendario.cargar_datos(forzar_scraping=True)
                print("✅ Datos actualizados")
            
            elif opcion == '6':
                print("👋 ¡Hasta pronto!")
                break
            
            else:
                print("❌ Opción no válida")


if __name__ == "__main__":
    main()