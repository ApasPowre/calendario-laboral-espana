# Issues Conocidos

## 🐛 Fuzzy Matching con Nombres Ambiguos

**Problema:** Cuando un nombre de municipio es ambiguo (ej: "Santa Cruz" en Canarias), el sistema puede sumar festivos de múltiples municipios.

**Ejemplo:**
- Input: "santa cruz" en Canarias
- Resultado: 3 festivos locales (mezcla de Santa Cruz de Tenerife + Santa Cruz de La Palma)
- Esperado: 2 festivos de un solo municipio

**Workaround:**
- Usar nombre completo: "santa cruz de tenerife" o "santa cruz de la palma"

**Fix Planificado:**
- Detectar múltiples matches con score alto (>80)
- Mostrar lista de opciones al usuario
- Requerir desambiguación
