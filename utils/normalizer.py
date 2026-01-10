"""
Normalizador de nombres de municipios españoles
Resuelve inconsistencias de mayúsculas, artículos, comas y variantes regionales
"""

import re
import unicodedata
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️  rapidfuzz no disponible, usando difflib (más lento)")


class MunicipioNormalizer:
    """Normalizador inteligente de nombres de municipios"""
    
    # Artículos y preposiciones en diferentes idiomas
    ARTICULOS = {
        'es': ['el', 'la', 'los', 'las'],
        'ca': ['el', 'la', 'els', 'les', "l'", "d'"],
        'va': ['el', 'la', 'els', 'les', "l'", "d'"],
        'gl': ['o', 'a', 'os', 'as'],
        'eu': [],  # Euskera no usa artículos definidos de la misma forma
    }
    
    PREPOSICIONES = ['de', 'del', 'dels', 'des', 'da', 'do']
    
    # Variantes comunes
    VARIANTES = {
        'sant': 'san',
        'santa': 'santa',
        'santo': 'san',
    }
    
    @staticmethod
    def remove_accents(text: str) -> str:
        """Elimina acentos y diacríticos manteniendo ñ y ç"""
        # Normalizar a NFD (descomponer caracteres)
        nfd = unicodedata.normalize('NFD', text)
        
        # Filtrar solo marcas diacríticas, pero mantener ñ y ç
        result = ''.join(
            char for char in nfd
            if unicodedata.category(char) != 'Mn' or char in ['ñ', 'Ñ', 'ç', 'Ç']
        )
        
        return unicodedata.normalize('NFC', result)
    
    @staticmethod
    def resolve_comma_inversion(nombre: str) -> str:
        """
        Resuelve inversión de artículos con coma
        "Ejido, el" -> "El Ejido"
        "Palma de Mallorca, la" -> "La Palma de Mallorca"
        """
        # Patrón: texto + coma + espacio + artículo
        pattern = r'^(.+?),\s+(el|la|los|las|els|les|l\'|d\')$'
        match = re.match(pattern, nombre, re.IGNORECASE)
        
        if match:
            base = match.group(1).strip()
            articulo = match.group(2).strip()
            
            # Capitalizar artículo al inicio
            articulo_cap = articulo.capitalize()
            if articulo.lower() in ["l'", "d'"]:
                # Mantener apóstrofe pegado
                return f"{articulo_cap}{base}"
            else:
                return f"{articulo_cap} {base}"
        
        return nombre
    
    @classmethod
    def normalize_basic(cls, nombre: str) -> str:
        """
        Normalización básica sin perder información
        - Title Case inteligente
        - Artículos y preposiciones en minúscula
        - Mantiene estructura original
        """
        if not nombre:
            return ""
        
        # Resolver inversión de coma primero
        nombre = cls.resolve_comma_inversion(nombre.strip())
        
        # Pre-procesar apóstrofes catalanes: dividir L'Hospitalet en L' + Hospitalet
        # para que el title case funcione correctamente
        nombre = re.sub(r"(L|D)'(\w)", lambda m: f"{m.group(1)}' {m.group(2)}", nombre, flags=re.IGNORECASE)
        
        # Title case
        palabras = nombre.split()
        resultado = []
        
        for i, palabra in enumerate(palabras):
            palabra_lower = palabra.lower()
            
            # Primera palabra siempre capitalizada
            if i == 0:
                resultado.append(palabra.capitalize())
            # Artículos y preposiciones en minúscula
            elif palabra_lower in cls.ARTICULOS['es'] + cls.ARTICULOS['ca'] + cls.PREPOSICIONES:
                resultado.append(palabra_lower)
            # Apóstrofes solos (L', D')
            elif palabra in ["L'", "l'", "D'", "d'"]:
                resultado.append(palabra.capitalize())
            # Resto capitalizado
            else:
                resultado.append(palabra.capitalize())
        
        # Unir y re-pegar apóstrofes
        nombre_normalizado = ' '.join(resultado)
        nombre_normalizado = re.sub(r"(L|D)'\s+", lambda m: f"{m.group(1)}'", nombre_normalizado)
        
        # Corregir casos especiales
        nombre_normalizado = re.sub(r'\bDe La\b', 'de la', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bDe Les\b', 'de les', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bDe Els\b', 'de els', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bDel\b', 'del', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bDels\b', 'dels', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bDes\b', 'des', nombre_normalizado)
        
        # Sant/Santa
        nombre_normalizado = re.sub(r'\bSant\b', 'Sant', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bSanta\b', 'Santa', nombre_normalizado)
        nombre_normalizado = re.sub(r'\bSan\b', 'San', nombre_normalizado)
        
        return nombre_normalizado
    
    @classmethod
    def normalize_search(cls, nombre: str) -> str:
        """
        Normalización agresiva para búsqueda/comparación
        - Sin acentos (excepto ñ/ç)
        - Lowercase
        - Sin artículos iniciales
        - Sin espacios extra
        """
        if not nombre:
            return ""
        
        # Resolver inversión primero
        nombre = cls.resolve_comma_inversion(nombre.strip())
        
        # Lowercase
        nombre = nombre.lower()
        
        # Eliminar acentos
        nombre = cls.remove_accents(nombre)
        
        # Eliminar artículos iniciales
        for articulo in cls.ARTICULOS['es'] + cls.ARTICULOS['ca']:
            pattern = f"^{re.escape(articulo)}\\s+"
            nombre = re.sub(pattern, '', nombre, flags=re.IGNORECASE)
        
        # Normalizar espacios
        nombre = re.sub(r'\s+', ' ', nombre).strip()
        
        return nombre
    
    @classmethod
    def fuzzy_match(
        cls, 
        query: str, 
        candidates: List[str], 
        threshold: int = 80,
        limit: int = 5
    ) -> List[Tuple[str, int]]:
        """
        Encuentra los mejores matches usando fuzzy matching
        
        Args:
            query: Nombre a buscar
            candidates: Lista de candidatos
            threshold: Score mínimo (0-100)
            limit: Número máximo de resultados
            
        Returns:
            Lista de tuplas (candidato, score) ordenadas por score descendente
        """
        if not query or not candidates:
            return []
        
        # Normalizar query para búsqueda
        query_normalized = cls.normalize_search(query)
        
        if RAPIDFUZZ_AVAILABLE:
            # Usar rapidfuzz (más rápido y preciso)
            results = process.extract(
                query_normalized,
                candidates,
                scorer=fuzz.ratio,
                limit=limit
            )
            # Filtrar por threshold
            return [(match[0], match[1]) for match in results if match[1] >= threshold]
        else:
            # Fallback a difflib
            scores = []
            for candidate in candidates:
                candidate_normalized = cls.normalize_search(candidate)
                score = int(SequenceMatcher(None, query_normalized, candidate_normalized).ratio() * 100)
                if score >= threshold:
                    scores.append((candidate, score))
            
            # Ordenar por score descendente
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:limit]
    
    @classmethod
    def find_best_match(
        cls,
        query: str,
        candidates: List[str],
        threshold: int = 80
    ) -> Optional[str]:
        """
        Encuentra el mejor match único
        
        Returns:
            Mejor candidato o None si no hay match suficientemente bueno
        """
        matches = cls.fuzzy_match(query, candidates, threshold=threshold, limit=1)
        
        if matches:
            return matches[0][0]
        
        return None
    
    @classmethod
    def are_equivalent(cls, nombre1: str, nombre2: str, threshold: int = 90) -> bool:
        """
        Determina si dos nombres son equivalentes
        
        Args:
            nombre1: Primer nombre
            nombre2: Segundo nombre
            threshold: Score mínimo para considerar equivalencia
            
        Returns:
            True si son equivalentes
        """
        if not nombre1 or not nombre2:
            return False
        
        # Normalización para comparación
        norm1 = cls.normalize_search(nombre1)
        norm2 = cls.normalize_search(nombre2)
        
        # Comparación exacta
        if norm1 == norm2:
            return True
        
        # Fuzzy comparison
        if RAPIDFUZZ_AVAILABLE:
            score = fuzz.ratio(norm1, norm2)
        else:
            score = int(SequenceMatcher(None, norm1, norm2).ratio() * 100)
        
        return score >= threshold


# Funciones de conveniencia
def normalize_municipio(nombre: str) -> str:
    """Normalización básica de nombre de municipio"""
    return MunicipioNormalizer.normalize_basic(nombre)


def normalize_for_search(nombre: str) -> str:
    """Normalización agresiva para búsqueda"""
    return MunicipioNormalizer.normalize_search(nombre)


def find_municipio(query: str, municipios: List[str], threshold: int = 80) -> Optional[str]:
    """Encuentra el municipio que mejor hace match con la query"""
    return MunicipioNormalizer.find_best_match(query, municipios, threshold)


def fuzzy_search_municipios(query: str, municipios: List[str], threshold: int = 80, limit: int = 5) -> List[Tuple[str, int]]:
    """Busca municipios con fuzzy matching"""
    return MunicipioNormalizer.fuzzy_match(query, municipios, threshold, limit)


# Tests unitarios
if __name__ == "__main__":
    print("🧪 TESTS DEL NORMALIZADOR\n")
    print("="*80)
    
    # Test 1: Inversión de coma
    print("\n1️⃣ Test: Inversión de coma")
    casos = [
        "Ejido, el",
        "Palma de Mallorca, la",
        "Roca del Vallès, La",
        "Hospital de Llobregat, L'",
    ]
    for caso in casos:
        resultado = MunicipioNormalizer.resolve_comma_inversion(caso)
        print(f"   '{caso}' -> '{resultado}'")
    
    # Test 2: Normalización básica
    print("\n2️⃣ Test: Normalización básica")
    casos = [
        "BARCELONA",
        "el ejido",
        "L'HOSPITALET DE LLOBREGAT",
        "sant cugat del vallès",
    ]
    for caso in casos:
        resultado = normalize_municipio(caso)
        print(f"   '{caso}' -> '{resultado}'")
    
    # Test 3: Normalización para búsqueda
    print("\n3️⃣ Test: Normalización para búsqueda")
    casos = [
        "El Ejido",
        "L'Hospitalet de Llobregat",
        "Sant Cugat del Vallès",
        "Palma de Mallorca",
    ]
    for caso in casos:
        resultado = normalize_for_search(caso)
        print(f"   '{caso}' -> '{resultado}'")
    
    # Test 4: Fuzzy matching
    print("\n4️⃣ Test: Fuzzy matching")
    municipios = [
        "Barcelona",
        "El Ejido",
        "L'Hospitalet de Llobregat",
        "Sant Cugat del Vallès",
        "Palma de Mallorca",
    ]
    
    queries = [
        "barcelona",
        "ejido",
        "hospitalet llobregat",
        "san cugat valles",
        "palma mallorca",
    ]
    
    for query in queries:
        resultado = find_municipio(query, municipios, threshold=70)
        print(f"   '{query}' -> '{resultado}'")
    
    # Test 5: Equivalencia
    print("\n5️⃣ Test: Equivalencia")
    pares = [
        ("Barcelona", "BARCELONA"),
        ("El Ejido", "Ejido, el"),
        ("L'Hospitalet", "Hospitalet de Llobregat, l'"),
        ("Sant Cugat", "San Cugat"),
    ]
    
    for nombre1, nombre2 in pares:
        equiv = MunicipioNormalizer.are_equivalent(nombre1, nombre2, threshold=80)
        print(f"   '{nombre1}' ≈ '{nombre2}': {equiv}")
    
    print("\n" + "="*80)
    print("✅ Tests completados\n")