
# Shared constants for the backend agents

CATEGORY_SCALE = ["Extremely_Low", "Low", "Moderate", "High", "Extremely_High"]

# Possible categorical values for air_quality_index
AIR_QUALITY_VALUES = [
    "Good", "Moderate", "Moderate/Poor", "Good/Moderate"
]

# Column names from final.csv header
COLUMNS = [
    "median_household_income","surface_area","population_density","average_age","families_with_children_percentage",
    "rent_vs_own_percentage","unemployment_rate","education_level_percentage","total_crimes","violent_ratio",
    "property_ratio","violent_vs_property_ratio","crime_trend_slope","crimes_per_100_people","median_rent",
    "median_home_price","average_housing_age","air_quality_index","average_dB_level","maximum_dB_level","gym_density",
    "culture_density","local_businesses_density","restaurant_density","premium_stores_density","nightlife_density",
    "hospital_density","dist_downtown_km","proximity_to_sea","green_space_percentage","charging_stations_number",
    "walk_score","transit_score","bike_score","accessibility_score"
]

# Mapping variables to OSM tags
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
