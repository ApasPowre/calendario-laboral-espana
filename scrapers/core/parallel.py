"""
Utilidades para paralelizar peticiones HTTP en discovery
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Optional
import time


def parallel_requests(
    items: List[Any],
    worker_function: Callable,
    max_workers: int = 5,
    timeout: int = 30,
    verbose: bool = True
) -> List[Any]:
    """
    Ejecuta peticiones HTTP en paralelo
    
    Args:
        items: Lista de items a procesar (ej: años a buscar)
        worker_function: Función que procesa cada item
        max_workers: Número máximo de threads paralelos
        timeout: Timeout por request
        verbose: Mostrar progreso
        
    Returns:
        Lista de resultados (None si falló)
    """
    results = []
    
    if verbose:
        print(f"🔄 Procesando {len(items)} items con {max_workers} workers...")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_item = {
            executor.submit(worker_function, item): item 
            for item in items
        }
        
        # Recoger resultados a medida que terminan
        for future in as_completed(future_to_item, timeout=timeout):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
                
                if verbose and result:
                    print(f"   ✅ {item}: OK")
            except Exception as e:
                if verbose:
                    print(f"   ❌ {item}: {str(e)[:50]}")
                results.append(None)
    
    elapsed = time.time() - start_time
    
    if verbose:
        successful = len([r for r in results if r is not None])
        print(f"⏱️  Completado en {elapsed:.2f}s ({successful}/{len(items)} exitosos)")
    
    return results


def parallel_search_years(
    years: List[int],
    search_function: Callable,
    max_workers: int = 5
) -> dict:
    """
    Busca URLs para múltiples años en paralelo
    
    Args:
        years: Lista de años a buscar
        search_function: Función que busca URL para un año
        max_workers: Threads paralelos
        
    Returns:
        Dict {año: url} con resultados encontrados
    """
    def worker(year):
        try:
            url = search_function(year)
            return (year, url) if url else None
        except:
            return None
    
    results = parallel_requests(years, worker, max_workers=max_workers, verbose=True)
    
    # Convertir a dict, filtrando None
    return {year: url for year, url in results if year and url}
