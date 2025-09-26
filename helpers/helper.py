import streamlit as st
import json
import requests as r
import pandas as pd
from io import BytesIO
from urllib.parse import quote

##############################
## BCR API HELPER FUNCTIONS ##
##############################

def get_user_info(bcr_token):
    header = {'authorization': f'bearer {bcr_token}'}
    user_info = r.get("https://api.brandwatch.com/me", headers=header).json()
    return user_info

def get_bcr_token(username, password):
    username_quoted = quote(username)
    url = f"https://api.brandwatch.com/oauth/token?username={username_quoted}&password={password}&grant_type=api-password&client_id=brandwatch-api-client"
    response = r.get(url)

    if response.status_code == 200:
        data = response.json()
        return data['access_token']
    else:
        st.error(f"Failed to retrieve token (status code: {response.status_code}). Check your login credentials and try again.")
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

def get_project_ids(access_token):
    headers = {"User-Agent": "Mozilla/5.0"}
    parameters = {"access_token": access_token}

    response = r.get(f'https://api.brandwatch.com/projects/summary', params=parameters, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        projects = [{"Name": project["name"], "ID": str(project["id"])} for project in data["results"]]
        return projects
    else:
        st.error(f"Failed to retrieve project IDs. Status code: {response.status_code}")
        return []

def fetch_queries(access_token, project_id):
    queries_url = f"https://api.brandwatch.com/projects/{project_id}/queries"
    auth = {"authorization": f"bearer {access_token}"}
    query_info = r.get(queries_url, headers = auth).json()
    return query_info['results']

def fetch_categories(access_token, project_id):
    categories_url = f"https://api.brandwatch.com/projects/{project_id}/rulecategories"
    auth = {"authorization": f"bearer {access_token}"}
    categories_info = r.get(categories_url, headers=auth)
    return categories_info.json()['results']

def fetch_tags(access_token, project_id):
    tags_url = f"https://api.brandwatch.com/projects/{project_id}/ruletags"
    auth = {"authorization": f"bearer {access_token}"}
    tags_info = r.get(tags_url, headers=auth)
    return tags_info.json()['results']

def fetch_author_lists(access_token, project_id):
    author_lists_url = f"https://api.brandwatch.com/projects/{project_id}/group/author/summary"
    auth = {"authorization": f"bearer {access_token}"}
    author_lists_info = r.get(author_lists_url, headers=auth).json()
    return author_lists_info["results"]

def fetch_site_lists(access_token, project_id):
    site_lists_url = f"https://api.brandwatch.com/projects/{project_id}/group/site/summary"
    auth = {"authorization": f"bearer {access_token}"}
    site_lists_info = r.get(site_lists_url, headers=auth).json()
    return site_lists_info["results"]

def upload_queries(bcr_token, user_docs):
    response = []
    for user_doc in user_docs:
        query_url = f"https://api.brandwatch.com/projects/{user_doc['projectId']}/queries"
        auth = {"authorization": f"bearer {bcr_token}"}
        data = {"booleanQuery": user_doc['boolean'],
                "name": user_doc['queryName'], # + ' - ' + date,
                "startDate": user_doc['startDate'],
                "languages": user_doc['languages'].split(', ') if not pd.isna(user_doc['languages']) else [],
                'contentSources': user_doc['contentSources'].split(', ') if not pd.isna(user_doc['contentSources']) else [],
                }
        create_query = r.post(query_url, headers = auth, json = data)
        create_query
        if 'errors' in create_query.json().keys():
            response.append({"projectID": str(user_doc['projectId']),
                             "queryName": user_doc['queryName'],
                             "issue": create_query.json()['errors'][0]['message']})
        elif 'id' not in create_query.json().keys():
            response.append({"projectID": str(user_doc['projectId']),
                             "queryName": user_doc['queryName'],
                             "issue": create_query.json()})
        # if 'id' in create_query.json().keys():
        #     message_response = f"Query with name of {user_doc['name']} is now in the account"
        # elif 'id' not in create_query.json().keys():
        #     message_response = f"There was an issue with your query named {user_doc['name']}. Check your sheet for any required edits"
    return response


def upload_tags(bcr_token, user_docs):
    all_tags = [x['tagName'] for x in user_docs]
    for user_doc in user_docs:
        if isinstance(user_doc['queryIDs'], int):
            user_doc['queries'] = user_doc['queryIDs']
        elif ',' in str(user_doc['queryIDs']):
            #user_doc['queries'] = user_doc['appliesTo'].split(',')
            user_doc['queries'] = [int(m) for m in user_doc['queryIDs'].split(',')] 
        else:
            user_doc['queries'] = None

    dupes = []
    uniques = []
    for x in all_tags:
        if x in uniques:
            dupes.append(x)
        elif x not in uniques:
            uniques.append(x)

    problem_tags = []
    for unique in uniques:
        tag_data = {"name":unique,"queryIds":None, 'rules':[]}
        for user_doc in user_docs:
            if user_doc['tagName'] == unique:
                filter = {'queryIds': user_doc['queries'], 'filter': {'search': user_doc['boolean']}}
                tag_data['rules'].append(filter)
        tag_url = f'https://api.brandwatch.com/projects/{user_doc["projectId"]}/ruletags'
        auth = {"authorization": f"bearer {bcr_token}"}
        tag_call = r.post(tag_url, json= tag_data, headers=auth)
        # if tag_call.status_code == 200:
        #     tag_id = tag_call.json()['id']
        #     backfill_url = f'https://api.brandwatch.com/projects/{user_doc["projectId"]}/bulkactions/ruletags/{tag_id}'#?earliest=2025-03-01
        #     headers = {'authorization': f'bearer {bcr_token}'}
        #     backfill = r.post(backfill_url, headers = headers)
        #     backfill
        # else:
        if tag_call.status_code != 200:
            error_messages = []
            for e in tag_call.json()['errors']:
                error_messages.append(e['message'])
            problem_tags.append({'tagName':unique, 'issue': error_messages})

    return problem_tags

 
def upload_categories(bcr_token, user_docs):
    for user_doc in user_docs:
        if isinstance(user_doc['queryIDs'], int):
            user_doc['queries'] = user_doc['queryIDs'] 
        elif ',' in str(user_doc['queryIDs']):
            #user_doc['queries'] = user_doc['appliesTo'].split(',')
            user_doc['queries'] = [int(m) for m in user_doc['queryIDs'].split(',')] 
        else:
            user_doc['queries'] = None

    all_markets = [x['parentCategoryName'] for x in user_docs]
    dupes = []
    uniques = []
    for x in all_markets:
        if x in uniques:
            dupes.append(x)
        elif x not in uniques:
            uniques.append(x)

    problem_cats = []
    for unique in uniques:
        unique_data = {'name': unique, 'children_raw': [], 'children':[]}
        for user_doc in user_docs:
            if user_doc['parentCategoryName'] == unique:
                if user_doc['queries'] is not None and 'enableCategoryMetrics' in user_doc and str.lower(user_doc['enableCategoryMetrics']) in ['y','yes','true']:
                    enable_cat_metrics = True
                else:
                    enable_cat_metrics = False
                raw_data = {'boolean': user_doc['boolean'], 'subcategoryName': user_doc['subcategoryName'], 'queryIds': user_doc['queries']}
                unique_data['children_raw'].append(raw_data)
        current_subcats = [z['subcategoryName'] for z in unique_data['children_raw']]
        dupe_subcats = []
        unique_subcats = []
        for current_subcat in current_subcats:
            if current_subcat in unique_subcats:
                dupe_subcats.append(current_subcat)
            elif x not in unique_subcats:
                unique_subcats.append(current_subcat)
        for unique_subcat in unique_subcats:
            child_info = {'name': unique_subcat,
                    'rules':[]}
            for raw_child in unique_data['children_raw']:
                if raw_child['subcategoryName'] == unique_subcat:
                    rule_data = {'queryIds': raw_child['queryIds'],'filter': {'queryId': None,'search': raw_child['boolean']}}
                    child_info['rules'].append(rule_data)
            unique_data['children'].append(child_info)
        final_json = {'name': unique,
                    'enableCategoryMetrics': enable_cat_metrics,
                    'queryIds': user_doc['queries'],
                    'multiple': True,
                    'children': unique_data['children']}
        upload_cats = f'https://api.brandwatch.com/projects/{user_doc["projectId"]}/rulecategories'
        headers = {'authorization': f'bearer {bcr_token}'}
        upload = r.post(upload_cats, headers=headers, json=final_json)#.json()
        
        if upload.status_code == 200:
            cat_id = upload.json()['id']
            backfill_url = f'https://api.brandwatch.com/projects/{user_doc["projectId"]}/bulkactions/rulecategories/{cat_id}'#?earliest=2024-03-01'
            headers = {'authorization': f'bearer {bcr_token}'}
            backfill = r.post(backfill_url, headers = headers)
            #backfill
        else:
            error_messages = []
            for e in upload.json()['errors']:
                error_messages.append(e['message'])
            problem_cats.append({'parentCategoryName':unique, 'subCategoryName':unique_subcat, 'issue': error_messages})
            st.error(f"Could not upload {unique}>>{unique_subcat}: {error_messages}")

    return problem_cats

 

def fetch_authors(token, project_id, query_id, start_date, end_date, cat_ids=None, tag_ids=None):
    base_url = f"https://api.brandwatch.com/projects/{project_id}/data/volume/topauthors/queries"
    params = {"queryId": query_id,
              "startDate": start_date,
              "endDate": end_date,
              "category": cat_ids,
              "tag": tag_ids,
              "limit": 1000,}
    header = {"authorization": f"bearer {token}"}
    call = r.get(base_url, params = params, headers = header)
    results = call.json()['results']
    my_authors = []
    for result in results:
        key, val = next(iter(result.items()))
        authordata = {"name" : val['authorName'],
                      "domain": val['domain'],
                      "volume" : val['volume']}
        my_authors.append(authordata)
    return my_authors


def fetch_category_metrics(token, project_id, query_id, start_date, end_date, cat_ids, tag_ids=None):
    ### Fetch CLM Sentiment
    clm_url = f"https://api.brandwatch.com/projects/{project_id}/data/volume/categories/categorySentiment"
    params = {'queryId': query_id,
            'startDate': start_date,
            'endDate': end_date,
            'tag': tag_ids,
            'dim1Args': cat_ids,
            'dim2Args': cat_ids}
    headers = {'authorization': f'bearer {token}'}
    clm_call = r.get(clm_url, headers=headers, params=params)
    results_sent = clm_call.json()['results']

    chart_sent = []
    for x in results_sent:
        name = x['name']
        data = {'Subcategory Name': name}
        for y in x['values']:
            value_data = {y['name'].title(): round(y['value'], 2)}
            data.update(value_data)
        chart_sent.append(data)

    for x in chart_sent:
        x['Total Volume'] = x['Negative'] + x['Neutral'] + x['Positive']

    ### Fetch CLM Prominence
    prom_url = f"https://api.brandwatch.com/projects/{project_id}/data/categoryProminenceSum/categories/queries"
    params = {'queryId': query_id,
            'startDate': start_date,
            'endDate': end_date,
            'tag': tag_ids,
            'dim1Args': cat_ids,
            'dim2Args': cat_ids}
    headers = {'authorization': f'bearer {token}'}
    prom_call = r.get(prom_url, headers=headers, params=params)
    results_prom = prom_call.json()['results']

    chart_prom = []
    for x in results_prom:
        name = x['name']
        data = {'Subcategory Name': name}
        for y in x['values']:
            value_data = {'Prominence Sum': round(y['value'], 2)}
            data.update(value_data)
        chart_prom.append(data)

    ### Calculate Avg Prominence
    df_sent = pd.DataFrame(chart_sent)
    df_prom = pd.DataFrame(chart_prom)
    merged_temp_query = df_sent.merge(df_prom)
    merged_dict = merged_temp_query.to_dict(orient='records')

    for x in merged_dict:
        if x['Total Volume'] != 0:
            x['Avg Prominence'] = round((x['Prominence Sum'] / x['Total Volume']), 2)
        else:
            x['Avg Prominence'] = 0

    df_combo = pd.DataFrame(merged_dict)
    final_chart = df_combo[df_combo['Total Volume'] > 0]

    return final_chart


def fetch_mentions(token, project_id, query_id, start_date, end_date, tags=None, xtags=None, cats=None, xcats=None):
    all_mentions = []
    mentions_url = f"https://api.brandwatch.com/projects/{project_id}/data/mentions?"
    mentions_params = {'queryId':query_id,
                       'startDate':start_date,
                       'endDate': end_date,
                       'tag': tags,
                       'category': cats,
                       'xtag': xtags,
                       'xcategory': xcats,
                       'pageSize':5000
                      }
    header = {"authorization": f"bearer {token}"}
    mentions_call = r.get(mentions_url, params=mentions_params, headers=header)
    print (mentions_call)
    mentions = mentions_call.json()['results']
    all_mentions.extend(mentions)
    cursor = mentions_call.json().get('nextCursor', None)
    i = 2
    while cursor:
        print (f'starting page {i} of your download')
        mentions_url = f"https://api.brandwatch.com/projects/{project_id}/data/mentions?"
        mentions_params = {'queryId':query_id,
                           'startDate':start_date,
                           'endDate': end_date,
                           'tag': tags,
                           'category': cats,
                           'xtag': xtags,
                           'xcategory': xcats,
                           'pageSize':5000,
                           'cursor': cursor
                          }
        mentions_call = r.get(mentions_url, params=mentions_params, headers=header)
        mentions = mentions_call.json()['results']
        all_mentions.extend(mentions)
        cursor = mentions_call.json().get('nextCursor', None)
        i += 1
    return all_mentions


def fetch_custom_sources(bcr_token):
    sources_url = "https://api.brandwatch.com/content/sources/list"
    header = {'authorization': f'bearer {bcr_token}'}
    sources = r.get(sources_url, headers=header)
    return sources.json()['results']

def create_custom_source(bcr_token, name, description=None, project_ids=None):
    header = {'authorization': f"bearer {bcr_token}", "Content-Type": "application/json"}
    data = {"name": name,
            "description": description,
            "projectIds": project_ids}
    response = r.post('https://api.brandwatch.com/content/sources', headers=header, json=data)
    return response.json()

def delete_custom_source(bcr_token, source_id):
    header = {'authorization': f'bearer {bcr_token}'}
    response = r.delete(f"https://api.brandwatch.com/content/sources/{source_id}", headers=header)
    return response.json()

def upload_content(bcr_token, user_docs, source_id):
    custom_base = [{k: v for k, v in e.items() if k not in ('date','contents','type','guid','title','language','author','url','geolocation','engagementType')} for e in user_docs]

    docsup = [{k: v for k, v in e.items() if k in ('date','contents','type','guid','title','language','author','url','geolocation','engagementType')} for e in user_docs]
    for x in range(0, len(docsup)):
        docsup[x]["custom"] = custom_base[x]

    chunks = [docsup[x:x+1000] for x in range(0, len(docsup), 1000)]
    for chunk in chunks:
        items = {"items": chunk,
                 "contentSource": source_id,
                 "requestUsage": "True"}
        header = {"authorization": f"bearer {bcr_token}"}
        upload_url = "https://api.brandwatch.com/content/upload"
        upload_mentions = r.post(upload_url, json=items, headers=header).json()
        with st.status("Uploading content..."):
            st.write(upload_mentions)
        #print (upload_mentions)


###############################
## MISC FUNCTIONS & SNIPPETS ##
###############################

def to_excel(df, sheet):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name=sheet)
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def bcr_auth_form():
    col1, col2 = st.columns(2)
    username = col1.text_input("Enter Brandwatch username")
    password = col2.text_input("Enter Brandwatch password", type="password")

    if st.button("Authenticate"):
        bcr_token = get_bcr_token(username, password)
        st.session_state.bcr_token = bcr_token
        st.session_state.authenticated = True
        st.session_state.username = username
        st.rerun()

@st.dialog("Impersonate another user")
def impersonate_modal():
    become_user = st.text_input("Enter username to become", label_visibility="collapsed", placeholder="Enter username to become", key="become_user_modal")
    if st.button("Impersonate", key="impersonate_modal"):
        if len(become_user) > 2:
            become_token = become_someone(become_user, st.session_state.bcr_token)
            if become_token is not None:
                st.toast(f"✅ Success!")
                st.session_state.bcr_token = become_token
                st.session_state.username = become_user
                st.session_state.become_user = become_user
                st.rerun()
            else:
                st.error(f"Failed to impersonate. Are you logged in to an admin account?")

@st.dialog(":warning: Restricted Access")
def app_login():
    st.markdown("#### For internal use by Brandwatch and Cision team members only.")
    st.button("Log in with Google", type="primary", on_click=st.login, use_container_width=True)
    st.link_button("&nbsp;&nbsp;&nbsp;Request access&nbsp;&nbsp;&nbsp;&nbsp;",
                   url="mailto:carlos@brandwatch.com;mark.ward@cision.com?subject=BCR API Web App Access&body=Hi! Could I please have access to the BCR API web app?",
                   use_container_width=True)