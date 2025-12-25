"""
Scrapers para las Islas Canarias
Incluye festivos autonómicos y locales
"""

from .autonomicos import CanariasAutonomicosScraper
from .locales import CanariasLocalesScraper

__all__ = ['CanariasAutonomicosScraper', 'CanariasLocalesScraper']