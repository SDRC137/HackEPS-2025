import json
import pandas as pd
import os
import requests
import time
import sys
import hashlib

# Add backend to path to import shared_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared_constants import VARIABLE_TO_OSM

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(lat, lon, osm_tags, radius):
    """Generates a unique hash for the query."""
    query_str = f"{lat}_{lon}_{sorted(osm_tags)}_{radius}"
    return hashlib.md5(query_str.encode()).hexdigest()

def load_from_cache(key):
    """Loads data from cache if exists."""
    cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def save_to_cache(key, data):
    """Saves data to cache."""
    cache_path = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to save cache: {e}")

import random

def generate_mock_points(lat, lon, count=3, radius=0.01):
    """Generates mock points around a center for demo purposes if API fails."""
    mock_points = []
    for i in range(count):
        # Random offset
        d_lat = (random.random() - 0.5) * radius
        d_lon = (random.random() - 0.5) * radius
        mock_points.append({
            "name": f"Ubicación Simulada {i+1}",
            "lat": lat + d_lat,
            "lon": lon + d_lon,
            "type": "mock",
            "id": 100000 + i
        })
    return mock_points

def search_places_overpass(lat, lon, osm_tags, radius=3000, limit=10):
    """
    Fetches POIs from OpenStreetMap using Overpass API with Caching.
    """
    # Check Cache
    cache_key = get_cache_key(lat, lon, osm_tags, radius)
    cached_data = load_from_cache(cache_key)
    if cached_data is not None:
        # print(f"Loaded from cache: {osm_tags}")
        return cached_data

    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://api.openstreetmap.fr/oapi/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://interpreter.lazus.de/"
    ]
    
    # Build the query union
    query_parts = []
    for tag in osm_tags:
        if '=' in tag:
            parts = tag.split('=', 1)
            if len(parts) == 2:
                key, value = parts
                selector = f'["{key}"="{value}"]'
            else:
                # Fallback if split fails unexpectedly
                key = tag
                selector = f'["{key}"]'
        else:
            key = tag
            selector = f'["{key}"]'
            
        # Query nodes, ways, and relations
        query_parts.append(f'node{selector}(around:{radius},{lat},{lon});')
        query_parts.append(f'way{selector}(around:{radius},{lat},{lon});')
        query_parts.append(f'relation{selector}(around:{radius},{lat},{lon});')
    
    query_string = "".join(query_parts)
    
    overpass_query = f"""
    [out:json][timeout:25];
    (
      {query_string}
    );
    out center {limit};
    """
    
    headers = {
        'User-Agent': 'HackEPS-2025-Agent/1.0'
    }

    for attempt in range(3):
        for server in overpass_servers:
            try:
                # Add a small delay to be nice to the public API
                time.sleep(0.5 * (attempt + 1)) 
                # print(f"Trying {server}...")
                response = requests.get(server, params={'data': overpass_query}, headers=headers, timeout=30)
                
                if response.status_code == 429:
                    print(f"Rate limit hit on {server}, waiting...")
                    time.sleep(2 * (attempt + 1))
                    continue
                    
                response.raise_for_status()
                data = response.json()
                
                results = []
                for element in data.get('elements', []):
                    # Get coordinates (center for ways/relations)
                    if 'lat' in element and 'lon' in element:
                        e_lat, e_lon = element['lat'], element['lon']
                    elif 'center' in element:
                        e_lat, e_lon = element['center']['lat'], element['center']['lon']
                    else:
                        continue
                        
                    tags = element.get('tags', {})
                    name = tags.get('name', 'Unknown Location')
                    
                    # Skip locations without a name
                    if name == 'Unknown Location':
                        continue
                    
                    # Determine a friendly type name
                    place_type = "poi"
                    for tag in osm_tags:
                        key = tag.split('=')[0]
                        if key in tags:
                            place_type = tags[key]
                            break
                    
                    results.append({
                        "name": name,
                        "lat": e_lat,
                        "lon": e_lon,
                        "type": place_type,
                        "id": element['id']
                    })
                    
                # Save to Cache
                save_to_cache(cache_key, results)
                return results
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching Overpass data from {server}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue
    
    print("Failed to fetch data from all Overpass servers. Using MOCK data for demo.")
    # Fallback to mock data so the demo doesn't fail completely
    mock_results = generate_mock_points(lat, lon, count=3)
    return mock_results

def get_important_locations(neighborhood_name, requirements_list, custom_osm_requirements=None):
    """
    Genera lista de POIs importantes basados en requisitos del usuario.
    requirements_list: lista de dicts {variable_name, value, weight}
    custom_osm_requirements: lista de dicts {search_term, osm_tag} (NUEVO para el Cliente Secreto)
    """
    # Load neighborhood data
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(base_path)
    neighborhoods_path = os.path.join(root_path, 'final_with_position.csv') # Usar final_with_position.csv que tiene centroides
    
    try:
        neighborhoods = pd.read_csv(neighborhoods_path)
    except FileNotFoundError:
        # Fallback o error
        print(f"Error: No se encuentra {neighborhoods_path}")
        return {}

    # Get neighborhood center
    # Normalizar nombre para búsqueda
    neighborhood_row = neighborhoods[neighborhoods['name'].str.lower() == neighborhood_name.lower()]
    if neighborhood_row.empty:
        print(f"Barrio {neighborhood_name} no encontrado en CSV de posiciones.")
        return {}
    
    neighborhood = neighborhood_row.iloc[0]
    center_lat = neighborhood.get('latitude_centroid', 0)
    center_lon = neighborhood.get('longitude_centroid', 0)

    important_positions = {}

    # 1. Process Standard Requirements (CSV Columns)
    for req in requirements_list:
        weight = req.get('weight')
        variable = req.get('variable_name')
        value = req.get('value')
        
        # Consideramos variables que estén mapeadas a OSM, independientemente del valor explícito
        # Si el usuario le da peso, le importa.
        if variable in VARIABLE_TO_OSM:
            osm_tags = VARIABLE_TO_OSM.get(variable)
            
            if osm_tags:
                # print(f"Fetching OSM data for {variable}...") # Verbose off
                found_places = search_places_overpass(center_lat, center_lon, osm_tags, limit=5) # Limit 5 para no saturar
                
                if found_places:
                    places_list = []
                    for place in found_places:
                        places_list.append({
                            "name": place['name'],
                            "lat": place['lat'],
                            "lon": place['lon'],
                            "type": place['type']
                        })
                    
                    important_positions[variable] = {
                        "count": len(found_places),
                        "locations": places_list,
                        "is_custom": False
                    }

    # 2. Process Custom/Secret Requirements (Dynamic OSM Tags)
    if custom_osm_requirements:
        print(f"Buscando requisitos especiales del Cliente Secreto: {len(custom_osm_requirements)}")
        for custom in custom_osm_requirements:
            term = custom.get("search_term")
            tag = custom.get("osm_tag")
            
            if tag:
                print(f"   - Buscando '{term}' ({tag})...")
                
                # Try searching with the specific tag first
                found_places = search_places_overpass(center_lat, center_lon, [tag], limit=5)
                
                if found_places:
                    places_list = []
                    for place in found_places:
                        places_list.append({
                            "name": place['name'],
                            "lat": place['lat'],
                            "lon": place['lon'],
                            "type": term # Usamos el término del usuario como tipo
                        })
                    
                    # Usamos el término de búsqueda como clave
                    important_positions[f"custom_{term}"] = {
                        "count": len(found_places),
                        "locations": places_list,
                        "is_custom": True,
                        "label": f"{term.title()} (Especial)"
                    }
                else:
                    print(f"   - No se encontraron '{term}' cerca.")

    return important_positions

def generate_map_data(neighborhood_name, requirements_json_path):
    # Load neighborhood data
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(base_path)
    neighborhoods_path = os.path.join(root_path, 'neighborhoods.csv')
    
    try:
        neighborhoods = pd.read_csv(neighborhoods_path)
    except FileNotFoundError:
        neighborhoods = pd.read_csv(r'c:\Users\javil\OneDrive\Documentos\GitHub\HackEPS-2025\neighborhoods.csv')

    # Get neighborhood center
    neighborhood = neighborhoods[neighborhoods['name'] == neighborhood_name].iloc[0]
    center_lat = neighborhood['latitude_centroid']
    center_lon = neighborhood['longitude_centroid']

    # Load requirements
    with open(requirements_json_path, 'r') as f:
        requirements = json.load(f)

    important_positions = {}

    # Process requirements
    for req in requirements['requirements']:
        weight = req.get('weight')
        variable = req.get('variable_name')
        
        # If weight is high (4 or 5), we consider it important
        if weight and weight >= 4:
            osm_tags = VARIABLE_TO_OSM.get(variable)
            
            if osm_tags:
                print(f"Fetching OSM data for {variable} (Weight: {weight})...")
                found_places = search_places_overpass(center_lat, center_lon, osm_tags, limit=20)
                
                print(f"Found {len(found_places)} sites for {variable}")
                
                places_list = []
                for place in found_places:
                    print(f"{place['type'].title()} ({place['name']}) coordinates: {place['lon']}, {place['lat']}")
                    places_list.append({
                        "name": place['name'],
                        "lat": place['lat'],
                        "lon": place['lon'],
                        "type": place['type']
                    })
                
                important_positions[variable] = {
                    "count": len(found_places),
                    "locations": places_list
                }
            else:
                # Variable is important but not a physical place (e.g. crime rate, income)
                pass

    output = {
        "neighborhood": {
            "name": neighborhood_name,
            "center": [center_lat, center_lon]
        },
        "important_positions": important_positions
    }

    return output

if __name__ == "__main__":
    # Example Usage
    dummy_reqs = {
        "requirements": [
            {"variable_name": "green_space_percentage", "value": "High", "weight": 5},
            {"variable_name": "restaurant_density", "value": "High", "weight": 4},
            {"variable_name": "total_crimes", "value": "Low", "weight": 5} # Should be ignored
        ]
    }
    
    req_path = "temp_requirements.json"
    with open(req_path, 'w') as f:
        json.dump(dummy_reqs, f)

    # Generate data for "Downtown"
    print("Generating map data for Downtown...")
    data = generate_map_data("Downtown", req_path)
    
    output_file = os.path.join(os.path.dirname(__file__), 'posiciones_importantes.json')
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Important positions generated at {output_file}")
    
    if os.path.exists(req_path):
        os.remove(req_path)
