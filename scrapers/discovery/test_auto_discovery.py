"""
Test real del auto-discovery - Intenta descubrir 2026 sin usar KNOWN_URLS
"""

from scrapers.discovery.boe_discovery import BOEAutoDiscovery

def test_auto_discovery():
    """Prueba el auto-discovery forzado"""
    discovery = BOEAutoDiscovery()
    
    print("="*80)
    print("🧪 TEST: Auto-discovery para 2026 (forzado, sin usar KNOWN_URLS)")
    print("="*80)
    
    # Intentar auto-discovery directamente
    url = discovery._try_auto_discovery(2026)
    
    if url:
        print(f"\n✅ Auto-discovery encontró URL: {url}")
        
        # Validar
        if discovery.validate_url(url, 2026):
            print(f"✅ URL validada correctamente")
        else:
            print(f"❌ URL encontrada pero no válida")
    else:
        print(f"\n❌ Auto-discovery NO encontró la URL")
        print(f"   Esto confirma que el auto-discovery no es confiable")
        print(f"   📋 Enfoque correcto: Mantener KNOWN_URLS actualizado manualmente")


if __name__ == "__main__":
    test_auto_discovery()