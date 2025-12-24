# 📅 Calendario Laboral España

Sistema automatizado para obtener y consultar festivos laborales de todos los municipios de España desde fuentes oficiales (BOE y boletines autonómicos).

## 🎯 Objetivo

Crear la base de datos más completa y actualizada de festivos laborales en España, accesible mediante API REST y exportable a múltiples formatos.

## 📊 Cobertura

- ✅ 8,131 municipios de España
- ✅ Festivos nacionales, autonómicos, provinciales y locales
- ✅ Festivos insulares (Canarias, Baleares)
- ✅ Fuentes oficiales verificadas

## 🏗️ Arquitectura
```
BOE/Boletines Autonómicos → Scrapers → Base de Datos → API REST → Usuarios
```

## 🚀 Estado del proyecto

**Fase 1: MVP - En desarrollo**

- [ ] Scraper BOE (festivos nacionales)
- [ ] Scraper BOC Canarias (88 municipios)
- [ ] Base de datos estructurada
- [ ] Export a Google Sheets/Excel
- [ ] API REST básica

## 🛠️ Stack tecnológico

- Python 3.12+
- Beautiful Soup / Scrapy
- Pandas
- PostgreSQL / Supabase
- FastAPI (API REST)
- GitHub Actions (automatización)

## 📝 Licencia

Por determinar (considerando MIT u otra open source)

## 👥 Autores

Proyecto iniciado por Biplaza Asesoría
```

Guarda (Command + S).

## **Paso 10: Configurar requirements.txt**

Haz clic en `requirements.txt` y pega:
```
# Web scraping
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.1.0

# Data manipulation
pandas>=2.2.0
openpyxl>=3.1.0

# API (para fase 2)
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.6.0

# Database (para fase 2)
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0

# Utilities
python-dateutil>=2.8.2