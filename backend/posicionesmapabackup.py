import json
import pandas as pd
import os
import requests
import time

# Mapping variables to OSM tags (Key=Value or just Key)
VARIABLE_TO_OSM = {
    "green_space_percentage": ["leisure=park", "landuse=recreation_ground", "leisure=garden", "natural=wood"],
    "gym_density": ["leisure=fitness_centre", "sport=fitness"],
    "culture_density": ["tourism=museum", "amenity=arts_centre", "amenity=theatre"],
    "local_businesses_density": ["shop=convenience", "shop=supermarket", "shop=bakery"],
    "restaurant_density": ["amenity=restaurant", "amenity=cafe"],
    "premium_stores_density": ["shop=department_store", "shop=clothes", "shop=jewelry"],
    "nightlife_density": ["amenity=bar", "amenity=nightclub", "amenity=pub"],
    "hospital_density": ["amenity=hospital", "amenity=clinic"],
    "transit_score": ["amenity=bus_station", "public_transport=station", "railway=station"],
    "proximity_to_sea": ["natural=beach"],
    "education_level_percentage": ["amenity=university", "amenity=college", "amenity=library"]
}

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
