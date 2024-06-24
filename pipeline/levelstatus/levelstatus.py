import os
import logging
log = logging.getLogger()

import pandas as pd
import numpy as np

from pipeline.config import *


DATA_DIR = os.environ.get('DATA_DIR', None)
PROCESSED_DATA_DIR = os.environ.get('PROCESSED_DATA_DIR', None)
RESULTS_DIR = os.environ.get('RESULTS_DIR', None)



def load_data(path: str, filename: str) -> pd.DataFrame:
    full_path = f"{path}/{filename}.csv"
    log.debug("loading dataset: %s", full_path)

    try:
        # data = pd.read_csv(full_path, delimiter='\t', parse_dates=['Activity Date'])
        # data = pd.read_csv(full_path, delimiter='\t')
        data = pd.read_csv(full_path, delimiter='\t', encoding='utf-8', encoding_errors='replace')
    except FileNotFoundError as e:
        log.error(e) # no traceback info - tidier
        exit(0)
    

    # truncate miliseconds in "Activity Date" column (eg. 2023-11-01 00:07:16.553600 to 2023-11-01 00:07:16)
    data['Activity Date'] = data['Activity Date'].astype(str).str[:-5]
    data['Activity Date'] = pd.to_datetime(data['Activity Date'])

    data['Apparatus ID'] = data['Apparatus ID'].astype(str)
    data['Apparatus Status'] = data['Apparatus Status'].astype(str)
    data['Activity Code'] = data['Activity Code'].astype(str)
    data['Call Number'] = data['Call Number'].astype('Int64')
    data['Call Type'] = data['Call Type'].astype(str)
    data['Remarks'] = data['Remarks'].astype(str)


    # data['Apparatus Status'] = data['Apparatus Status'].astype(str)


    log.info(f"Loaded {len(data)} rows and {len(data.columns)} columns")
    print(data.head())

    return data



def remove_unneeded_cols(df: pd.DataFrame) -> pd.DataFrame:
    print(df.columns)

    columns_to_remove = [
        "Updated by Operator Code",
        "Updated by Desk ID",
        "Updated by Operator Jurisdiction",
        "Call priority",
        "Call Jurisdiction",
        "Station Jurisdiction",
        "Activity Type",
        "Call Date"
    ]

    df = df.drop(columns=columns_to_remove)

    log.info("Dropping columns: %s", columns_to_remove)
    print( df.head() )

    return df


def remove_unneeded_rows(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Dropping rows with Activity Type: M, C, L, S")

    df = df[df["Activity Type"] != "M"] # messages
    df = df[df["Activity Type"] != "C"] # more messages?
    df = df[df["Activity Type"] != "L"] # LOGOFF remarks (duplicative - use #TODO for actual logoff tracking)
    df = df[df["Activity Type"] != "S"] # "signal" (eg. AUTO RADIO ALERTED PERSONNEL: MD208515 -  (22824))

    # drop the "Activity Type" column
    # df = df.drop(columns=["Activity Type"])

    print(df.head())

    return df


def remove_non_AMR(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Dropping all rows that are not AMR")

    stations_to_keep = [
        "715",
        "715B",
        "ZLZERO"
    ]

    df = df[df["Station"].isin(stations_to_keep)]

    # drop the station column now that we don't need it anymore
    df = df.drop(columns="Station")

    # drop "Apparatus ID"s that start with "MS" (AMR Supervisors)
    df = df[~df["Apparatus ID"].str.startswith("MS")]

    print(df.head())

    return df


def arrange_cols(df: pd.DataFrame) -> pd.DataFrame:
    log.info("Re-arranging columns")

    # re-arrange the columns
    df = df[[
        "Activity Date",
        "Apparatus ID",
        "Apparatus Status",
        "Activity Code",
        "Call Number",
        "Call Type",
        "Remarks"
    ]]

    print(df.head())

    return df




def process_levelstatus(df: pd.DataFrame):
    data = df.copy()

    




## TODO REFACTOR THIS
def process_levelstatus( opts ):
    """ This is called form the command line tool... we need to make this into a function that can be called from the web app
    """
    # Set the display.max_rows option in pandas
    # TODO what does this do?
    # max_rows = kwargs.get('DISPLAY_MAX_ROWS', None)
    # pd.set_option('display.max_rows', max_rows)
    filename = opts.get("<filename>", None)
    if filename is None:
        log.error("Please specify a file to analyse.")
        return

    data = load_data( DATA_DIR, filename)

    data = remove_unneeded_rows(data)
    data = remove_unneeded_cols(data)

    data = remove_non_AMR(data)

    data = arrange_cols(data)

    # sort times by ascending order in 'Activity Date'
    data = data.sort_values(by=['Activity Date'])

    # Replace various forms of missing values with np.nan (standard NaN in numpy/pandas)
    data.replace(['nan'], np.nan, inplace=True)

    # If you want to replace missing values with empty strings instead
    # data.fillna('', inplace=True)

    # reset the index
    data = data.reset_index(drop=True)

    log.info("Saving processed data to %s", PROCESSED_DATA_DIR)
    # save the processed data to a csv file
    data.to_csv(f"{PROCESSED_DATA_DIR}/{filename}.csv", index=False)
    print(data.head())


    ######################## LEVELS ########################
    data['ALS level'] = 0
    data['BLS level'] = 0
    data['ALS logged on'] = [[] for _ in range(len(data))]
    data['ALS AV'] = [[] for _ in range(len(data))]
    data['comments'] = ''
    data = available_units(data)
    data = talley_available_units(data)

    data = data[[
        "Activity Date",
        "Apparatus ID",
        "Apparatus Status",
        "Activity Code",
        "ALS level", # NEW
        # "BLS level", # NEW
        "ALS AV", # NEW
        "comments", # NEW
        # "ALS logged on", # NEW
        "Remarks",
        "Call Number",
        "Call Type"
    ]]

    ####################### SAVE ###########################
    log.info("Saving processed data to %s", PROCESSED_DATA_DIR)
    # save the processed data to a csv file
    data.to_csv(f"{PROCESSED_DATA_DIR}/{filename}_LEVELS.csv", index=False)
    print(data.head())

    plot_that_shit(data)


    ########################








def available_units(df: pd.DataFrame) -> pd.DataFrame:
    # Create a new column called 'level' and set it to 0
    # df['ALS level'] = 0
    # df['BLS level'] = 0
    # df['Available Units'] = ''
    if 'ALS logged on' not in df.columns:
        df['ALS logged on'] = [[] for _ in range(len(df))]

    logged_on = []
    av = []

    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        if index == 0:
            df.at[index, 'ALS logged on'] = []
            continue

        # only worry about ALS units
        if row['Apparatus ID'].startswith("B"):
            df.at[index, "comments"] = f"ignoring BLS status updates for now..."
            # TODO god damn this is ugly!!
            df.at[index, 'ALS logged on'] = logged_on.copy()
            df.at[index, 'ALS AV'] = av.copy()
            continue

        # if row['Apparatus Status'] == 'ZZ':
        #     if 'MDT SIGNON' in row['Remarks']:
        #         if row['Apparatus ID'] not in logged_on:
        #             logged_on.append(row['Apparatus ID'])
        #             df.at[index, "comments"] = f"LOG ON: adding {row['Apparatus ID']} to logged in units"
        #         else:
        #             df.at[index, "comments"] = f"LOG ON: {row['Apparatus ID']} _already_ in logged in - duplicate, not adding"

        #     elif "STATUS: IQ TO ZZ" in row['Remarks']:
        #         if row['Apparatus ID'] in logged_on:
        #             logged_on.remove(row['Apparatus ID'])
        #             df.at[index, "comments"] = f"LOG OFF: removing {row['Apparatus ID']} from logged in units"
        #         else:
        #             df.at[index, "comments"] = f"WARNING: LOG OFF: {row['Apparatus ID']} WAS NOT in logged on units!!"

        if row['Apparatus Status'] == "AV":
            # if row['Apparatus ID'] not in logged_on:
            #     if row['Apparatus ID'].startswith("M2"):
            #         logged_on.append(row['Apparatus ID'])
            #         df.at[index, "comments"] = f"CLACKAMAS MUTUAL AID UNIT BEING ADDED TO AVAILABLE UNITS: {row['Apparatus ID']}"
            #     # else:
            #         # print(row['Apparatus ID'])
            #         # raise Exception(f"WARNING: {row['Apparatus ID']} is not in available units but has status of AV")
            if row['Apparatus ID'] not in av:
                if not row['Apparatus ID'].startswith("LZ"): # don't add LZ units to available units
                    av.append(row['Apparatus ID'])
                    df.at[index, "comments"] = f"{row['Apparatus ID']} AVAILABLE"
            else:
                df.at[index, "comments"] = f"{row['Apparatus ID']} AVAILABLE - duplicate"

        if row['Apparatus Status'] == "DP":
            if row['Apparatus ID'] in av:
                av.remove(row['Apparatus ID'])
                df.at[index, "comments"] = f"{row['Apparatus ID']} DISPATCHED"
            else:
                if row['Apparatus ID'].startswith("LZ"):
                    df.at[index, "comments"] = f"<<< 911 CALL WITH NO AVAILABLE UNITS!! >>>"
                else:
                    df.at[index, "comments"] = f"WARNING: {row['Apparatus ID']} wasn't in available units but has status of DP"


        if row['Apparatus Status'] == "ZZ":
            if row['Apparatus ID'] in av:
                av.remove(row['Apparatus ID'])
                df.at[index, "comments"] = f"{row['Apparatus ID']} OOS"
            
            if row['Remarks'] == "STATUS: IQ TO ZZ":
                df.at[index, "comments"] = f"GOODNIGHT, {row['Apparatus ID']} <3"

            if row['Remarks'] == "MDT SIGNON ":
                df.at[index, "comments"] = f"GOOD MORNING, {row['Apparatus ID']} <3"

            # else:
                # df.at[index, "comments"] = f"WARNING: {row['Apparatus ID']} wasn't known to be available, is not UNAVAILABLE"


        # Directly assign the 'available_units' list to the current row's 'Available Units'
        df.at[index, 'ALS logged on'] = logged_on.copy()
        df.at[index, 'ALS AV'] = av.copy()

    print(df.tail())

    return df




def talley_available_units(df: pd.DataFrame) -> pd.DataFrame:
    # Create a new column called 'level' and set it to 0
    df['ALS level'] = 0
    
    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        df.at[index, 'ALS level'] = len(row['ALS AV'])

    return df



def plot_that_shit(df: pd.DataFrame, save_fig: bool = True) -> None:
    import matplotlib.pyplot as plt

    # find the first day in this dataframe
    first_day = df['Activity Date'].dt.date.min()
    # keep all days past the first day
    df = df[df['Activity Date'].dt.date > first_day]


    # Set the timestamp column as the index
    df.set_index('Activity Date', inplace=True)

    # Resample data into 1-minute intervals taking the mean of the 'value'
    # resampled_df = df['ALS level'].resample('1T').mean() # dots don't always connect
    # resampled_df = df['ALS level'].resample('5T').mean() # smoother lines
    resampled_df = df['ALS level'].resample('2T').min() # smoother lines
    df = resampled_df

    # get the first and last timestamp in the df
    first_timestamp = df.index.min()
    last_timestamp = df.index.max()
    first = first_timestamp.strftime('%Y%m%d')
    last = last_timestamp.strftime('%Y%m%d')

    # df['date'] = df['Activity Date'].dt.date
    # remove the time and keep the date

    #### LINE CHART
    plt.figure(figsize=(15, 7))
    df.plot(title='Levels over time')

    # set y range from 0 to 6
    # plt.ylim(bottom=0, top=6)
    plt.xlabel('Date')
    plt.ylabel('ALS Levels')
    plt.ylim(bottom=0)
    #### BAR CHART
    # plt.figure(figsize=(15, 7))
    # df.plot(kind='bar', title='Event Values Over Time')
    # plt.xlabel('Time')
    # plt.ylabel('Value')

    # Depending on the number of bars, you might want to adjust the xticks to show fewer labels
    # to prevent them from overlapping. Here's an example of how to show every nth label:
    # n = 500  # Shows every n-th label
    # plt.xticks(range(0, len(resampled_df.index), n), resampled_df.index[::n].strftime('%Y-%m-%d %H:%M'), rotation=45, ha='right')


    # plt.show()
    # plt.savefig()
    if save_fig:
        plt.savefig(f'{RESULTS_DIR}/levels {first}-{last}.png', dpi=300, bbox_inches='tight')
    
    # return the plot as an image

    return plt.gcf() # return the plot as an image




# def update_level(row, previous_level):
#     # Copy the previous level
#     updated_level = previous_level

#     # If the status is 'AV', increment the level
#     if row['Apparatus Status'] == 'AV':
#         # if Apparatus ID starts with "M"
#         if row['Apparatus ID'].startswith("M"):
#             updated_level += 1
#         elif row['Apparatus ID'].startswith("B"):
#             updated_level += 1

#     # If the status is 'DP', decrement the level
#     elif row['Apparatus Status'] == 'DP':
#         updated_level -= 1

#     # Return the updated level
#     return updated_level

















    # Initialize the level and available units list
    # level = 0
    # available_units = []

    # Create a new column for the level and available units for each row
    # ambulance_data['Level'] = 0
    # ambulance_data['Available Units'] = [[] for _ in range(len(ambulance_data))]

    # Iterate over the status changes to update the 'level' and 'available units' accordingly
    # for index, row in ambulance_data.iterrows():
    #     level, available_units = update_level_and_units(row, level, available_units)
    #     ambulance_data.at[index, 'Level'] = level
    #     ambulance_data.at[index, 'Available Units'] = available_units

    # # Now we need to create the full timeline from the first to the last status change, minute by minute
    # start_time = ambulance_data['Activity Date'].min()
    # end_time = ambulance_data['Activity Date'].max()
    # full_timeline = pd.DataFrame(index=pd.date_range(start=start_time, end=end_time, freq='T'))
    # full_timeline = full_timeline.join(ambulance_data.set_index('Activity Date'), how='left')

    # # Forward fill the 'Level' and 'Available Units' to maintain the values over time
    # full_timeline['Level'].ffill(inplace=True)
    # full_timeline['Available Units'].ffill(inplace=True)

    # # Fill any remaining NaN values with 0 for 'Level' and empty list for 'Available Units'
    # full_timeline['Level'].fillna(0, inplace=True)
    # full_timeline['Available Units'].fillna([[]], inplace=True)

    # # Reset index to make 'Activity Date' a column again
    # full_timeline.reset_index(inplace=True)
    # full_timeline.rename(columns={'index': 'Activity Date'}, inplace=True)

    # # Display the first few rows of the full timeline
    # full_timeline.head()










# Define the status change logic as a function
def update_level_and_units(row, current_level, current_units):
    # Copy the current units to avoid modifying the original list
    updated_units = current_units.copy()
    
    # If status is 'AV', increment the level and add the unit if not already in the list
    if row['Apparatus Status'] == 'AV':
        current_level += 1
        if row['Apparatus ID'] not in updated_units:
            updated_units.append(row['Apparatus ID'])
    
    # If status is 'DP', decrement the level and remove the unit from the list if present
    elif row['Apparatus Status'] == 'DP':
        current_level = max(0, current_level - 1)  # Ensure level doesn't go below 0
        if row['Apparatus ID'] in updated_units:
            updated_units.remove(row['Apparatus ID'])
    
    # If status is 'ZZ' and remarks indicate sign-on, add to the list if not already present
    elif row['Apparatus Status'] == 'ZZ' and 'MDT SIGNON' in row['Remarks']:
        if row['Apparatus ID'] not in updated_units:
            updated_units.append(row['Apparatus ID'])
    
    # If status is 'ZZ' and remarks indicate sign-off, remove from the list if present
    elif row['Apparatus Status'] == 'ZZ' and 'STATUS: IQ TO ZZ' in row['Remarks']:
        if row['Apparatus ID'] in updated_units:
            updated_units.remove(row['Apparatus ID'])
            
    return current_level, updated_units






############

prompt = """

I'm working with raw 911 system apparatus status updates.  I have cleaned my dataset and have an example of a single ambulance unit "M301" during its 12 hour shift.

Each row corresponds to a status update: AV available, DP dispatched, ER en route, OS on scene, TR transporting, TC transport complete, IQ in quarters (back at base after shift, usually), and ZZ is logged in but not "in the system."

The goal is to track total available ambulance units throughout a given time period.

"""

prompt2 = """

No, let's have a status for every minute.

Instead, we should have a column called "level" which we can increment when a medic unit has an "AV" status update.  Alternatively we can decrement it 1 when a medic unit has a "DP" unit change.

Additionally, let's have another column called "available units."  When a unit has a "ZZ" status change with a remark of "MDT SIGNON" we can add that apparatus ID to the list of available units. Also, when a unit has a status change of "ZZ" with remark of " STATUS: IQ TO ZZ" we can remove it from the list.

"""
