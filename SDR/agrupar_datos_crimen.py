import pandas as pd
import numpy as np
import os

def main():
    # Define paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(base_path)
    neighborhoods_path = os.path.join(root_path, 'neighborhoods.csv')
    crime_data_path = os.path.join(base_path, 'Crime_Data_from_2020_to_Present_20251122.csv')

    print(f"Loading neighborhoods from {neighborhoods_path}...")
    neighborhoods = pd.read_csv(neighborhoods_path)
    
    print(f"Loading crime data from {crime_data_path}...")
    crime_data = pd.read_csv(crime_data_path)

    # Prepare coordinates
    # Neighborhoods: latitude_centroid, longitude_centroid
    neigh_coords = neighborhoods[['latitude_centroid', 'longitude_centroid']].values
    neigh_names = neighborhoods['name'].values

    # Crime: LAT, LON
    # Filter out invalid coordinates for calculation (e.g., 0,0)
    # We will assign "Unknown" to them later
    crime_coords = crime_data[['LAT', 'LON']].values

    print(f"Processing {len(crime_data)} records...")

    # Vectorized approach with chunks to save memory
    chunk_size = 50000
    n_chunks = (len(crime_data) // chunk_size) + 1
    assigned_neighborhoods = []

    for i in range(n_chunks):
        start = i * chunk_size
        end = start + chunk_size
        chunk = crime_coords[start:end]
        
        if len(chunk) == 0:
            break
            
        # Calculate squared Euclidean distance
        # (ChunkSize, 1, 2) - (1, NumNeigh, 2) -> (ChunkSize, NumNeigh, 2)
        diff = chunk[:, np.newaxis, :] - neigh_coords[np.newaxis, :, :]
        dists_sq = np.sum(diff**2, axis=2) # (ChunkSize, NumNeigh)
        
        nearest_indices = np.argmin(dists_sq, axis=1)
        chunk_assignments = neigh_names[nearest_indices]
        
        # Handle (0,0) coordinates - usually indicate missing location
        # Check where LAT and LON are both 0 (or very close to 0)
        is_zero = (np.abs(chunk[:, 0]) < 0.0001) & (np.abs(chunk[:, 1]) < 0.0001)
        
        # Convert to object array to allow string assignment if it was not already
        chunk_assignments = chunk_assignments.astype(object)
        chunk_assignments[is_zero] = "Unknown"
        
        assigned_neighborhoods.extend(chunk_assignments)
        
        print(f"Processed chunk {i+1}/{n_chunks}")

    # Add column
    crime_data['Neighborhood_Name'] = assigned_neighborhoods

    print("Saving updated dataset...")
    crime_data.to_csv(crime_data_path, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
