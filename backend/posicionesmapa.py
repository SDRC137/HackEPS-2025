import json
import pandas as pd
import os
import requests
import time
import sys

# Add backend to path to import shared_constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared_constants import VARIABLE_TO_OSM

def search_places_overpass(lat, lon, osm_tags, radius=2000, limit=10):
    """
    Fetches POIs from OpenStreetMap using Overpass API.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Build the query union
    query_parts = []
    for tag in osm_tags:
        if '=' in tag:
            key, value = tag.split('=')
            selector = f'["{key}"="{value}"]'
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
    
    try:
        # Add a small delay to be nice to the public API
        time.sleep(1) 
        response = requests.get(overpass_url, params={'data': overpass_query})
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
            
        return results
        
    except Exception as e:
        print(f"Error fetching Overpass data: {e}")
        return []

def get_important_locations(neighborhood_name, requirements_list):
    """
    Genera lista de POIs importantes basados en requisitos del usuario.
    requirements_list: lista de dicts {variable_name, value, weight}
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

    # Process requirements
    for req in requirements_list:
        weight = req.get('weight')
        variable = req.get('variable_name')
        value = req.get('value')
        
        # Consideramos variables con valor definido (no null) y que estén mapeadas a OSM
        if value is not None and variable in VARIABLE_TO_OSM:
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
                        "locations": places_list
                    }

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
