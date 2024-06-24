import os
import logging
log = logging.getLogger()

import pandas as pd
import numpy as np

from pipeline.config import *


DATA_DIR = os.environ.get('DATA_DIR', None)
RESULTS_DIR = os.environ.get('RESULTS_DIR', None)



def load_data(path: str, filename: str) -> pd.DataFrame:
    full_path = f"{path}/{filename}.csv"
    log.debug("loading dataset: %s", full_path)

    data = pd.read_csv(full_path, parse_dates=['incidentDate', 'alarm', 'dispatch', 'enroute', 'arrival', 'enrouteFacility', 'cleared'])
    # data['arrival'] = pd.to_datetime(data['arrival'])

    # catch file not found error

    log.debug(data.head())

    return data


def filter_out_incidents_without_amr(data: pd.DataFrame) -> pd.DataFrame:
    # Check for rows where the 'agency' is AMR and there is a dispatch time
    has_amr_dispatched = data['juris4'].str.contains('AMR') & data['dispatch'].notnull()
    
    # Determine the incidents with AMR dispatched
    incidents_with_amr = has_amr_dispatched.groupby(data['incident']).transform('any')

    # Log incidents without AMR dispatch
    incidents_without_amr = data[~incidents_with_amr]
    incidents_without_amr.to_csv(f'{RESULTS_DIR}/incidents_without_amr.csv', index=False)  # Exporting to a CSV for review
    log.info(f"Logged {len(incidents_without_amr)} incidents without AMR dispatch")

    print("KEEPING THESE RECORDS GOING FORWARD:")
    print(data[incidents_with_amr].head())

    # Keep only incidents where an AMR was dispatched
    return data[incidents_with_amr]


def filter_out_incidents_without_pfr(data: pd.DataFrame) -> pd.DataFrame:
    # Check for rows where the 'agency' is PF&R and there is a dispatch time
    has_pfr_dispatched = data['juris4'].str.contains('PF&R') & data['dispatch'].notnull()
    
    # Determine the incidents with PF&R dispatched
    incidents_with_pfr = has_pfr_dispatched.groupby(data['incident']).transform('any')

    # Log incidents without PF&R dispatch
    incidents_without_pfr = data[~incidents_with_pfr]
    incidents_without_pfr.to_csv(f'{RESULTS_DIR}/incidents_without_pfr.csv', index=False)  # Exporting to a CSV for review
    log.info(f"Logged {len(incidents_without_pfr)} incidents without PF&R dispatch")

    print("KEEPING THESE RECORDS GOING FORWARD:")
    print(data[incidents_with_pfr].head())

    # Keep only incidents where PF&R was dispatched
    return data[incidents_with_pfr]



def merge_arrivals(data: pd.DataFrame) -> pd.DataFrame:
    # Filter AMR and PF&R data
    amr_data = data[data['juris4'] == "AMR"]
    pfr_data = data[data['juris4'] == "PF&R"]

    # Group by 'incident' to find the minimum 'arrival' and take the 'incidentType' and 'cleared' as well
    amr_min_arrival = amr_data.groupby('incident').agg({'arrival': 'min', 'cleared': 'first', 'incidentType': 'first'})
    pfr_min_arrival = pfr_data.groupby('incident').agg({'arrival': 'min', 'cleared': 'first', 'incidentType': 'first'})

    # Merge the two DataFrames on the 'incident' column while keeping all columns
    merged = pd.merge(pfr_min_arrival, amr_min_arrival, on='incident', how='outer', suffixes=('_pfr', '_amr'))

    merged.to_csv(f'{RESULTS_DIR}/merged_arrivals.csv', index=True)

    log.debug("MERGED ARRIVALS")
    log.debug(merged.head())

    return merged



def calculate_wait_times(merged: pd.DataFrame) -> pd.DataFrame:
    # Check if 'arrival_amr' is NaT and use 'cleared_amr' if that's the case
    merged['effective_amr_arrival'] = merged.apply(
        lambda row: row['cleared_amr'] if pd.isna(row['arrival_amr']) else row['arrival_amr'],
        axis=1
    )
    
    # Calculate 'wait_seconds' based on 'effective_amr_arrival' instead of 'arrival_amr'
    merged['wait_seconds'] = (merged['effective_amr_arrival'] - merged['arrival_pfr']).dt.total_seconds().fillna(0)
    merged['wait_seconds'] = merged['wait_seconds'].apply(lambda x: max(x, 0))
    
    # Calculate 'wait_time_minutes' based on updated 'wait_seconds'
    merged['wait_time_minutes'] = (merged['wait_seconds'] / 60).round(1)
    
    # # Generate 'year_week' based on 'arrival_pfr'
    # merged['year_week'] = merged['arrival_pfr'].dt.isocalendar().year.astype(str) + '-W' + \
    #                       merged['arrival_pfr'].dt.isocalendar().week.astype(str).str.zfill(2)

    # Adjust 'year_week' to consider Sunday as the first day of the week
    # Offset 'arrival_pfr' by one day if it's a Sunday
    merged['adjusted_date'] = merged['arrival_pfr'].apply(lambda x: x - pd.Timedelta(days=1) if x.weekday() == 6 else x)
    merged['year_week'] = merged['adjusted_date'].dt.strftime('%Y-W%U')
    
    # Drop the 'adjusted_date' column as it is no longer needed
    merged.drop(columns=['adjusted_date'], inplace=True)

    log.debug("WAIT TIMES")
    # log.debug(merged.head())
    log.debug(merged.head())
    return merged



def clean_merged_arrivals(merged: pd.DataFrame) -> pd.DataFrame:
    cleaned_merged = merged[merged['arrival_pfr'].notna()]

    cleaned_merged.to_csv(f'{RESULTS_DIR}/merged_arrivals_cleaned.csv', index=True)

    log.debug("CLEANED MERGED ARRIVALS")
    log.debug(cleaned_merged.head())
    
    return cleaned_merged


def filter_incidents(merged: pd.DataFrame, min_wait: int) -> pd.DataFrame:
    return merged[merged['wait_time_minutes'] >= min_wait]


# def incidents_by_week(merged: pd.DataFrame, wait_time) -> pd.DataFrame:
#     # counts = merged.groupby('year_week').size()
#     counts = merged[merged['wait_time_minutes'] >= wait_time].groupby('year_week').size()

#     # add a date range column
#     print(counts.head())
#     counts = counts.reset_index()
#     counts['date_range'] = counts['year_week'].apply(lambda x: pd.to_datetime(x + '-0', format='%Y-W%W-%w'))

#     return counts.reset_index(name='incidents')

def incidents_by_week(merged: pd.DataFrame, wait_time_threshold: int) -> pd.DataFrame:
    # Get the counts of incidents by week where the wait time exceeds the threshold
    incident_counts = merged[merged['wait_time_minutes'] >= wait_time_threshold].groupby('year_week').size()

    # Reset index to convert Series to DataFrame
    incident_counts = incident_counts.reset_index(name='incidents')

    # Function to calculate the start (Monday) of the week
    def get_week_start_date(year_week_str):
        year, week = map(int, year_week_str.split('-W'))
        # For ISO weeks, %G-W%V-%u format ensures Monday as the first day of the week
        return pd.to_datetime(f'{year}-W{week}-1', format='%G-W%V-%u')

    # Calculate start and end dates of the week
    incident_counts['start_date'] = incident_counts['year_week'].apply(get_week_start_date)
    incident_counts['end_date'] = incident_counts['start_date'] + pd.to_timedelta('6 days')

    # if dataframe is empty
    if incident_counts.empty:
        log.error("No incidents found that meet the wait time threshold.  This is a good thing")
        return None

    print(incident_counts.head())
    # Create a date range string
    incident_counts['date_range'] = incident_counts.apply(
        lambda x: f"{x['start_date'].strftime('%b %d')} - {x['end_date'].strftime('%b %d, %Y')}", axis=1
    )

    incident_counts.drop(columns=['start_date', 'end_date'], inplace=True)

    # rearrange 'date_range' to come first
    cols = incident_counts.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    incident_counts = incident_counts[cols]

    # TODO: would be nice to add weather data to give additional context

    return incident_counts



def export_data(df: pd.DataFrame, path: str, filename: str):
    export_path = f"{path}/{filename}"
    print(f">> exporting to: {export_path}")
    df.to_csv(export_path, index=False)


def print_analysis(merged: pd.DataFrame):

    # total_unique_incidents = merged['incident'].nunique()
    # NOTE: 'incident' is not a column but the DataFrame's index. 
    total_unique_incidents = merged.index.nunique()
    # average_wait_time = merged['wait_seconds'].mean().round(1)
    average_wait_time = round(merged['wait_seconds'].mean(), 1)
    print(f"Total Incidents: {total_unique_incidents}")
    print(f"Average Wait Time: {average_wait_time} seconds")




# NOTE: This is the main function that is called from pipeline/__main__.py
def process_wait_times( opts ):

    # Set the display.max_rows option in pandas
    # TODO what does this do?
    # max_rows = kwargs.get('DISPLAY_MAX_ROWS', None)
    # pd.set_option('display.max_rows', max_rows)
    filename = opts.get("<filename>", None)
    if filename is None:
        log.error("Please specify a file to analyse.")
        return


    data = load_data( DATA_DIR, filename)

    # Filter out incidents without any AMR unit dispatched
    data_with_amr = filter_out_incidents_without_amr(data)

    data_with_amr = filter_out_incidents_without_amr(data)
    data_with_amr_and_pfr = filter_out_incidents_without_pfr(data_with_amr)

    merged_arrivals = merge_arrivals(data_with_amr_and_pfr)
    merged_arrivals = clean_merged_arrivals(merged_arrivals)

    df_wait_times = calculate_wait_times(merged_arrivals)
    print(df_wait_times.head())

    for min_wait in [1, 5, 10, 15]:
        incidents = filter_incidents(df_wait_times, min_wait)
        export_data(incidents, RESULTS_DIR, f"/export_wait_times_{min_wait}_min.csv")

    wait_time=10
    weekly_incidents = incidents_by_week(df_wait_times, wait_time)
    if weekly_incidents is not None:
        export_data(weekly_incidents, RESULTS_DIR, f"/export_incidents_by_week ({wait_time} minutes).csv")
        print_analysis(merged_arrivals)
