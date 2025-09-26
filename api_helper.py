import streamlit as st
import helpers.helper as helper
import requests as r
from urllib.parse import quote
import pandas as pd
from io import BytesIO



if 'authenticated' not in st.session_state:
    st.session_state.authenticated = None
if 'bcr_token' not in st.session_state:
    st.session_state.bcr_token = None
if 'bcr_username' not in st.session_state:
    st.session_state.bcr_username = None
if 'projects' not in st.session_state:
    st.session_state.projects = None
if 'queries' not in st.session_state:
    st.session_state.queries = None
if 'categories' not in st.session_state:
    st.session_state.categories = None
if 'tags' not in st.session_state:
    st.session_state.tags = None


st.image("img/bw_cision_logo.png", width=250)
st.header("BCR Asset ID Lookup", divider="rainbow")
st.markdown("##### Authenciate via Brandwatch to look up project/query/category/tag IDs.")

placeholder = st.empty()

# if not st.session_state.authenticated:
#     st.write()
#     with st.form("login", border=False, enter_to_submit=False):
#         col1, col2 = st.columns(2)
#         username = col1.text_input("Enter Brandwatch username")
#         password = col2.text_input("Enter Brandwatch password", type="password")
#         login_submit = st.form_submit_button("Log in")
            
#     if login_submit:
#         bcr_token = helper.get_bcr_token(username, password)
#         st.session_state.bcr_token = bcr_token
#         st.session_state.username = username
#         st.session_state.authenticated = True
    
if st.session_state.bcr_token:
    #st.caption(f"Your access token (valid for 364 days):&nbsp;&nbsp;**{st.session_state.bcr_token}**")
    placeholder.caption(f"*Currently logged in as {st.session_state.username}. Refresh the page to log out.*")
    st.write("")
    projects = helper.get_project_ids(st.session_state.bcr_token)
    if projects:
        st.session_state['projects'] = projects

    one, two = st.columns(2)
    #placeholder = two.empty()
    all_projects = {project['Name']: project['ID'] for project in st.session_state['projects']}
    selected_project = one.selectbox("Select a project below:", all_projects.keys(), index=None, placeholder="Select a project to fetch asset IDs...", label_visibility="collapsed")

    for p in st.session_state['projects']:
        if selected_project == p['Name']:
            project_id = p['ID']
            project_name = p['Name']
            st.session_state['project_id'] = project_id
            st.session_state['project_name'] = project_name

    if selected_project:
        two.badge(f"Project ID: {st.session_state['project_id']}")
        #if st.button(label="Fetch query, category, and tag IDs"):
        with st.spinner("In progress..."):
            queries = helper.fetch_queries(st.session_state.bcr_token, project_id)
            query_list = []
            for q in queries:
                query_info = {"query_name": q['name'],
                            "query_id": q['id']}
                query_list.append(query_info)
            
            query_df = pd.DataFrame(query_list)
            if 'query_id' in query_df:
                query_df['query_id'] = query_df['query_id'].astype(str)

            categories = helper.fetch_categories(st.session_state.bcr_token, project_id)
            cat_list = []
            for x in categories:
                for c in x['children']:
                    for r in c['rules']:
                        rule_info = {"parent_category_name": x['name'],
                                    "parent_category_id": x['id'],
                                    "sub_category_name": c['name'],
                                    "sub_category_id": c['id']}
                        cat_list.append(rule_info)
            cat_df = pd.DataFrame(cat_list)
            if 'parent_category_id' in cat_df:
                cat_df['parent_category_id'] = cat_df['parent_category_id'].astype(str)
            if 'sub_category_id' in cat_df:
                cat_df['sub_category_id'] = cat_df['sub_category_id'].astype(str)

            tags = helper.fetch_tags(st.session_state.bcr_token, project_id)
            tag_list = []
            for x in tags:
                for r in x['rules']:
                    rule_info = {"tag_name": x['name'],
                                    "tag_id": x['id']}
                    tag_list.append(rule_info)
            tag_df = pd.DataFrame(tag_list)
            if 'tag_id' in tag_df:
                tag_df['tag_id'] = tag_df['tag_id'].astype(str)

            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            query_df.to_excel(writer, index=False, sheet_name="queries")
            cat_df.to_excel(writer, index=False, sheet_name="categories")
            tag_df.to_excel(writer, index=False, sheet_name="tags")
            writer.close()
            processed_data = output.getvalue()

            tab1, tab2, tab3 = st.tabs(["Queries", "Categories", "Tags"])
            tab1.dataframe(query_df, hide_index=True)
            tab2.dataframe(cat_df, hide_index=True)
            tab3.dataframe(tag_df, hide_index=True)
            
            st.download_button(label="💾 Export all details (queries, categories, and tags)", data=processed_data, file_name=f"{project_name} - Assets.xlsx")
else:
    st.write()
    with st.form("login", border=False, enter_to_submit=False):
        col1, col2 = st.columns(2)
        username = col1.text_input("Enter Brandwatch username")
        password = col2.text_input("Enter Brandwatch password", type="password")
        login_submit = st.form_submit_button("Log in")
            
    if login_submit:
        bcr_token = helper.get_bcr_token(username, password)
        st.session_state.bcr_token = bcr_token
        st.session_state.username = username