import pandas as pd
import numpy as np
import folium
import folium.plugins as plugins
# from sklearn.neighbors import KernelDensity
import sklearn


STATION_1 = [45.5219553, -122.6732621]
STATION_3 = [45.528893, -122.6889443]
STATION_12 = [45.5547691, -122.5766133]


def create_adjusted_heatmap(csv_path, output_path):
    # Load the incident data
    df = pd.read_csv(csv_path)
    unique_incidents = df.drop_duplicates(subset=['incident', 'latitude', 'longitude'])[['incident', 'latitude', 'longitude']]
    
    # Extract the data for the heatmap
    heat_data = [[row["latitude"], row["longitude"]] for _, row in unique_incidents.iterrows()]

    # Calculate the density values using Kernel Density Estimation (KDE)
    data = unique_incidents[['longitude', 'latitude']].values
    kde = KernelDensity(bandwidth=0.01, metric='haversine')
    kde.fit(np.radians(data))
    density = np.exp(kde.score_samples(np.radians(data)))

    # Determine the 80th percentile of the density values
    percentile_80 = np.percentile(density, 80)

    # Normalize density values between 0 and 1
    density_normalized = (density - density.min()) / (density.max() - density.min())
    percentile_80_normalized = (percentile_80 - density.min()) / (density.max() - density.min())

    # Create a custom gradient where values from the 80th percentile and above are deep red
    gradient = {
        0: 'blue',
        0.5 * percentile_80_normalized: 'green',
        percentile_80_normalized: 'yellow',
        1: 'red'
    }

    # Create the heatmap with the adjusted gradient
    portland_coordinates = [45.5231, -122.6765]
    heatmap_adjusted = folium.Map(location=portland_coordinates, zoom_start=12, tiles='cartodb positron')
    plugins.HeatMap(heat_data, radius=15, gradient=gradient).add_to(heatmap_adjusted)

    # Add a marker for Station 3
    station_3_coords = [45.528893, -122.6889443]
    folium.Marker(station_3_coords, popup='Station 3', icon=folium.Icon(color='red', icon='fire', prefix='fa')).add_to(heatmap_adjusted)

    # Save the heatmap to an HTML file
    heatmap_adjusted.save(output_path)



if __name__ == "__main__":
    # input_csv_path = './example-sep23.csv'
    input_csv_path = '/Users/myca/My Drive/DATA/INTTERRA/DATA - CLEANED/2023 (YTD).csv'
    output_html_path = './heatmap.html'
    create_adjusted_heatmap(input_csv_path, output_html_path)
