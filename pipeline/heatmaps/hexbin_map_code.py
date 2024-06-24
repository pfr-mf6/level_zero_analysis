
import pandas as pd
import numpy as np
import folium
from matplotlib.colors import to_hex
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
import geopandas as gpd
import shapely.geometry as geometry

def hex_coordinates(center, size):
    "Generate coordinates for a regular hexagon given a center, size."
    angle = np.linspace(0, 2*np.pi, 7)
    x = center[0] + size * np.sin(angle)
    y = center[1] + size * np.cos(angle)
    return np.column_stack((x, y))

def plot_hexbin_on_map(data, x_col, y_col, gridsize, map_obj, cmap='plasma'):
    "Plot hexbin on a folium map."
    
    # Create a hexbin plot to get the data transformed into hex bins
    hb = plt.hexbin(data[x_col], data[y_col], gridsize=gridsize, cmap=cmap, mincnt=1)
    plt.close()
    
    # Calculate hex size
    dx = (data[x_col].max() - data[x_col].min()) / gridsize
    dy = dx * np.sqrt(3) / 2
    
    # For each hexagon in the hexbin data, create a polygon and add it to the map
    for i, (x, y) in enumerate(zip(hb.get_offsets()[:, 0], hb.get_offsets()[:, 1])):
        hex_coords = hex_coordinates([x, y], dx)
        hexagon = Polygon(hex_coords)
        color = to_hex(plt.cm.plasma(hb.get_array()[i]/np.max(hb.get_array())))
        
        # Convert the hexagon to geojson and add it to the map
        geojson = folium.GeoJson(
            geometry.mapping(hexagon),
            style_function=lambda feature, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.6
            }
        )
        geojson.add_to(map_obj)
    
    return map_obj

if __name__ == "__main__":
    # Load the incident data
    df = pd.read_csv('./example-sep23.csv')
    unique_incidents = df.drop_duplicates(subset=['incident', 'latitude', 'longitude'])[['incident', 'latitude', 'longitude', 'incidentDate']]
    
    # Create the hexbin map
    portland_coordinates = [45.5231, -122.6765]
    hex_map = folium.Map(location=portland_coordinates, zoom_start=12, tiles='cartodb positron')
    hex_map = plot_hexbin_on_map(unique_incidents, 'longitude', 'latitude', gridsize=700, map_obj=hex_map)
    
    # Save the map to an HTML file
    hex_map.save('./heatmap.html')
