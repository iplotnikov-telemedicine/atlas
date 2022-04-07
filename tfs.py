# import grequests
import requests
# from requests.auth import HTTPBasicAuth
import json
import os
import streamlit as st
from urllib.parse import quote
# import ssl
# ssl._create_default_https_context = ssl._create_unverified_context
import urllib3
urllib3.disable_warnings()

# PAT = 'm7s354d6d6sdtm2uzqkx2lyqy6owbtenqtsc5rsibet2h7ol6eta'
PAT = '5dari7aedmgetb7nfwclwve3hanqtkhkyulum6w7iqae5xko2dqq'


@st.experimental_singleton
def create_tfs_session():
    _session = requests.Session()
    _session.verify = False
    _session.trust_env = False
    os.environ['CURL_CA_BUNDLE'] = ''
    # _session.proxies = {"https":"10.2.176.162:8080", "http":"10.2.176.162:8080"}
    _session.auth = ('', PAT)
    _session.headers.update({"charset": "utf-8", "Content-Type": "application/json"})
    return _session


@st.experimental_memo(show_spinner=False)
def get_work_items(_session, text):
    url = f'''https://tfs.tele2.ru/tfs/Main/Tele2/_odata/v2.0/WorkItems?$filter=contains(Title,'{quote(text)}')&$select=WorkItemId,Title'''
    # area_path = r'Tele2\РПИ'
    # url = f'''https://tfs.tele2.ru/tfs/Main/Tele2/_odata/v2.0/WorkItems?$filter=contains(Title,'{quote(text)}')%20&%20AreaPath%20eq%20'{quote(area_path)}'&$select=WorkItemId,Title'''
    # print(url)
    json_response = _session.get(url)
    # print(json_response)
    response = json.loads(json_response.text)
    if 'value' in response:
        return response['value']
    else:
        return []


if __name__ == '__main__':
    cols = st.columns(2)
    search = cols[0].text_input('Поиск TFS по названию', key='text')
    if search:
        session = create_tfs_session()
        response = get_work_items(st.session_state.text)
        response



    # url = '''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/wit/wiql?api-version=5.0'''
    # data = {
        #     "query": f"Select [System.Id], [System.Title] From WorkItems Where [System.Title] CONTAINS '{text}' order by [System.CreatedDate] desc"
        # }
        # response = s.post(url, data=json.dumps(data))
    # for wit in response_dict.get('workItems'):
        #     id = wit.get('id')
        #     response = s.get(wit.get('url'))
        #     response_dict = json.loads(response.text)
        #     break


# def create_token():
#     with requests.Session() as s:
#         url = '''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/tokens/pats?api-version=6.1-preview.1'''
#         data = {
#             "displayName": "new_token",
#             "scope": "app_token",
#             "validTo": "2022-12-31T23:46:23.319Z",
#         }
#         response = s.post(url, data=json.dumps(data))
#         # response_dict = json.loads(response.text)
#     return response.text


# def grequests_response(urls):
#     reqs = (grequests.get(url) for url in urls)
#     jsons = (json.loads(resp.text) for resp in grequests.map(reqs))
#     return {json.get('id') : json.get('fields').get('System.Title') for json in jsons}




# def create_query():
#     url = '''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/wit/queries/11c7a4f9-52fd-4c97-af3e-4b358d609738?api-version=5.0'''
#     data = {
#     "name": "Tableau query",
#     "wiql": "Select [System.Id], [System.Title] From WorkItems Where [System.Title] CONTAINS 'Tableau' order by [System.CreatedDate] desc"
#     }
#     headers = {"charset": "utf-8", "Content-Type": "application/json"}
#     response = requests.post(url, auth=HTTPBasicAuth('', personal_access_token), data=json.dumps(data), headers=headers)
#     print(response.text)


# def update_query(text):
#     url = '''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/wit/queries/89a2e709-ba93-439c-8588-a2c29e89348a?api-version=5.0'''
#     data = {
#     "wiql": f"Select [System.Id], [System.Title] From WorkItems Where [System.Title] CONTAINS '{text}' order by [System.CreatedDate] desc"
#     }
#     headers = {"charset": "utf-8", "Content-Type": "application/json"}
#     response = requests.post(url, auth=HTTPBasicAuth('', personal_access_token), data=json.dumps(data), headers=headers)
#     print(response.text)






# id = '89a2e709-ba93-439c-8588-a2c29e89348a'
# url_by_id = '''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/wit/workitems/225786?api-version=6.0'''
# url = f'''https://tfs.tele2.ru/tfs/Main/Tele2/_apis/wit/wiql/{id}?api-version=5.0'''
# url = 'https://tfs.tele2.ru/tfs/Main/Tele2/_queries?tempQueryId=d0f233ff-93c4-4c37-a7d8-039bfd0062af'
# url = 'https://tfs.tele2.ru/tfs/Main/Tele2/_apis/search/workitemsearchresults?searchText=EDW&api-version=6.0'
# url = '''tfstest.tele2.ru/tfs/Main/Tele2/_odata/v3.0-preview/WorkItems?$select=WorkItemId,Title,WorkItemType,State,CreatedDate&$filter=startswith(Area/AreaPath,Tele2\Reports)'''
# url = '''https://tfs.tele2.ru/tfs/Main/Tele2/_queries/query?searchText=EDW'''


# data = json.dumps(data)
# print(data)





# result = json.loads(response.text)
# soup = BeautifulSoup(response.text, "html.parser")
# print(soup)
# answer = soup.find('a')


# print(response.text[224829:224829])
# print(response.text.find('EDW', 224829))

# from azure.devops.connection import Connection
# from msrest.authentication import BasicAuthentication
# import pprint

# # proxy = 'http://10.2.176.162:8080'
# # os.environ['http_proxy'] = proxy 
# # os.environ['HTTP_PROXY'] = proxy
# # os.environ['https_proxy'] = proxy
# # os.environ['HTTPS_PROXY'] = proxy

# # Fill in with your personal access token and org URL
# personal_access_token = 'm7s354d6d6sdtm2uzqkx2lyqy6owbtenqtsc5rsibet2h7ol6eta'
# organization_url = 'https://tfs.tele2.ru/tfs/Main'

# # Create a connection to the org
# credentials = BasicAuthentication('', personal_access_token)
# connection = Connection(base_url=organization_url, creds=credentials)

# # Get a client (the "core" client provides access to projects, teams, etc)
# core_client = connection.clients.get_core_client()

# # Get the first page of projects
# get_projects_response = core_client.get_projects()
# index = 0
# while get_projects_response is not None:
#     for project in get_projects_response.value:
#         pprint.pprint("[" + str(index) + "] " + project.name)
#         pprint(dir(project.name))
#         index += 1
#     if get_projects_response.continuation_token is not None and get_projects_response.continuation_token != "":
#         # Get the next page of projects
#         get_projects_response = core_client.get_projects(continuation_token=get_projects_response.continuation_token)
#     else:
#         # All projects have been retrieved
#         get_projects_response = None