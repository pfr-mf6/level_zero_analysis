
import pandas as pd
import folium
import folium.plugins as plugins
import geopandas as gpd

STATION_1 = [45.5219553, -122.6732621]
STATION_3 = [45.528893, -122.6889443]
STATION_12 = [45.5547691, -122.5766133]

def create_heatmap(csv_path, output_path):
    # Load the incident data
    df = pd.read_csv(csv_path)
    unique_incidents = df.drop_duplicates(subset=['incident', 'latitude', 'longitude'])[['incident', 'latitude', 'longitude']]
    
    # Convert the unique incidents to a GeoDataFrame
    gdf = gpd.GeoDataFrame(unique_incidents, geometry=gpd.points_from_xy(unique_incidents.longitude, unique_incidents.latitude))
    
    # Create a heatmap
    portland_coordinates = [45.5231, -122.6765]
    heatmap_map = folium.Map(location=portland_coordinates, zoom_start=12, tiles='cartodb positron')
    
    # Extract the data for the heatmap
    heat_data = [[point.xy[1][0], point.xy[0][0]] for point in gdf.geometry]
    
    # Add the heatmap to the map
    plugins.HeatMap(heat_data, radius=20).add_to(heatmap_map)

    # Add the stations to the map
    # folium.Marker(STATION_1, popup='Station 1', icon=folium.Icon(color='red', icon='1', prefix='fa')).add_to(heatmap_map)
    # folium.Marker(STATION_3, popup='Station 3', icon=folium.Icon(color='red', icon='3', prefix='fa')).add_to(heatmap_map)
    # folium.Marker(STATION_12, popup='Station 12', icon=folium.Icon(color='red', icon='12', prefix='fa')).add_to(heatmap_map)

    # Save the heatmap to an HTML file
    heatmap_map.save(output_path)

if __name__ == "__main__":
    # input_csv_path = './example-sep23.csv'
    input_csv_path = '/Users/myca/My Drive/DATA/INTTERRA/DATA - CLEANED/2023 (YTD).csv'
    output_html_path = './heatmap.html'
    create_heatmap(input_csv_path, output_html_path)
