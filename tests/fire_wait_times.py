import pandas as pd
pd.set_option('display.max_rows', None)

# TODO:
dataset_filename = "condensed-large"

# PATH = "/Users/micah/My Drive/DATA/INTTERRA" # io
PATH = "/Users/myca/My Drive/DATA/INTTERRA" # Jupiter
# PATH = "/Users/myca/Downloads" # Jupiter downloads
full_path = f"{PATH}/{dataset_filename}.csv"

print(F"\n\n------------------------------------------")
print(">> loading dataset: ", dataset_filename)
print(f"{full_path=}")


#
#
#
print("\n\n------------------------------------------ DATA IMPORT:")
data = pd.read_csv(full_path)
# data = pd.read_csv(full_path, low_memory=False)
data['arrival'] = pd.to_datetime(data['arrival'])
# data['arrival'] = pd.to_datetime(data['arrival'], errors='coerce')

print(data.head())


#
#
#
print("\n\n------------------------------------------ MERGED ARRIVALS:")

# Filter out records corresponding to "AMR" and "PF&R"
amr_data = data[data['dispatchStation'] == "AMR"]
pfr_data = data[data['dispatchStation'].str.startswith("PF&R")]

# Group by 'incident' and get the earliest arrival time for each group
amr_min_arrival = amr_data.groupby('incident')['arrival'].min()
pfr_min_arrival = pfr_data.groupby('incident')['arrival'].min()

# Merge the two series on 'incident'
merged_arrivals = pd.concat([pfr_min_arrival, amr_min_arrival], axis=1, keys=['pfr_arrival', 'amr_arrival'])

# Calculate wait time for each incident
merged_arrivals['wait_seconds'] = (merged_arrivals['amr_arrival'] - merged_arrivals['pfr_arrival']).dt.total_seconds()

# If AMR arrived before PF&R or at the same time, set wait time to 0
merged_arrivals['wait_seconds'] = merged_arrivals['wait_seconds'].apply(lambda x: max(0, x))

print( merged_arrivals.head(n=10) )
export_filename = f"{PATH}/export- merged arrivals.csv"
print(">> exporting to: ", export_filename)
merged_arrivals.to_csv( export_filename )


#
#
#
print("\n\n------------------------------------------ WAIT TIMES:")

incidents_waited_1_minute = merged_arrivals[merged_arrivals['wait_seconds'] >= 60].copy() # five minute
incidents_waited_1_minute['wait_time_minutes'] = (incidents_waited_1_minute['wait_seconds'] / 60).round(1)


# Drop the original 'wait_time' column in seconds
# filtered_data = filtered_data.drop(columns=['wait_seconds'])

incidents_waited_5 = incidents_waited_1_minute[incidents_waited_1_minute['wait_time_minutes'] >= 5.0]
incidents_waited_10 = incidents_waited_1_minute[incidents_waited_1_minute['wait_time_minutes'] >= 10.0]
incidents_waited_15 = incidents_waited_1_minute[incidents_waited_1_minute['wait_time_minutes'] >= 15.0]


print(incidents_waited_1_minute.head())
export_filename = f"{PATH}/export- wait times.csv"
print(">> exporting to: ", export_filename)
incidents_waited_1_minute[incidents_waited_1_minute['wait_time_minutes'] >= 10].to_csv( export_filename )



print("\n\n------------------------------------------ INCIDENTS BY WEEK:")

# Extract the 'year-week' string directly for all the filtered datasets using ISO week numbering
incidents_waited_1_minute['year_week'] = incidents_waited_1_minute['pfr_arrival'].dt.isocalendar().year.astype(str) + '-W' + incidents_waited_1_minute['pfr_arrival'].dt.isocalendar().week.astype(str).str.zfill(2)
incidents_waited_5['year_week'] = incidents_waited_5['pfr_arrival'].dt.isocalendar().year.astype(str) + '-W' + incidents_waited_5['pfr_arrival'].dt.isocalendar().week.astype(str).str.zfill(2)
incidents_waited_10['year_week'] = incidents_waited_10['pfr_arrival'].dt.isocalendar().year.astype(str) + '-W' + incidents_waited_10['pfr_arrival'].dt.isocalendar().week.astype(str).str.zfill(2)
incidents_waited_15['year_week'] = incidents_waited_15['pfr_arrival'].dt.isocalendar().year.astype(str) + '-W' + incidents_waited_15['pfr_arrival'].dt.isocalendar().week.astype(str).str.zfill(2)

# Count incidents by 'year_week' for all the filtered datasets
incidents_by_week_total = incidents_waited_1_minute.groupby('year_week').size()
incidents_by_week_5 = incidents_waited_5.groupby('year_week').size()
incidents_by_week_10 = incidents_waited_10.groupby('year_week').size()
incidents_by_week_15 = incidents_waited_15.groupby('year_week').size()

# Create a DataFrame to merge the counts
incidents_by_week_df = pd.DataFrame({
    'total_incidents': incidents_by_week_total,
    'waited_5_plus': incidents_by_week_5,
    'waited_10_plus': incidents_by_week_10,
    'waited_15_plus': incidents_by_week_15,
}).fillna(0).astype(int)  # Replace NaN with 0 and convert to integer

# Reset the index so 'year_week' becomes a column
incidents_by_week_df.reset_index(inplace=True)

# Reorder the columns
columns_ordered = ['year_week'] + incidents_by_week_df.columns[1:].tolist()[::-1]
incidents_by_week_df = incidents_by_week_df[columns_ordered]

print(incidents_by_week_df)

export_filename = f"{PATH}/export- incidents by week.csv"
print(">> exporting to: ", export_filename)
incidents_by_week_df.to_csv(export_filename, index=False)



# 
#
#
print("\n\n------------------------------------------ DATA VISUALIZATION:")

# Calculate statistics for wait times
total_incidents = len(merged_arrivals)
average_wait_time = merged_arrivals['wait_seconds'].mean().round(1)

print( f"ANALYSIS FOR DATASET: {dataset_filename}" )
print("------------------------------------------")
print( f"{total_incidents=}" )
print( f"{average_wait_time=} seconds" )

print( f"waited 5+ minutes on {len(incidents_waited_5)} incidents" )
print( f"waited 10+ minutes on {len(incidents_waited_10)} incidents" )
print( f"waited 15+ minutes on {len(incidents_waited_15)} incidents" )
