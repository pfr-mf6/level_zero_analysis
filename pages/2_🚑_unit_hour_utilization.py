import streamlit as st

st.set_page_config(
    # page_title="Hello World"
    layout="wide",
    initial_sidebar_state="collapsed",
)

cols_sm = st.columns((1, 4))
with cols_sm[0]:
    with st.container(border=True):
        st.page_link("🏡_home_page.py", label="Home Page 🏡", icon="👈", use_container_width=True)



st.header("⏳ :violet[Unit Hour Utilization]", divider=True)

st.write("This is a simple web app that allows you to explore the Portland Fire data.")
