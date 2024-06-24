import os
import logging
log = logging.getLogger()


import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt




def load_uploaded_file(file):
    # log.debug(f"file: {file}")

    data = pd.read_csv(file, delimiter='\t', encoding='utf-8', encoding_errors='replace')

    # truncate miliseconds in "Activity Date" column (eg. 2023-11-01 00:07:16.553600 to 2023-11-01 00:07:16)
    data['Activity Date'] = data['Activity Date'].astype(str).str[:-5]
    data['Activity Date'] = pd.to_datetime(data['Activity Date'])

    data['Apparatus ID'] = data['Apparatus ID'].astype(str)
    data['Apparatus Status'] = data['Apparatus Status'].astype(str)
    data['Activity Code'] = data['Activity Code'].astype(str)
    data['Call Number'] = data['Call Number'].astype('Int64')
    data['Call Type'] = data['Call Type'].astype(str)
    data['Remarks'] = data['Remarks'].astype(str)


    st.divider()
    st.write("### :ok: dataset loaded")
    st.caption(f"Loaded {len(data):,} rows and {len(data.columns)} columns")
    with st.expander("Click to show truncated data header"):
        st.write(data.head(n=20))

    # st.caption('A caption with _italics_ :blue[colors] and emojis :sunglasses:') # TODO

    return data







def remove_unneeded_cols(df: pd.DataFrame) -> pd.DataFrame:
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

    with st.expander("Dropping unneeded columns..."):
        st.write(columns_to_remove)
        st.write(df.head(n=20))

    return df


def remove_unneeded_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["Activity Type"] != "M"] # messages
    df = df[df["Activity Type"] != "C"] # more messages?
    df = df[df["Activity Type"] != "L"] # LOGOFF remarks (duplicative - use #TODO for actual logoff tracking)
    df = df[df["Activity Type"] != "S"] # "signal" (eg. AUTO RADIO ALERTED PERSONNEL: MD208515 -  (22824))

    # drop the "Activity Type" column
    # df = df.drop(columns=["Activity Type"])

    with st.expander("Dropping rows with Activity Type: M, C, L, S"):
        st.write(df.head(n=20))

    return df


def remove_non_AMR(df: pd.DataFrame) -> pd.DataFrame:
    # stations_to_keep = [
    #     "715",
    #     "715B",
    #     "ZLZERO"
    # ]
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

    with st.expander("Only keeping AMR rows"):
        st.write(df.head(n=20))


    return df


def arrange_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df[[
        "Activity Date",
        "Apparatus ID",
        "Apparatus Status",
        "Activity Code",
        "Call Number",
        "Call Type",
        "Remarks"
    ]]

    with st.expander("Re-arranging columns"):
        st.write(df.head(n=20))

    return df










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

    with st.expander("Evaluating time-series to determine available units at any given time..."):
        st.write(df.head(n=20))

    return df




def talley_available_units(df: pd.DataFrame) -> pd.DataFrame:
    # Create a new column called 'level' and set it to 0
    df['ALS level'] = 0
    
    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        df.at[index, 'ALS level'] = len(row['ALS AV'])

    return df



def plot_that_shit(df: pd.DataFrame, save_fig: bool = True, resample_interval = None) -> None:
    import matplotlib.pyplot as plt

    # find the first day in this dataframe
    first_day = df['Activity Date'].dt.date.min()
    # keep all days past the first day
    df = df[df['Activity Date'].dt.date > first_day]


    # Set the timestamp column as the index
    df.set_index('Activity Date', inplace=True)

    if resample_interval:
        st.caption(f"doing resamping... {int(resample_interval)}")
        # Resample data into 1-minute intervals taking the mean of the 'value'
        # resampled_df = df['ALS level'].resample('1T').mean() # dots don't always connect
        # resampled_df = df['ALS level'].resample('5T').mean() # smoother lines
        resampled_df = df['ALS level'].resample(f'{resample_interval}T').min() # smoother lines
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
    # if save_fig:
        # plt.savefig(f'{RESULTS_DIR}/levels {first}-{last}.png', dpi=300, bbox_inches='tight')
    
    # return the plot as an image

    return plt.gcf() # return the plot as an image











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




def page():
    st.write("# AMR System Levels")

    uploaded_file = st.file_uploader("Choose a file")

    option = None
    with st.expander("Calculation parameters"):
        option = st.selectbox('Resampling interval (minutes)', ["Don't resample", '2', '5', '10', '15', '30'], index=2)
        st.text(f"option: {option}")
        if option == "Don't resample":
            option = None

    st.divider()


    if uploaded_file is not None:
        st.write(f"option: {option}")

        data = load_uploaded_file(uploaded_file)

        st.divider()
        st.write("### :technologist: cleaning data")

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
        fig = plot_that_shit(data, save_fig=False, resample_interval=option)
        st.pyplot(fig)

        # if 'processed_data' not in st.session_state:
            # st.session_state['processed_data'] = None

        # if st.button('Process'):
            # st.session_state['processed_data'] = process_data(data, option)

        # if st.session_state['processed_data'] is not None:
            # st.write(st.session_state['processed_data'])
