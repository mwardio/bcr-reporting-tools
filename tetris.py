import streamlit as st
import json
import requests as r
import pandas as pd
from io import BytesIO
from urllib.parse import quote
import helpers.og_helper as og_helper
import helpers.tetris_helper as tetris_helper
from datetime import datetime

import requests as r
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from pptx.util import Inches, Pt



### BCR Auth


def get_bcr_token(username, password):
    username_quoted = quote(username)
    url = f"https://api.brandwatch.com/oauth/token?username={username_quoted}&password={password}&grant_type=api-password&client_id=brandwatch-api-client"
    response = r.get(url)

    if response.status_code == 200:
        data = response.json()
        print (data)
        return data['access_token']
    else:
        st.error(f"Failed to retrieve token. Status code: {response.status_code}")
        return None

def become_someone(become_user, access_token):
    become_params = {"username": become_user,
        "grant_type": "api-become",
        "client_id": "brandwatch-api-client",
        "access_token": access_token}
    response = r.post("https://api.brandwatch.com/oauth/token", become_params)
    if response:
        return response.json()["access_token"]
    else:
        return None


### BCR Data Collection

def fetch_data(bcr_token, project_id, data_source_type, query_id, parent_categories, locations, content_sources, x_parent_categories, start_date, end_date, dim2Args:list):
        auth = {'authorization': f'bearer {bcr_token}'}
        url = f"https://api.brandwatch.com/projects/{project_id}/data/volume/all/categories"
        params = {'anyParentCategory': parent_categories,
                'startDate': start_date,
                'endDate': end_date,
                data_source_type: query_id,
                'location': locations,
                'pageType': content_sources,
                'xparentCategory': x_parent_categories,
                'dim2Args': dim2Args
                }
        actual_call = r.get(url, headers = auth, params=params)
        full_url = actual_call.request.url
        debug_call = actual_call.json()
        return actual_call.json()['results']


### Formatting

### Chart Generation

### Slide Generation



left_co, cent_co,last_co = st.columns(3)
with last_co:
    st.image('https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/Liverpool_FC.svg/640px-Liverpool_FC.svg.png', width=95)
with left_co:
    st.image('https://cdn.mos.cms.futurecdn.net/TaLfnqQU3Pz7J7qqrSkuBd.png', width=125)
#with left_co:
    #st.image('https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXc1N3Q4bnlidXF6MXg1bnpndXBzajR0bnl3NndieDFnZjlrNm92YiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/MOSebUr4rvZS0/giphy.gif', width=125)

#st.title("nameTBD - Need a PPT from BCR? Visit Anfield Road...")
#st.header("This module will allow you BCR data from your BCR dashboard in power point charts.")

st.markdown(
    """
    <h1 style='font-size: 32px;'>nameTBD...</h1>
    <h3 style='font-size: 20px; color: grey;'>This module will allow you to generate PowerPoint slides with BCR data charts.</h3>
    """,
    unsafe_allow_html=True



)

### Initialize authentication with null values

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'bcr_token' not in st.session_state:
    st.session_state.bcr_token = None
if 'username' not in st.session_state:
    st.session_state.username = None

placeholder = st.empty()

df = pd.DataFrame({'options': ['Yes', 'No']})

# Display login form if not already authenticated
if not st.session_state.authenticated:
    username = st.text_input("Enter Brandwatch username")
    password = st.text_input("Enter Brandwatch password", type="password")
    if st.button("Authenticate"):
        bcr_token = og_helper.get_bcr_token(username, password)
        st.session_state.bcr_token = bcr_token
        st.session_state.authenticated = True
        st.session_state.username = username
        st.rerun()


# Everything below will show only if authenticated
else:
    placeholder.caption(f"*Currently logged in as {st.session_state.username}. Refresh the page to log out.*")
    # Option to impersonate another user
    with st.expander("Impersonate another user (optional)", expanded=False):
        become_user = st.text_input("Enter username to become")
        if st.button("Impersonate"):
            if len(become_user) > 2:
                become_token = og_helper.become_someone(become_user, st.session_state.bcr_token)
                if become_token is not None:
                    placeholder.success(f"Now impersonating {become_user}.")
                    st.session_state.bcr_token = become_token
                    st.session_state.username = become_user
                else:
                    st.error(f"Failed to impersonate. Make sure you're logged in to an admin account.")
            else:
                placeholder.success(f"Currently logged in as {st.session_state.username}. Refresh the page to log out.")

df_workflows = pd.DataFrame({'options_workflow': ['No7 Monthly', 'P&G Report', 'From Spreadsheet']})

if st.session_state.authenticated:
    c,a,b = st.columns([0.5,0.25,0.25])
    option_flow = c.selectbox('What are you looking to download?', df_workflows['options_workflow'])

    if option_flow == 'From Spreadsheet':
        st.warning("*Spreadsheet must follow specific formatting -- [click here to download a template](https://mward.io)*")
        #a,b = st.columns(2)
        start_date = a.date_input('Enter your start date', format="YYYY-MM-DD", max_value='today', value=None)
        end_date = b.date_input('Enter your end date', format="YYYY-MM-DD", max_value='today', value=None)
        # start_date = str(start_date)
        # end_date = str(end_date)
    
        if start_date and end_date:
            #template_status = st.text_input('Do you have the template? (Y/N)')
            # st.download_button(
            #             label="Spreadsheet must follow specific formatting - click here to download a template",
            #             data=open("templates/input_template.xlsx", "rb"),
            #             file_name="input_template.xlsx"
            # )
            #if template_status == 'Y':
            # show file uploader
            #st.warning("*Spreadsheet must follow specific formatting -- [click here to download a template](https://mward.io)*")
            file_input = st.file_uploader("Upload data template file here", type=['csv', 'xlsx'])
            if file_input is not None:
                #file = pd.read_excel(file_input, sheet_name='Slide 1')
                #companies = file.to_dict(orient='records')
                with st.spinner("sorcery in progress", show_time=True):
                    pptx_file = tetris_helper.gen_pptx_from_bcr_xlsx(st.session_state.bcr_token, start_date, end_date, file_input)
                    st.balloons()
                    st.download_button(
                        label="📥 Click to download PPTX",
                        type="primary",
                        data=pptx_file,
                        file_name="report.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )