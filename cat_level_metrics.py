import streamlit as st
import helpers.bcr_helper as helper
import json
import requests as r
import pandas as pd
from io import BytesIO
from urllib.parse import quote


if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'bcr_token' not in st.session_state:
    st.session_state.bcr_token = None
if 'username' not in st.session_state:
    st.session_state.username = None

def main():
    st.header("BCR Category Level Metrics", divider="rainbow")
    st.markdown("##### View or download category level sentiment and prominence metrics.")

    placeholder = st.empty()

    ## Display login form if not already authenticated
    if not st.session_state.authenticated:
        st.write("")
        helper.bcr_auth_form()

    ## Everything below will show only if authenticated
    else:
        placeholder.caption(f"_Currently logged in as {st.session_state.username}. Refresh the page to log out._")
        with st.expander("Impersonate another user (optional)", expanded=False):
            a,b = st.columns([0.6,0.4])
            become_user = a.text_input(label="", placeholder="Enter username to become", label_visibility="collapsed")
            if b.button("Impersonate"):
                if len(become_user) > 2:
                    become_token = helper.become_someone(become_user, st.session_state.bcr_token)
                    if become_token is not None:
                        placeholder.success(f"Now impersonating {become_user}.")
                        st.session_state.bcr_token = become_token
                        st.session_state.username = become_user
                    else:
                        st.error(f"Failed to impersonate. Make sure you're logged in to an admin account.")
                else:
                    placeholder.success(f"Currently logged in as {st.session_state.username}. Refresh the page to log out.")
        st.write("")
    
        projects = helper.get_project_ids(st.session_state.bcr_token)
        if projects:
            st.session_state['projects'] = projects

        col1, col2, = st.columns([0.6,0.4])
        all_projects = {project['Name']: project['ID'] for project in st.session_state['projects']}
        selected_project = col1.selectbox("Select a project to load options:", all_projects.keys(), index=None, placeholder="Select a project to load options...", label_visibility="collapsed")

        for p in st.session_state['projects']:
            if selected_project == p['Name']:
                project_id = p['ID']
                project_name = p['Name']
                # st.session_state['project_id'] = project_id
                # st.session_state['project_name'] = project_name

        # Confirm a project has been selected and present workflow options
        if not selected_project:
            st.stop()
            
        st.session_state['categories'] = helper.fetch_categories(st.session_state.bcr_token, project_id)
        #all_cats = {cat['name']: cat['id'] for cat in st.session_state['categories']}
        clm_cats = {cat['name']: cat['id'] for cat in [cat for cat in st.session_state['categories'] if 'enableCategoryMetrics' in cat and cat['enableCategoryMetrics'] == True]}
        if len(clm_cats) == 0:
            st.error("The selected project has no categories with category level metrics enabled.")
            st.stop()
        query_id = None
        with st.form("clm_form", border=False, enter_to_submit=False):
            st.session_state['queries'] = helper.fetch_queries(st.session_state.bcr_token, project_id)
            all_queries = {query['name']: query['id'] for query in st.session_state['queries']}
            one, two, three = st.columns([0.6,0.2,0.2])
            selected_query = one.selectbox("Select a query:", all_queries.keys(), index=None, placeholder="", label_visibility="visible")
            for q in st.session_state['queries']:
                if q['name'] == selected_query: query_id = q['id']

            start_date = two.date_input("Start date:", value=None, max_value="today", format="MM/DD/YYYY")
            end_date = three.date_input("End date:", value=None, max_value="today", format="MM/DD/YYYY")

            selected_cats = st.multiselect("", clm_cats.keys(), placeholder="Select parent categories to include...", help="Only categories with CLM enabled will be shown here", label_visibility="collapsed")
            cat_ids = []
            for c in st.session_state['categories']:
                for s in selected_cats:
                    if s == c['name']: cat_ids.append(c['id'])
            cat_ids = ','.join(map(str, cat_ids))

            st.session_state['tags'] = helper.fetch_tags(st.session_state.bcr_token, project_id)
            all_tags = {tag['name']: tag['id'] for tag in st.session_state['tags']}
            selected_tags = st.multiselect("", all_tags.keys(), placeholder="Filter by tags (optional)...", label_visibility="collapsed")
            tag_ids = []
            for t in st.session_state['tags']:
                for s in selected_tags:
                    if s == t['name']: tag_ids.append(t['id'])
            tag_ids = ','.join(map(str, tag_ids))

            clm_form_submit = st.form_submit_button("Fetch category level metrics")
        
        if clm_form_submit:
            if query_id is None:
                st.error("You must select a query first!")
                st.stop()
            if selected_cats is None:
                st.error("You must select at least one category to include!")
                st.stop()
            cat_metrics = helper.fetch_category_metrics(st.session_state.bcr_token, project_id, query_id, start_date, end_date, cat_ids, tag_ids)
            cat_df = pd.DataFrame(cat_metrics)
            st.dataframe(cat_df, hide_index=True)
            st.download_button(label="💾 Download spreadsheet", data=helper.to_excel(cat_df), file_name=f"{project_name}_Category_Metrics.xlsx")


main()