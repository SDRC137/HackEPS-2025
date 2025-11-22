import pandas as pd
import os

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(base_path)
    input_path = os.path.join(root_path, 'neighborhoods_crimen.csv')
    output_path = os.path.join(root_path, 'neighborhoods_crimen_definitivo.csv')

    print(f"Loading {input_path}...")
    df = pd.read_csv(input_path)

    # Columns to select
    # Original neighborhood columns + requested metrics
    # Note: 'population' is already in the source csv
    cols_to_keep = [
        'OBJECTID', 
        'name', 
        'latitude_centroid', 
        'longitude_centroid', 
        'population',
        'Violent_vs_Property_Ratio',
        'Crimes_Per_1000_People',
        'Crime_Trend_Slope'
    ]

    # Check if columns exist
    missing_cols = [c for c in cols_to_keep if c not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns: {missing_cols}")
        return

    print("Selecting columns...")
    df_definitivo = df[cols_to_keep].copy()

    print(f"Saving to {output_path}...")
    df_definitivo.to_csv(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
