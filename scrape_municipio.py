#!/usr/bin/env python3
"""
Scraper Unificado de Festivos Laborales
Combina festivos nacionales, autonómicos y locales para un municipio específico
"""

import sys
import json
from typing import List, Dict, Optional
from datetime import datetime


def scrape_festivos_completos(municipio: str, ccaa: str, year: int) -> Dict:
    """
    Extrae TODOS los festivos (nacionales + autonómicos + locales) para un municipio
    
    Args:
        municipio: Nombre del municipio
        ccaa: Comunidad autónoma ('madrid', 'canarias', etc)
        year: Año del calendario
        
    Returns:
        Dict con todos los festivos combinados
    """
    
    print("=" * 80)
    print(f"🗓️  CALENDARIO LABORAL COMPLETO - {municipio.upper()}, {ccaa.upper()} {year}")
    print("=" * 80)
    print()
    
    festivos_todos = []
    
    # 1. FESTIVOS NACIONALES (BOE)
    print("📌 PASO 1/3: Extrayendo festivos NACIONALES...")
    try:
        from scrapers.core.boe_scraper import BOEScraper
        
        scraper_boe = BOEScraper(year=year, ccaa=ccaa)
        festivos_nacionales = scraper_boe.scrape()
        
        if festivos_nacionales:
            festivos_todos.extend(festivos_nacionales)
            print(f"   ✅ {len(festivos_nacionales)} festivos nacionales extraídos")
        else:
            print(f"   ⚠️  No se encontraron festivos nacionales")
    except Exception as e:
        print(f"   ❌ Error extrayendo festivos nacionales: {e}")
    
    print()
    
    # 2. FESTIVOS AUTONÓMICOS
    print(f"📌 PASO 2/3: Extrayendo festivos AUTONÓMICOS de {ccaa.upper()}...")
    try:
        if ccaa.lower() == 'madrid':
            from scrapers.ccaa.madrid.autonomicos import MadridAutonomicosScraper
            scraper_auto = MadridAutonomicosScraper(year=year)
        elif ccaa.lower() == 'canarias':
            from scrapers.ccaa.canarias.autonomicos import CanariasAutonomicosScraper
            scraper_auto = CanariasAutonomicosScraper(year=year, municipio=municipio)
        else:
            print(f"   ❌ CCAA '{ccaa}' no soportada todavía")
            scraper_auto = None
        
        if scraper_auto:
            festivos_autonomicos = scraper_auto.scrape()
            
            if festivos_autonomicos:
                festivos_todos.extend(festivos_autonomicos)
                print(f"   ✅ {len(festivos_autonomicos)} festivos autonómicos extraídos")
            else:
                print(f"   ⚠️  No se encontraron festivos autonómicos")
    except Exception as e:
        print(f"   ❌ Error extrayendo festivos autonómicos: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. FESTIVOS LOCALES
    print(f"📌 PASO 3/3: Extrayendo festivos LOCALES de {municipio}...")
    try:
        if ccaa.lower() == 'madrid':
            from scrapers.ccaa.madrid.locales import MadridLocalesScraper
            scraper_local = MadridLocalesScraper(year=year, municipio=municipio)
        elif ccaa.lower() == 'canarias':
            from scrapers.ccaa.canarias.locales import CanariasLocalesScraper
            scraper_local = CanariasLocalesScraper(year=year, municipio=municipio)
        else:
            print(f"   ❌ CCAA '{ccaa}' no soportada todavía")
            scraper_local = None
        
        if scraper_local:
            festivos_locales = scraper_local.scrape()
            
            if festivos_locales:
                festivos_todos.extend(festivos_locales)
                print(f"   ✅ {len(festivos_locales)} festivos locales extraídos")
            else:
                print(f"   ⚠️  No se encontraron festivos locales para {municipio}")
    except Exception as e:
        print(f"   ❌ Error extrayendo festivos locales: {e}")
    
    print()
    print("=" * 80)
    
    # Eliminar duplicados por fecha (mantener el de mayor prioridad)
    # Prioridad: local > nacional > autonomico
    festivos_unicos = {}
    prioridad = {'local': 3, 'nacional': 2, 'autonomico': 1}
    
    for festivo in festivos_todos:
        fecha = festivo['fecha']
        tipo_actual = festivo.get('tipo', 'nacional')
        
        if fecha not in festivos_unicos:
            festivos_unicos[fecha] = festivo
        else:
            # Mantener el de mayor prioridad
            tipo_existente = festivos_unicos[fecha].get('tipo', 'nacional')
            if prioridad.get(tipo_actual, 0) > prioridad.get(tipo_existente, 0):
                festivos_unicos[fecha] = festivo
    
    # Convertir de vuelta a lista y ordenar
    festivos_todos = sorted(festivos_unicos.values(), key=lambda x: x['fecha'])
    
    # Gestionar sustituciones por CCAA
    if ccaa.lower() == 'canarias':
        # Canarias sustituye festivos nacionales que caen en domingo
        # Verificar si algún festivo autonómico marca sustitución
        festivos_sustituidos = set()
        
        # Para 2025: 12 octubre cae domingo → se sustituye por 30 mayo
        if year == 2025:
            festivos_sustituidos.add('2025-10-12')
        
        # Filtrar festivos sustituidos
        if festivos_sustituidos:
            festivos_todos = [f for f in festivos_todos if f['fecha'] not in festivos_sustituidos]
            print(f"   ℹ️  Festivos sustituidos eliminados: {len(festivos_sustituidos)}")

    # Resumen
    print(f"✅ TOTAL: {len(festivos_todos)} festivos laborales para {municipio}, {ccaa.upper()} en {year}")
    print("=" * 80)
    print()
    
    return {
        'municipio': municipio,
        'ccaa': ccaa,
        'year': year,
        'total_festivos': len(festivos_todos),
        'festivos': festivos_todos,
        'generado': datetime.now().isoformat()
    }


def guardar_resultados(data: Dict, municipio: str, ccaa: str, year: int):
    """Guarda resultados en JSON y Excel"""
    
    import pandas as pd
    
    # Nombre de archivo normalizado
    mun_norm = municipio.lower().replace(' ', '_')
    ccaa_norm = ccaa.lower()
    
    # JSON
    filename_json = f"data/{ccaa_norm}_{mun_norm}_completo_{year}.json"
    with open(filename_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 JSON guardado: {filename_json}")
    
    # Excel
    if data['festivos']:
        df = pd.DataFrame(data['festivos'])
        filename_excel = f"data/{ccaa_norm}_{mun_norm}_completo_{year}.xlsx"
        df.to_excel(filename_excel, index=False)
        print(f"💾 Excel guardado: {filename_excel}")
    
    print()


def mostrar_resumen(data: Dict):
    """Muestra resumen de festivos por tipo"""
    
    festivos = data['festivos']
    
    if not festivos:
        print("❌ No hay festivos para mostrar")
        return
    
    # Contar por tipo
    tipos = {}
    for f in festivos:
        tipo = f.get('tipo', 'desconocido')
        tipos[tipo] = tipos.get(tipo, 0) + 1
    
    print("📊 RESUMEN POR TIPO:")
    for tipo, count in sorted(tipos.items()):
        print(f"   • {tipo}: {count}")
    print()
    
    # Mostrar festivos
    print("📅 LISTADO DE FESTIVOS:")
    for f in festivos:
        fecha = f.get('fecha', 'N/A')
        desc = f.get('descripcion', 'Sin descripción')
        tipo = f.get('tipo', '').upper()
        print(f"   {fecha} - [{tipo:12}] {desc}")
    print()


def main():
    """Función principal"""
    
    # Parsear argumentos
    if len(sys.argv) < 4:
        print("❌ Uso: python scrape_municipio.py <municipio> <ccaa> <año>")
        print()
        print("Ejemplos:")
        print("  python scrape_municipio.py Madrid madrid 2026")
        print("  python scrape_municipio.py \"Santa Cruz de Tenerife\" canarias 2025")
        print()
        print("CCAA soportadas: madrid, canarias")
        sys.exit(1)
    
    municipio = sys.argv[1]
    ccaa = sys.argv[2]
    
    try:
        year = int(sys.argv[3])
    except ValueError:
        print(f"❌ Año inválido: {sys.argv[3]}")
        sys.exit(1)
    
    # Validar CCAA
    ccaa_soportadas = ['madrid', 'canarias']
    if ccaa.lower() not in ccaa_soportadas:
        print(f"❌ CCAA '{ccaa}' no soportada")
        print(f"   CCAA disponibles: {', '.join(ccaa_soportadas)}")
        sys.exit(1)
    
    # Ejecutar scraping
    try:
        data = scrape_festivos_completos(municipio, ccaa, year)
        
        # Guardar
        guardar_resultados(data, municipio, ccaa, year)
        
        # Mostrar resumen
        mostrar_resumen(data)
        
        print("✅ Proceso completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()