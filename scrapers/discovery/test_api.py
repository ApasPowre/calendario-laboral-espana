"""
Test directo de la API del BOE para ver la estructura del JSON
"""

import requests
import json

# Sabemos que BOE-A-2025-21667 se publicó el 28 de octubre de 2025
fecha = "20251028"  # 28 de octubre de 2025

api_url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"

print(f"🔍 Consultando API del BOE: {api_url}\n")

try:
    response = requests.get(api_url, headers={'Accept': 'application/json'}, timeout=10)
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Guardar JSON completo para inspección
        with open('data/boe_sumario_20251028.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON guardado en: data/boe_sumario_20251028.json")
        print(f"\n📊 Estructura del JSON:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])  # Primeros 2000 chars
        
        # Buscar "fiestas laborales" en todo el JSON
        json_str = json.dumps(data, ensure_ascii=False).lower()
        if 'fiestas laborales' in json_str:
            print(f"\n✅ Encontrado 'fiestas laborales' en el JSON")
            
            # Encontrar contexto
            idx = json_str.find('fiestas laborales')
            context = json_str[max(0, idx-200):min(len(json_str), idx+200)]
            print(f"\nContexto:\n{context}")
        else:
            print(f"\n❌ NO encontrado 'fiestas laborales' en el JSON")
    
    else:
        print(f"❌ Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")