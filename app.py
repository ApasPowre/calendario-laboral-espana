"""
Generador de Calendarios Laborales
Aplicación Streamlit para generar calendarios personalizados
"""

import streamlit as st
import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

# Añadir al path para imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils.calendar_generator import CalendarGenerator


# Configuración de la página
st.set_page_config(
    page_title="Generador de Calendarios Laborales",
    page_icon="📅",
    layout="wide"
)


def cargar_municipios(ccaa: str):
    """
    Carga municipios dinámicamente desde archivo de configuración
    
    Args:
        ccaa: Nombre de la CCAA (canarias, madrid, valencia, etc)
    
    Returns:
        Lista ordenada de municipios
    """
    import json
    import os
    
    # Buscar archivo de configuración (dos posibles nombres)
    archivos_posibles = [
        f'config/{ccaa}_municipios.json',
        f'config/{ccaa}_municipios_islas.json'  # Para Canarias
    ]
    
    for archivo in archivos_posibles:
        if os.path.exists(archivo):
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Si es estructura de islas (Canarias)
            if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
                municipios = set()
                for lista_municipios in data.values():
                    municipios.update(lista_municipios)
                return sorted(list(municipios))
            
            # Si es lista directa
            elif isinstance(data, list):
                return sorted(data)
            
            # Si es dict con clave "municipios"
            elif isinstance(data, dict) and 'municipios' in data:
                return sorted(data['municipios'])
    
    # Fallback si no existe archivo
    fallbacks = {
        'canarias': ['Arrecife', 'Santa Cruz de Tenerife', 'Las Palmas de Gran Canaria'],
        'madrid': ['Madrid', 'Alcalá de Henares', 'Alcobendas']
    }
    
    return fallbacks.get(ccaa, [f'Municipio de {ccaa.title()}'])


# Cargar municipios para CCAA disponibles
CCAA_DISPONIBLES = ['canarias', 'madrid', 'andalucia', 'valencia', 'baleares']  # ← Fácil añadir más

MUNICIPIOS = {
    ccaa: cargar_municipios(ccaa)
    for ccaa in CCAA_DISPONIBLES
}


def ejecutar_scraper(municipio: str, ccaa: str, year: int) -> dict:
    """Ejecuta el scraper y devuelve los datos SIN guardar archivos"""
    
    try:
        # Importar función de scraping
        from scrape_municipio import scrape_festivos_completos
        
        # Ejecutar scraping (devuelve dict con festivos)
        data = scrape_festivos_completos(municipio, ccaa, year)
        
        # NO guardar archivos - solo devolver datos en memoria
        return data
        
    except Exception as e:
        st.error(f"Error en el scraping: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

def main():
    # Header
    st.title("📅 Generador de Calendarios Laborales")
    st.markdown("Genera calendarios personalizados con festivos oficiales de España")
    
    st.markdown("---")
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # === DATOS BÁSICOS ===
        st.subheader("📍 Ubicación")
        
        # Selección de CCAA
        ccaa = st.selectbox(
            "Comunidad Autónoma",
            options=CCAA_DISPONIBLES,  # ← Usar la lista definida arriba
            format_func=lambda x: x.title()
        )
        
        # Selección de municipio
        municipio = st.selectbox(
            "Municipio",
            options=MUNICIPIOS[ccaa]
        )
        
        # Selección de año
        year = st.number_input(
            "Año",
            min_value=2025,
            max_value=2040,
            value=datetime.now().year,  # Año actual dinámico
            step=1
        )
        
        st.markdown("---")
        
        # === DATOS EMPRESA ===
        st.subheader("🏢 Empresa")
        
        empresa = st.text_input(
            "Nombre empresa *",
            placeholder="Ej: Biplaza Asesoría, S.L."
        )
        
        # Campos opcionales expandibles
        with st.expander("➕ Más información (opcional)"):
            direccion = st.text_area(
                "Dirección centro de trabajo",
                placeholder="Ej: Calle Obispo Rey Redondo 30, 1º\nSan Cristóbal de La Laguna"
            )
            
            convenio = st.text_input(
                "Convenio aplicable",
                placeholder="Ej: Gestorías Administrativas"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                num_patronal = st.text_input(
                    "Nº Patronal",
                    placeholder="38 1125814 10"
                )
            with col2:
                mutua = st.text_input(
                    "Mutua",
                    placeholder="Ibermutuamur"
                )
        
        st.markdown("---")
        
        # === HORARIO ===
        st.subheader("🕐 Horario laboral")
        
        # ¿Hay horario de verano?
        tiene_verano = st.checkbox("Horario diferenciado verano/invierno")
        
        if tiene_verano:
            # HORARIO INVIERNO
            st.markdown("**Horario invierno:**")
            horario_inv = st.text_area(
                "Descripción horario invierno",
                placeholder="Lunes a viernes: 9:00-13:00 / 17:00-20:00\nSábados: 9:00-13:30",
                key="horario_inv",
                height=80
            )
            
            # HORARIO VERANO
            st.markdown("**Horario verano:**")
            horario_ver = st.text_area(
                "Descripción horario verano",
                placeholder="Lunes a viernes: 8:00-15:00",
                key="horario_ver",
                height=80
            )
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_verano_inicio = st.date_input(
                    "Inicio verano",
                    value=None,
                    help="Ej: 15 de junio"
                )
            with col2:
                fecha_verano_fin = st.date_input(
                    "Fin verano",
                    value=None,
                    help="Ej: 15 de septiembre"
                )
        else:
            # HORARIO ÚNICO
            horario_inv = st.text_area(
                "Descripción horario",
                placeholder="Lunes a viernes: 9:00-13:00 / 17:00-20:00\nSábados: 9:00-13:30",
                height=100
            )
            horario_ver = None
            fecha_verano_inicio = None
            fecha_verano_fin = None
        
        st.markdown("---")
        
        # Botón generar
        generar = st.button("🎨 Generar Calendario", type="primary", use_container_width=True)
    
    # Área principal
    # Área principal
    if generar:
        # Validar datos requeridos
        if not empresa:
            st.error("❌ El nombre de la empresa es obligatorio")
            return
        
        if not horario_inv:
            st.error("❌ Debes especificar el horario laboral")
            return
        
        with st.spinner(f"⏳ Generando calendario para {municipio}, {ccaa.title()} {year}..."):
            
            # Ejecutar scraper
            data = ejecutar_scraper(municipio, ccaa, year)
            
            if data:
                st.success(f"✅ Calendario generado: {data['total_festivos']} festivos")
                
                # Preparar datos de horario
                horario_data = {
                    'tiene_verano': tiene_verano,
                    'invierno': horario_inv,
                    'verano': horario_ver if tiene_verano else None,
                    'verano_inicio': fecha_verano_inicio if tiene_verano else None,
                    'verano_fin': fecha_verano_fin if tiene_verano else None
                }
                
                # Preparar datos opcionales
                datos_opcionales = {
                    'direccion': direccion if direccion else None,
                    'convenio': convenio if convenio else None,
                    'num_patronal': num_patronal if num_patronal else None,
                    'mutua': mutua if mutua else None
                }
                
                # Generar HTML del calendario
                generator = CalendarGenerator(
                    year=year,
                    festivos=data['festivos'],
                    municipio=municipio,
                    ccaa=ccaa,
                    empresa=empresa,
                    horario=horario_data,
                    datos_opcionales=datos_opcionales
                )
                
                html = generator.generate_html()
                
                # Agregar script para auto-print
                html_con_print = html.replace('</body>', '''
                    <script>
                        window.onload = function() {
                            setTimeout(function() {
                                window.print();
                            }, 500);
                        };
                    </script>
                    </body>
                ''')
                
                # Botón para generar PDF (color corporativo)
                st.markdown("""
                    <style>
                    div.stDownloadButton > button {
                        background-color: #F1AB6C !important;
                        color: white !important;
                        border: none !important;
                        padding: 12px 24px !important;
                        font-weight: bold !important;
                        font-size: 16px !important;
                    }
                    div.stDownloadButton > button:hover {
                        background-color: #e09a5a !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    st.download_button(
                        label="📄 Generar PDF para imprimir",
                        data=html_con_print,
                        file_name=f"calendario_{ccaa}_{municipio.lower().replace(' ', '_')}_{year}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
                    st.info("💡 El archivo se descargará. Al abrirlo, tu navegador mostrará automáticamente el diálogo para guardar como PDF.", icon="ℹ️")
                
                # Tabs para visualizar
                tab1, tab2 = st.tabs(["📅 Preview", "📊 Datos"])
                
                with tab1:
                    # Mostrar preview del calendario
                    st.components.v1.html(html, height=1600, scrolling=True)
                
                with tab2:
                    # Mostrar tabla de festivos
                    st.subheader("📋 Listado de festivos")
                    
                    import pandas as pd
                    df = pd.DataFrame(data['festivos'])
                    df = df[['fecha', 'descripcion', 'tipo']]
                    df.columns = ['Fecha', 'Descripción', 'Tipo']
                    
                    st.dataframe(df, use_container_width=True, height=400)
                    
                    # Resumen por tipo
                    st.subheader("📊 Resumen por tipo")
                    resumen = df['Tipo'].value_counts()
                    st.bar_chart(resumen)
            else:
                st.error("❌ No se pudo generar el calendario. Revisa los logs.")
    
    else:
        # Instrucciones iniciales
        st.info("👈 Configura los parámetros en la barra lateral y haz clic en 'Generar Calendario'")
        
        # Características
        st.markdown("### ✨ Características")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📅 Fuentes oficiales**
            - BOE (nacionales)
            - BOCM / BOC (autonómicos)
            - Festivos locales
            """)
        
        with col2:
            st.markdown("""
            **🎨 Personalizable**
            - Logo empresa
            - Horario laboral
            - Diseño profesional
            """)
        
        with col3:
            st.markdown("""
            **📥 Múltiples formatos**
            - HTML interactivo
            - Impresión a PDF
            - Listo para publicar
            """)


if __name__ == "__main__":
    main()

