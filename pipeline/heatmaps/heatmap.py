import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('./example-sep23.csv')

# Display the first few rows of the DataFrame to inspect its structure
print( df.head() )


# Extract columns that might contain GPS location data (e.g., latitude, longitude)
potential_gps_columns = [col for col in df.columns if 'lat' in col.lower() or 'lon' in col.lower()]

# Display these columns for the first few rows
print( df[potential_gps_columns].head() )


# Extract unique incidents with corresponding latitude and longitude
unique_incidents = df.drop_duplicates(subset=['incident', 'latitude', 'longitude'])[['incident', 'latitude', 'longitude']]

print( unique_incidents.head() )


import matplotlib.pyplot as plt
import seaborn as sns

# Set up the map using seaborn
plt.figure(figsize=(10, 6))
sns.scatterplot(data=unique_incidents, x="longitude", y="latitude", hue="incident", palette="YlOrRd", legend=False)

# Add title and labels
plt.title('Heatmap of 911 Incident Data')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

plt.show()
