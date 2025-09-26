import streamlit as st
import pandas as pd
import time
from pg_corp_eu import *




reference_file = "pg_reference.xlsx"
if "fiscal_dates" in pd.ExcelFile(reference_file).sheet_names:
    fiscal_dates_df = pd.read_excel(reference_file, sheet_name="fiscal_dates")
if "regions" in pd.ExcelFile(reference_file).sheet_names:
    regions_df = pd.read_excel(reference_file, sheet_name="regions")
if "queries" in pd.ExcelFile(reference_file).sheet_names:
    queries_df = pd.read_excel(reference_file, sheet_name="queries")
if "streamlit" in pd.ExcelFile(reference_file).sheet_names:
    streamlit_options_df = pd.read_excel(reference_file, sheet_name="streamlit")

st.set_page_config(layout="centered", page_title="Report Builder")

st.image("img/bw_cision_logo.png", width=250)
st.header("Professional Services Report Builder", divider="rainbow")
st.write("")


region, period_start, period_end = None, None, None

one,two = st.columns(2)
client_selection = one.selectbox("Select a client:", streamlit_options_df['client'].unique(), index=None, placeholder="", label_visibility="visible")
report_selection = two.selectbox("Select a report:", streamlit_options_df[streamlit_options_df['client'] == client_selection]['report'], index=None, placeholder="", label_visibility="visible")

a,b,c = st.columns([0.5,0.25,0.25])
d,e = st.columns(2)

if report_selection == "No7 Beauty Barometer Monthly":
    st.info("Coming soon!")

elif report_selection == "P&G Corporate Quarterly":
    region = a.selectbox("Country:", regions_df['country'], index=None, placeholder="", label_visibility="visible")
    fiscal_year = b.selectbox("Fiscal year:", fiscal_dates_df['fiscal_year'].unique(), index=None, placeholder="", label_visibility="visible")
    fiscal_quarter = c.selectbox("Fiscal quarter:", ["Q1","Q2","Q3","Q4"], index=None, placeholder="", label_visibility="visible")

    if fiscal_year and fiscal_quarter:
        fiscal_period = f"{fiscal_quarter} FY {fiscal_year}"
        period_start = fiscal_dates_df[fiscal_dates_df['fiscal_period'] == fiscal_period]['start_date'].item()
        period_end = fiscal_dates_df[fiscal_dates_df['fiscal_period'] == fiscal_period]['end_date'].item()

        e.caption(f"*Date range to be covered: {period_start} – {period_end}*")

elif report_selection == "P&G Corporate Full Year":
    region = a.selectbox("Country:", regions_df['country'], index=None, placeholder="", label_visibility="visible")
    fiscal_year = b.selectbox("Fiscal year:", fiscal_dates_df['fiscal_year'].unique(), index=None, placeholder="", label_visibility="visible")
    if fiscal_year:
        fiscal_period = f"FY {fiscal_year}"
        period_start = fiscal_dates_df[fiscal_dates_df['fiscal_period'] == fiscal_period]['start_date'].item()
        period_end = fiscal_dates_df[fiscal_dates_df['fiscal_period'] == fiscal_period]['end_date'].item()
        d.caption(f"*Date range to be covered: {period_start} – {period_end}*")
    

if region and period_start and period_end:
    st.write("")
    button = st.empty()
    if button.button("Fetch data and generate report", type="secondary"):
        with st.spinner("sorcery in progress...", show_time=True):
            button.empty()
            #time.sleep(3)
            report_file = pg_corp_eu_report(region, fiscal_period, fiscal_dates_df, regions_df, queries_df)
            st.balloons()
            button.download_button("Done! Click to download PPTX 📥",
                                   type="primary",
                                   file_name=f"Procter Gamble Corp. {region} - {fiscal_period}.pptx",
                                   data=report_file)

