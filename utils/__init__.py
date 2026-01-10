"""
Utilidades del proyecto
"""

from .normalizer import (
    MunicipioNormalizer,
    normalize_municipio,
    normalize_for_search,
    find_municipio,
    fuzzy_search_municipios
)

__all__ = [
    'MunicipioNormalizer',
    'normalize_municipio',
    'normalize_for_search',
    'find_municipio',
    'fuzzy_search_municipios'
]