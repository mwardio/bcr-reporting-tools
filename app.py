import streamlit as st


pages = [
    st.Page("report_builder.py", title="PS Report Builder"),
    st.Page("tetris.py", title="Ad Hoc Slide Maker"),
    st.Page("api_helper.py", title="API Helper (ID Lookup)"),
    st.Page("cat_level_metrics.py", title="Categeory-Level Metrics")
]

st.set_page_config(layout="centered", page_icon="img/bw_icon.png")

pg = st.navigation(pages)

pg.run()
