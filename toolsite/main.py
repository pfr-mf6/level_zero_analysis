import os
import logging

from pipeline import logger
logger.setup_logging()
log = logging.getLogger()

import dotenv
dotenv.load_dotenv()

import streamlit as st


class Pages:
    TESTING_PAGE = "Testing Page"
    AMR_SYSTEM_LEVELS = "AMR system levels"
    ON_SCENE_WAIT_TIMES = "on-scene wait times"
    UNIT_HOUR_UTILIZATION = "Unit Hour Utilization"



def main():
    logging.getLogger("fsevents").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    st.set_page_config(page_title="My Webpage", page_icon=": tada: " , layout="wide" )

    with st.sidebar:
        st.title("Portland Fire and Rescue Data Analysis Tools")

        page_selection = (
                        'Select a tool',
                        Pages.AMR_SYSTEM_LEVELS,
                        Pages.ON_SCENE_WAIT_TIMES,
                        Pages.UNIT_HOUR_UTILIZATION,
                    ) if os.getenv("DEBUG", False) else (
                        'Select a tool',
                        Pages.ON_SCENE_WAIT_TIMES,
                    )
 
        startup_page = 1 if os.getenv("DEBUG", False) else 0

        page = st.selectbox("What data do you want to analyze? :point_down:",
                    page_selection,
                    index=startup_page # TODO: Comment out in production... otherwise set to tool you're working on
                    )

    if page == Pages.AMR_SYSTEM_LEVELS:
        from toolsite.pages.amr_system_levels import page as amr_system_levels
        amr_system_levels()
    elif page == Pages.ON_SCENE_WAIT_TIMES:
        from toolsite.pages.on_scene_wait_times import page as on_scene_wait_times
        on_scene_wait_times()
    elif page == Pages.UNIT_HOUR_UTILIZATION:
        from toolsite.pages.unit_hour_utilization import page as unit_hour_utilization
        unit_hour_utilization()
    else:
        from toolsite.pages.information import page as info_page
        info_page() #TODO
