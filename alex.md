# Data Dictionary: `latorre/final.csv`

This file documents each column in `latorre/final.csv`, the join of `latorre/EstiloVida.csv` (lifestyle indicators) and `latorre/climate.csv` (environmental indicators), joined by neighborhood `name`.

## Columns and Units

- `OBJECTID`: Integer identifier for the neighborhood; no units.
- `name`: Neighborhood name (string).
- `latitude_centroid`: Latitude of neighborhood centroid in decimal degrees (WGS84); unit: degrees.
- `longitude_centroid`: Longitude of neighborhood centroid in decimal degrees (WGS84); unit: degrees.
- `surface_area`: Neighborhood surface area; unit: square kilometers (km²).

- `air_quality_index`: Categorical air quality label (e.g., `Good`, `Good/Moderate`, `Moderate`, `Moderate/Poor`). Parenthetical codes were removed; no units.
- `average_dB_level`: Typical average ambient sound level; unit: decibels (dB).
- `maximum_dB_level`: Typical maximum/peak sound level; unit: decibels (dB).

- `gym_density`: Number of gyms per square kilometer; unit: counts/km².
- `culture_density`: Number of cultural venues per square kilometer (e.g., museums, galleries, theaters); unit: counts/km².
- `local_businesses_density`: Number of local businesses per square kilometer; unit: counts/km².
- `restaurant_density`: Number of restaurants per square kilometer; unit: counts/km².
- `premium_stores_density`: Number of premium/brand-name stores per square kilometer; unit: counts/km².
- `nightlife_density`: Number of nightlife venues per square kilometer (e.g., bars, clubs); unit: counts/km².
- `hospital_density`: Number of hospitals per square kilometer; unit: counts/km².

## Notes

- All density fields are computed as: `density = count / surface_area`.
  - Example: 20 restaurants in 2.5 km² → `20 / 2.5 = 8.0` restaurants/km².
- `latitude_centroid` and `longitude_centroid` represent the geometric centroid of each neighborhood polygon.
- `air_quality_index` values were simplified to remove parenthetical codes (e.g., `Moderate (M)` → `Moderate`).