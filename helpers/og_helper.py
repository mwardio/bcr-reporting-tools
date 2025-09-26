import streamlit as st
import json
import requests as r
import pandas as pd
from io import BytesIO
from urllib.parse import quote


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

def get_bcr_token(username, password):
    username_quoted = quote(username)
    url = f"https://api.brandwatch.com/oauth/token?username={username_quoted}&password={password}&grant_type=api-password&client_id=brandwatch-api-client"
    response = r.get(url)

    if response.status_code == 200:
        data = response.json()
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

def upload_queries(bcr_token, user_docs):
    for user_doc in user_docs:
        query_url = f"https://api.brandwatch.com/projects/{user_doc['project_id']}/queries"
        auth = {"authorization": f"bearer {bcr_token}"}
        data = {"booleanQuery": user_doc['boolean_query'],
                "name": user_doc['query_name'], # + ' - ' + date,
                "startDate": user_doc['data_start_date'],
                "languages": user_doc['languages'].split(', ') if not pd.isna(user_doc['languages']) else [],
                'contentSources': user_doc['content_sources'].split(', ') if not pd.isna(user_doc['content_sources']) else [],
                }
        create_query = r.post(query_url, headers = auth, json = data)
        user_doc['query_name']
        create_query
        if 'id' in create_query.json().keys():
            message_response = f"Query with name of {user_doc['query_name']} is now in the account"
            #st.success(message_response)
            st.success(f"Query with name of {user_doc['query_name']} is now in the account")
        elif 'id' not in create_query.json().keys():
            message_response = f"There was an issue with your query named {user_doc['query_name']}. Check your sheet for any required edits"
            #st.error(message_response)
            st.error(f"There was an issue with your query named {user_doc['query_name']}. Check your sheet for any required edits")
        #st.write(message_response)
    return message_response

def upload_tags(bcr_token, user_docs):
    all_tags = [x['tag_name'] for x in user_docs]
    for user_doc in user_docs:
        if pd.isna(user_doc['query_ids']):
            user_doc['queries'] = None
        elif user_doc['query_ids'] == 'all':
            user_doc['queries'] = None
        elif isinstance(user_doc['query_ids'], int):
            user_doc['queries'] = [int(user_doc['query_ids'])]
        elif ',' in user_doc['query_ids']:
            user_doc['queries'] = [int(m) for m in user_doc['query_ids'].split(',')] 

    dupes = []
    uniques = []
    for x in all_tags:
        if x in uniques:
            dupes.append(x)
        elif x not in uniques:
            uniques.append(x)

    for unique in uniques:
        tag_data = {"name":unique,"queryIds":None, 'rules':[]}
        for user_doc in user_docs:
            if user_doc['tag_name'] == unique:
                filter = {'queryIds': user_doc['queries'], 'filter': {'search': user_doc['boolean']}}
                tag_data['rules'].append(filter)
        tag_url = f'https://api.brandwatch.com/projects/{user_doc["project_id"]}/ruletags'
        auth = {"authorization": f"bearer {bcr_token}"}
        tag_call = r.post(tag_url, json= tag_data, headers=auth)
        unique
        tag_call

        if 'id' in tag_call.json().keys():
            tag_id = tag_call.json()['id']

            ### Backfill the tag
            backfill_url = f'https://api.brandwatch.com/projects/{user_doc["project_id"]}/bulkactions/ruletags/{tag_id}?earliest=2025-03-01'
            headers = {'authorization': f'bearer {bcr_token}'}
            backfill = r.post(backfill_url, headers = headers)
            st.success(f'Tag with name {unique} is now in the account')
            #print (backfill)
        
        elif 'id' not in tag_call.json().keys():
            st.error(f'There was an issue with tag with name {unique}. Please check your file')
            backfill = None
            #print (backfill)

    return backfill

def upload_categories(bcr_token, user_docs):
    
    ### Re-arrange values for queries applied
    for user_doc in user_docs:
        if pd.isna(user_doc['query_ids']):
            user_doc['queries'] = None
        elif user_doc['query_ids'] == 'all':
            user_doc['queries'] = None
        elif isinstance(user_doc['query_ids'], int):
            user_doc['queries'] = [int(user_doc['query_ids'])]
        elif ',' in user_doc['query_ids']:
            user_doc['queries'] = [int(m) for m in user_doc['query_ids'].split(',')] 

    #query_id = None

    all_markets = [x['parent_category_name'] for x in user_docs]
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
            if user_doc['parent_category_name'] == unique:
                raw_data = {'booleanQuery': user_doc['boolean'], 'subcategoryName': user_doc['sub_category_name'], 'queryIds': user_doc['queries']}
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
                    rule_data = {'queryIds': raw_child['queryIds'],'filter': {'queryId': None,'search': raw_child['booleanQuery']}}
                    child_info['rules'].append(rule_data)
            unique_data['children'].append(child_info)
        final_json = {'name': unique,
                    'queryIds': None,
                    'multiple': True,
                    'children': unique_data['children']}
        upload_cats = f'https://api.brandwatch.com/projects/{user_doc["project_id"]}/rulecategories'
        headers = {'authorization': f'bearer {bcr_token}'}
        upload = r.post(upload_cats, headers=headers, json=final_json)#.json()
        
        if upload.status_code == 200:
            cat_id = upload.json()['id']
            ### Backfill the category
            backfill_url = f'https://api.brandwatch.com/projects/{user_doc["project_id"]}/bulkactions/rulecategories/{cat_id}'#?earliest=2024-03-01'
            headers = {'authorization': f'bearer {bcr_token}'}
            backfill = r.post(backfill_url, headers = headers)
            print (backfill)
            st.success(f'Category with name of {unique} is now in your account and the request to backfill has been submitted')
        else:
            problem_cats.append(unique)
            st.error(f'There was an issue with category named {unique}. Review your spreadsheet')



# CONTENT CREATION FUNCTION

def account_content(bcr_token, content_source_name):
    #source = input("Enter the name of your source")
    base_url = "https://api.brandwatch.com/content/sources"
    items = {"name": content_source_name,
            "description": "Custom Data"}
    header = {"authorization": f"bearer {bcr_token}"}
    creation = r.post(base_url, json=items, headers=header)
    print (creation.json())
    name = (creation.json()['name'])
    csid = str((creation.json()['id']))
    #print (name + " " + csid)
    #print (creation.json()['id'])
    return creation.json()['id']

def project_content(bcr_token):
    source = input("Enter the name of your source")
    project = input("Enter your project id")
    base_url = "https://api.brandwatch.com/content/sources"
    items = {"name": source,
            "description": "Custom Data",
            "projectIds": project}
    header = {"authorization": f"bearer {bcr_token}"}
    creation = r.post(base_url, json=items, headers=header)
    #print (creation.json())
    name = (creation.json()['name'])
    csid = str((creation.json()['id']))
    print (name + " " + csid)   

# SOURCE LISTING FUNCTION

def my_sources(bcr_token):
    base_url = "https://api.brandwatch.com/content/sources/list"
    header = {"authorization": f"bearer {bcr_token}"}
    sourceinfo = r.get(base_url, headers = header)
    source = sourceinfo.json()
    results = source['results']
    return results

# DOCUMENT UPLOAD FUNCTIONS

def simpleupload(bcr_token):
    contentsourceid = input("Enter your content source id")
    excelfile = input("Enter the name of your Excel file")
    excelname = excelfile+".xlsx"
    document_df = pd.read_excel(excelname)
    user_docs = document_df.to_dict("records")
    chunks = [user_docs[x:x+1000] for x in range(0, len(user_docs), 1000)]
    for chunk in chunks:
        items = {"items": chunk,
                 "contentSource": contentsourceid,
                 "requestUsage": "True"}
        header = {"authorization": f"bearer {bcr_token}"}
        upload_url = "https://api.brandwatch.com/content/upload"
        upload_mentions = r.post(upload_url, json=items, headers=header).json()
        print (upload_mentions)

def complexupload(bcr_token, user_docs, content_source_id):
    #contentsourceid = input("Enter your content source id")
    #excelfile = input("Enter the name of your Excel file")
    #excelname = excelfile+".xlsx"
    #document_df = pd.read_excel(excelname)
    #user_docs = document_df.to_dict("records")
    
    custom_base = [{k: v for k, v in e.items() if k != 'date' and k != 'contents' and k != 'type' and k != 'guid' and k != 'title' and k!= 'language' and k != 'author' and k != 'url' and k != 'geolocation' and k != 'engagementType'} for e in user_docs]
#print (custom)
    docsup = [{k: v for k, v in e.items() if k == 'date' or k == 'contents' or k == 'guid' or k == 'title' or k == 'language' or k == 'author' or k == 'url' or k == 'geolocation' or k == 'engagementType'} for e in user_docs]
    for x in range(0, len(docsup)):
        docsup[x]["custom"] = custom_base[x]

    chunks = [docsup[x:x+1000] for x in range(0, len(docsup), 1000)]
    for chunk in chunks:
        items = {"items": chunk,
                 "contentSource": content_source_id,
                 "requestUsage": "True"}
        header = {"authorization": f"bearer {bcr_token}"}
        upload_url = "https://api.brandwatch.com/content/upload"
        upload_mentions = r.post(upload_url, json=items, headers=header).json()
        print (upload_mentions)



def fetch_authors(bcr_token, project_id, query_id, start_date, end_date):
    base_url = f"https://api.brandwatch.com/projects/{project_id}/data/volume/topauthors/queries"
    params = {"queryId": query_id,
              "startDate": start_date,
              "endDate": end_date,
             "limit": 1000,}
    header = {"authorization": f"bearer {bcr_token}"}
    call = r.get(base_url, params = params, headers = header)
    results = call.json()['results']
    my_authors = []
    for result in results:
        key, val = next(iter(result.items()))
        authordata = {"name" : val['authorName'],
                    "volume" : val['volume'],
                    "domain": val['domain']}
        my_authors.append(authordata)
    return my_authors