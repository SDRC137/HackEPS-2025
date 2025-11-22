import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from scipy import stats

def classify_crime(description):
    description = str(description).upper()
    
    violent_keywords = [
        'ASSAULT', 'BATTERY', 'ROBBERY', 'HOMICIDE', 'RAPE', 'KIDNAP', 
        'BRANDISH WEAPON', 'SHOTS FIRED', 'CRIMINAL THREATS', 'MANSLAUGHTER',
        'SEXUAL', 'WEAPON'
    ]
    
    property_keywords = [
        'THEFT', 'BURGLARY', 'VANDALISM', 'STOLEN', 'ARSON', 'SHOPLIFTING', 
        'PICKPOCKET', 'TRESPASSING', 'EMBEZZLEMENT', 'FORGERY', 'FRAUD'
    ]
    
    for keyword in violent_keywords:
        if keyword in description:
            return 'Violent'
            
    for keyword in property_keywords:
        if keyword in description:
            return 'Property'
            
    return 'Other'

def calculate_trend(group):
    # Group is a series of counts indexed by month (or date)
    # We expect 12 data points. If less, we fill with 0.
    if len(group) < 2:
        return 0.0
    
    y = group.values
    x = np.arange(len(y))
    
    # Simple linear regression slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(base_path)
    neighborhoods_path = os.path.join(root_path, 'neighborhoods.csv')
    crime_data_path = os.path.join(base_path, 'Crime_Data_from_2020_to_Present_20251122.csv')
    output_path = os.path.join(root_path, 'neighborhoods_crimen.csv')

    print("Loading data...")
    neighborhoods = pd.read_csv(neighborhoods_path)
    crime_data = pd.read_csv(crime_data_path)

    # Filter out crimes with unknown neighborhood
    crime_data = crime_data[crime_data['Neighborhood_Name'] != 'Unknown'].copy()
    
    print("Classifying crimes...")
    crime_data['Crime_Type'] = crime_data['Crm Cd Desc'].apply(classify_crime)
    
    # 1. Total Crimes per Neighborhood
    print("Calculating total crimes...")
    total_crimes = crime_data.groupby('Neighborhood_Name').size().reset_index(name='Total_Crimes')
    
    # 2. Violent and Property Counts
    print("Calculating crime types...")
    crime_counts = crime_data.groupby(['Neighborhood_Name', 'Crime_Type']).size().unstack(fill_value=0).reset_index()
    
    if 'Violent' not in crime_counts.columns:
        crime_counts['Violent'] = 0
    if 'Property' not in crime_counts.columns:
        crime_counts['Property'] = 0
        
    # 3. Ratios
    # We merge total crimes first to calculate ratios
    stats_df = pd.merge(total_crimes, crime_counts[['Neighborhood_Name', 'Violent', 'Property']], on='Neighborhood_Name', how='left')
    
    # Avoid division by zero
    stats_df['Violent_Ratio'] = stats_df['Violent'] / stats_df['Total_Crimes']
    stats_df['Property_Ratio'] = stats_df['Property'] / stats_df['Total_Crimes']
    
    # Violent vs Property Ratio (Violent / Property)
    # If Property is 0, we can set it to a high number or NaN. Let's handle it gracefully.
    # Or maybe the user meant (Violent Ratio) / (Property Ratio)? It's the same as Violent / Property.
    stats_df['Violent_vs_Property_Ratio'] = stats_df.apply(
        lambda row: row['Violent'] / row['Property'] if row['Property'] > 0 else np.nan, axis=1
    )

    # 4. Trend (Last 12 Months)
    print("Calculating trends...")
    crime_data['DATE OCC'] = pd.to_datetime(crime_data['DATE OCC'])
    
    # Determine the last date in the dataset
    last_date = crime_data['DATE OCC'].max()
    start_date = last_date - pd.DateOffset(months=12)
    
    recent_crimes = crime_data[crime_data['DATE OCC'] > start_date].copy()
    
    # Group by Neighborhood and Month (YYYY-MM)
    recent_crimes['Month'] = recent_crimes['DATE OCC'].dt.to_period('M')
    monthly_counts = recent_crimes.groupby(['Neighborhood_Name', 'Month']).size().reset_index(name='Count')
    
    # Pivot to get months as columns or just iterate
    # We need to ensure all 12 months are present for each neighborhood for accurate slope?
    # Or just use the months present. Linear regression handles missing x points, but 0 counts should be 0.
    
    # Better approach: Create a complete index of Neighborhood x Month
    months_period = pd.period_range(start=start_date, end=last_date, freq='M')
    
    trends = []
    for neighborhood in neighborhoods['name']:
        # Get counts for this neighborhood
        n_counts = monthly_counts[monthly_counts['Neighborhood_Name'] == neighborhood]
        
        # Reindex to ensure all months are present, filling missing with 0
        if not n_counts.empty:
            n_counts = n_counts.set_index('Month')['Count'].reindex(months_period, fill_value=0)
            slope = calculate_trend(n_counts)
        else:
            slope = 0.0
            
        trends.append({'Neighborhood_Name': neighborhood, 'Crime_Trend_Slope': slope})
        
    trends_df = pd.DataFrame(trends)
    
    # Merge everything
    print("Merging results...")
    final_df = pd.merge(neighborhoods, stats_df, left_on='name', right_on='Neighborhood_Name', how='left')
    final_df = pd.merge(final_df, trends_df, left_on='name', right_on='Neighborhood_Name', how='left')
    
    # Calculate Crimes per 1000 people
    # Ensure population is numeric
    if 'population' in final_df.columns:
        final_df['Crimes_Per_1000_People'] = (final_df['Total_Crimes'] / final_df['population']) * 1000
    else:
        print("Warning: 'population' column not found in neighborhoods data.")

    # Fill NaNs for neighborhoods with no crimes (if any)
    cols_to_fill = ['Total_Crimes', 'Violent', 'Property', 'Violent_Ratio', 'Property_Ratio', 'Violent_vs_Property_Ratio', 'Crime_Trend_Slope', 'Crimes_Per_1000_People']
    for col in cols_to_fill:
        if col in final_df.columns:
             # Don't fill NaN for Ratio if it was division by zero/undefined, but for Total_Crimes=0 it makes sense.
             # Actually, if Total_Crimes is NaN, it means 0 crimes.
             if col in ['Total_Crimes', 'Violent', 'Property', 'Crimes_Per_1000_People']:
                 final_df[col] = final_df[col].fillna(0)
    
    # Clean up duplicate name columns if any
    if 'Neighborhood_Name_x' in final_df.columns:
        final_df.drop(columns=['Neighborhood_Name_x', 'Neighborhood_Name_y'], inplace=True)
    elif 'Neighborhood_Name' in final_df.columns:
        final_df.drop(columns=['Neighborhood_Name'], inplace=True)

    print(f"Saving to {output_path}...")
    final_df.to_csv(output_path, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
