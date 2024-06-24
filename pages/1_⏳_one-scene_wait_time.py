import streamlit as st

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.page_link("🏡_home_page.py", label="Home Page 🏡", icon="👈", use_container_width=True)
st.header("⏳ :green[On-scene wait times]", divider=True)

st.write("This is a simple web app that allows you to explore the Portland Fire data.")
