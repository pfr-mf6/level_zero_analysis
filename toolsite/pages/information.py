import os

import streamlit as st


DATA_TYPES_AND_COLUMNS = """
## Data Types
Blah blah blah...

## Columns

| Column Name | Description |
| ----------- | ----------- |
| `Activity Type`   | |
|                   | <blank> |
|                   | S - 'signal' |
|                   | M - 'message' |
|                   | C - 'comms (between dispatchers?)' |
| `Apparatus Status` | |
|                   | <blank> |
|                   | DP - 'dispatched' |
|                   | EN - 'enroute' |
|                   | OS - 'on scene' |
|                   | OG - 'staged' |
|                   | TR - 'transporting' |
|                   | TC - 'transport complete' |
|                   | AV - 'available' |
|                   | IQ - 'in quarters' |
|                   | ZZ - 'no status but on board' |
|                   | FF - 'Crew members riding in to hopital with AMR' |
|                   | NA - 'OOS with code' |
| `Activity Code`   | |
|                  | <blank> |
|                  | CM - ??? |
|                  | 7P - 'personnel (AMR lunch break taken at end of shift)' |
|                  | 7C - 'AMR Company Code 1 (aka private transport)' |
|                  | 90 - ?? |
|                  | 91 - ?? |
|                  | 98 - ?? |
|                  | 99 - ?? |

"""

ASSET_FOLDER = os.path.join(os.path.dirname(__file__), "assets")

def page():
    st.markdown("# Welcome to your personal Data Analysis Suite")
    st.write("Select an Analysis method from the sidebar on the left.")

    st.image(os.path.join(ASSET_FOLDER, "pf&r-logo.png"), width=200)

    with st.expander("How to export data from 'remote CAD'"):
        image_column, text_column = st.columns ( (1, 2) )

        with image_column:
            st.image("https://picsum.photos/200")
        
        with text_column:
            st.write("This is a column of text")
    
    with st.expander("Explain data types and columns"):
        st.write(DATA_TYPES_AND_COLUMNS)



############## DEBUG TESTING ONLY ##############
    if not os.getenv("DEBUG", False):
        return

    st.write("https://www.markdownguide.org/extended-syntax/")
    st.write("# Testing purposes only")

    st.warning('This is a warning', icon="⚠️")
    # with st.spinner('Wait for it...'):
    #     time.sleep(5)

    import time
    progress_text = "Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.02)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()

    st.caption('A caption with _italics_ :blue[colors] and emojis :sunglasses:') # TODO

