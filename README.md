# 📅 Calendario Laboral España

**Generador automático de calendarios laborales personalizados por municipio en España.**

Extrae festivos nacionales, autonómicos y locales desde fuentes oficiales (BOE, boletines autonómicos) y genera calendarios visuales listos para imprimir o descargar.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://calendario-laboral-espana-yornkkgnnzizqn4omxfhr5.streamlit.app)

---

## 🎯 Características

✅ **6 Comunidades Autónomas** completas (Canarias, Madrid, Andalucía, Valencia, Baleares, Cataluña)  
✅ **2,572+ municipios** soportados con festivos exactos  
✅ **14 festivos precisos** por municipio (8 nacionales + 4-6 autonómicos + 2 locales)  
✅ **Auto-discovery** automático de URLs de boletines oficiales (80% CCAA)  
✅ **Parsing inteligente** de HTML, PDF, XML y YAML  
✅ **Generación de PDF** para imprimir con branding personalizable  
✅ **Deploy en Streamlit Cloud** - acceso público y gratuito  

---

## 📊 Cobertura Actual

| CCAA | Municipios | Provincias/Comarcas | Fuente Oficial | Auto-discovery | Formato |
|------|------------|---------------------|----------------|----------------|---------|
| **Canarias** | 88 | 2 islas principales | BOC | ✅ | YAML |
| **Madrid** | 181 | 1 provincia | BOCM | ✅ | PDF |
| **Andalucía** | 746 | 8 provincias | BOJA | ✅ | HTML |
| **Valencia** | 540+ | 3 provincias | DOGV | ✅ | PDF |
| **Baleares** | 67 | 4 islas | CAIB | ❌ (URLs predecibles) | HTML |
| **Cataluña** | 950+ | 42 comarcas | DOGC | ❌ | XML (Akoma Ntoso) |
| **TOTAL** | **2,572+** | **60+** | - | **80%** | - |

**Progreso:** 6/17 CCAA (35% de España)

---

## 🚀 Uso Rápido

### Opción 1: App Web (Recomendado)

Accede directamente a la aplicación desplegada:

👉 **[calendario-laboral-espana.streamlit.app](https://calendario-laboral-espana-yornkkgnnzizqn4omxfhr5.streamlit.app)**

1. Selecciona tu comunidad autónoma
2. Selecciona tu municipio
3. Elige el año
4. Genera el calendario visual
5. Descarga el PDF para imprimir

### Opción 2: Línea de Comandos
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/calendario-laboral-espana.git
cd calendario-laboral-espana

# Instalar dependencias
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generar calendario para un municipio
python scrape_municipio.py "BARCELONA" cataluna 2026

# Iniciar la app local
streamlit run app.py
```

---

## 🛠️ Arquitectura Técnica

### Scrapers Modulares

El proyecto utiliza scrapers especializados para cada fuente oficial:
```
scrapers/
├── core/
│   ├── base_scraper.py      # Clase base abstracta
│   └── boe_scraper.py        # Festivos nacionales + autonómicos
├── ccaa/
│   ├── canarias/
│   │   └── locales.py        # BOC - YAML parsing
│   ├── madrid/
│   │   └── locales.py        # BOCM - PDF parsing
│   ├── andalucia/
│   │   └── locales.py        # BOJA - HTML secuencial
│   ├── valencia/
│   │   └── locales.py        # DOGV - PDF multiidioma
│   ├── baleares/
│   │   └── locales.py        # CAIB - HTML tablas por islas
│   └── cataluna/
│       └── locales.py        # DOGC - XML Akoma Ntoso (curl)
└── discovery/
    └── ccaa/
        ├── canarias_discovery.py   # Auto-discovery BOC
        ├── madrid_discovery.py     # Auto-discovery BOCM
        ├── andalucia_discovery.py  # Auto-discovery BOJA
        └── valencia_discovery.py   # Auto-discovery DOGV
```

### Auto-discovery Inteligente

Los scrapers de Canarias, Madrid, Andalucía y Valencia incluyen **auto-discovery** que:

1. 🔍 Busca automáticamente en páginas oficiales
2. 📋 Extrae signaturas y enlaces
3. ✅ Valida contenido (provincias, municipios, año)
4. 💾 Cachea URLs descubiertas
5. 🔄 Actualiza automáticamente cada año

### Parsing Robusto

- **HTML:** BeautifulSoup con normalización de caracteres (ñ, ü, tildes, artículos catalanes)
- **PDF:** pypdf con extracción de texto y validación de estructura
- **XML:** ElementTree con HTML escapado (Akoma Ntoso estándar)
- **YAML:** Safe loading con manejo de encoding UTF-8
- **Formatos complejos:** Regex adaptativo para "14y17deagosto", "27 y 28 de agosto"
- **Tablas HTML:** Extracción estructurada por islas/provincias/comarcas
- **SSL problemático:** Fallback a curl para servidores con certificados antiguos

---

## 📝 Ejemplos de Salida

### Calendario Visual
```
Calendario generado: 14 festivos

┌─────────────────────────────────────────┐
│  CALENDARIO LABORAL 2026 - BARCELONA    │
│  Cataluña - Barcelonès                  │
└─────────────────────────────────────────┘

📅 FESTIVOS:
   2026-01-01 - [NACIONAL   ] Año Nuevo
   2026-01-06 - [NACIONAL   ] Epifanía del Señor
   2026-04-03 - [NACIONAL   ] Viernes Santo
   2026-04-06 - [AUTONOMICO ] Lunes de Pascua
   2026-05-01 - [NACIONAL   ] Fiesta del Trabajo
   2026-05-25 - [LOCAL      ] Festivo local de Barcelona
   2026-06-24 - [AUTONOMICO ] San Juan
   2026-08-15 - [NACIONAL   ] Asunción de la Virgen
   2026-09-11 - [AUTONOMICO ] Fiesta Nacional de Cataluña
   2026-09-24 - [LOCAL      ] Festivo local de Barcelona
   2026-10-12 - [NACIONAL   ] Fiesta Nacional de España
   2026-12-08 - [NACIONAL   ] Inmaculada Concepción
   2026-12-25 - [NACIONAL   ] Natividad del Señor
   2026-12-26 - [AUTONOMICO ] San Esteban
```

### JSON Output
```json
{
  "municipio": "Barcelona",
  "ccaa": "cataluna",
  "comarca": "Barcelonès",
  "year": 2026,
  "festivos": [
    {
      "fecha": "2026-01-01",
      "descripcion": "Año Nuevo",
      "tipo": "nacional"
    },
    {
      "fecha": "2026-05-25",
      "descripcion": "Festivo local de Barcelona",
      "tipo": "local",
      "municipio": "Barcelona",
      "comarca": "Barcelonès"
    }
  ]
}
```

---

## 🗺️ Roadmap

### Próximas CCAA (En orden de prioridad)

- [ ] **País Vasco** (251 municipios) - BOPV
- [ ] **Galicia** (313 municipios) - DOG
- [ ] **Castilla y León** (2,248 municipios) - BOCYL
- [ ] **Aragón** (731 municipios) - BOA
- [ ] **Murcia** (45 municipios) - BORM
- [ ] Resto de España...

### Features Planificadas

- [ ] Export a Google Calendar (ICS)
- [ ] Integración con Bitrix24 API
- [ ] Festivos personalizados de empresa
- [ ] Comparador entre municipios
- [ ] API REST pública
- [ ] Histórico de festivos (2020-2030)
- [ ] Auto-discovery para Baleares y Cataluña

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para añadir una nueva CCAA:

1. Crea el scraper en `scrapers/ccaa/nombre_ccaa/locales.py`
2. Implementa auto-discovery en `scrapers/discovery/ccaa/` (opcional)
3. Añade municipios en `config/nombre_ccaa_municipios.json`
4. Actualiza `CCAA_DISPONIBLES` en `app.py`
5. Añade tests y documentación

**Ver:** [CONTRIBUTING.md](CONTRIBUTING.md) para guía detallada

---

## 📄 Fuentes Oficiales

- **Nacional:** [BOE](https://www.boe.es/) - Boletín Oficial del Estado
- **Canarias:** [BOC](https://sede.gobcan.es/boc/) - Boletín Oficial de Canarias
- **Madrid:** [BOCM](https://www.bocm.es/) - Boletín Oficial de la Comunidad de Madrid
- **Andalucía:** [BOJA](https://www.juntadeandalucia.es/boja/) - Boletín Oficial de la Junta de Andalucía
- **Valencia:** [DOGV](https://dogv.gva.es/) - Diari Oficial de la Generalitat Valenciana
- **Baleares:** [CAIB](https://www.caib.es/sites/calendarilaboral/) - Govern de les Illes Balears
- **Cataluña:** [DOGC](https://dogc.gencat.cat/) - Diari Oficial de la Generalitat de Catalunya

---

## 📋 Requisitos

- Python 3.9+
- Dependencias: `streamlit`, `requests`, `beautifulsoup4`, `pypdf`, `pyyaml`, `pdfplumber`
- Sistema: `curl` (para Cataluña, generalmente preinstalado en Linux/Mac)
```bash
pip install -r requirements.txt
```

---

## 📜 Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles

---

## 👨‍💻 Autor

Desarrollado con ❤️ para facilitar la gestión de calendarios laborales en España.

**¿Preguntas o sugerencias?** Abre un [issue](https://github.com/tu-usuario/calendario-laboral-espana/issues)

---

## ⭐ Stats

![Municipios](https://img.shields.io/badge/Municipios-2572+-blue)
![CCAA](https://img.shields.io/badge/CCAA-6%2F17-green)
![Coverage](https://img.shields.io/badge/Cobertura-35%25-yellow)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)