import json
import os
import re
import requests
import random
import datetime
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from csv import writer
from mine_comments import parse_comment
import csv
import pandas as pd
'''
You need to put four github access token in the following dictionaries
'''
from dotenv import load_dotenv
load_dotenv()

TOKEN1 = os.getenv("GIT_TOKEN1")
TOKEN2 = os.getenv("GIT_TOKEN2")
TOKEN3 = os.getenv("GIT_TOKEN3")
TOKEN4 = os.getenv("GIT_TOKEN4")
TARGET = os.getenv('TARGET')
PATTERN_LIST = os.getenv('PATTERN_LIST')

tokens = {
    0: TOKEN1,
    1: TOKEN2,
    2: TOKEN3,
    3: TOKEN4,
}

tokens_status = {
    TOKEN1: True,
    TOKEN2: True,
    TOKEN3: True,
    TOKEN4: True,
}


def match_label(labels):
    label_flag = False
    for l in labels:
        if "bug" in l["name"]:
            label_flag = True
    return label_flag


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


retries = 10
now = datetime.datetime.now()

def collect_labels(object):
    labels = []
    for l in object:
        labels.append(l['name'])
    return labels

def get_commits(
    keyword,
    last_com,
    page_number,
    potential_commits,
    current_token,
):

    page_number += 1

    print("Current page number is: {}".format(page_number))

    headers = {
            "Authorization": f"Bearer {current_token}"
        }

    params = {
            "q": f"{keyword} in:issue",
            "per_page": 100, 
        }
    
    if page_number == 1:

        issue_link = "https://api.github.com/search/issues"

        response = requests_retry_session().get(
            issue_link,
            params=params,
            headers=headers,
        )
    else:
        response = requests_retry_session().get(
            last_com,
            params=params,
            headers=headers
        )
        link_ = last_com

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            params=params,
            headers=headers
        )

    first_100_commits = json.loads(response.text)

    if len(first_100_commits['items']) == 1:
        return None
    for i, commit in enumerate(first_100_commits['items']):

        if TARGET == 'device':
            pattern = r'(\bCUDA Out of Memory\b|\bCUDA out of memory\b|\bCUDA compilation error\b|\bGPU temperature\b|\bMixed precision training\b|\bVulkan\b|\bVulkan backend\b|\bAMP\b|\bgpu version mismatch\b|\bGPU version mismatch\b|\bgpu hangs\b|\bGPU hangs\b|\bdriver issue\b|\bgpu driver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bdevice placement\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
        else:
            pattern = r"(FutureWarning:|Warning:|warning:)"
        title_match = False
        body_match = False

        if isinstance(commit["body"], str):
            if isinstance(commit["body"], str):
                    comment_flag = parse_comment(
                        commit["comments_url"], current_token)

                    title_match_keyword = []
                    body_match_keyword = []
                    if re.findall(pattern, commit["title"]):
                        title_match_keyword.append(re.findall(pattern, commit["title"]))
                        title_match = True
                    if re.findall(pattern, commit["body"]):
                        body_match_keyword.append(re.findall(pattern, commit["body"]))
                        body_match = True

                    if title_match_keyword or body_match_keyword:
                        print(f'I matched a keyword in title: {title_match_keyword}')
                        print(f'I matched a keyword in body: {body_match_keyword}')

                    _date = commit["created_at"]
                    sdate = _date.split("-")

                    if title_match or body_match or comment_flag:
                        _date = commit["created_at"]
                        sdate = _date.split("-")
                        print(
                            "Title status: {0}, Body status: {1}, Comment status: {2}".format(
                                title_match, body_match, comment_flag
                            )
                        )

                        data =  [commit["html_url"].split('/')[-3], commit["html_url"],commit["created_at"], 'No version']

                        with open(
                                f"./output/issues/{TARGET}/all_issues.csv",
                                "a",
                                newline="\n",
                            ) as fd:
                                writer_object = csv.writer(fd)
                                writer_object.writerow(data
                                )

        if i == len(first_100_commits['items']) - 1:
            if page_number == 53:
                print("here!")
            last_com = response.links["next"]["url"]

            potential_commits = []

            get_commits(
                keyword,
                last_com,
                page_number,
                potential_commits,
                current_token,
            )


def search_comit_data(c, commit_data):
    t = []

    for item in commit_data:
        temp = item.split("/")
        t.append("/" + temp[3] + "/" + temp[4] + "/")

    r_prime = c.split("/")
    x = "/" + r_prime[3] + "/" + r_prime[4] + "/"
    if any(x in s for s in t):
        return True
    else:
        return False


def select_access_token(current_token):
    x = ""
    if all(value == False for value in tokens_status.values()):
        for k, v in tokens_status.items():
            tokens_status[k] = True

    for k, v in tokens.items():
        if tokens_status[v] != False:
            x = v
            break
    current_token = x
    return current_token


def main():
    issue_link = "https://api.github.com/search/issues"

    current_token = tokens[0]
    for keyword in PATTERN_LIST.split(','):
        headers = {
            "Authorization": f"Bearer {current_token}"
        }

        
        params = {
            "q": f"{keyword} in:issue",
            "per_page": 100, 
        }

        response = requests.get(issue_link, headers=headers, params=params)

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
            
        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                issue_link,
                params=params,
                headers=headers
            )
            
            
        response_text = json.loads(response.text)
        page_number = 0
        if len(response_text['items']) >= 100:
            last_com = response.links["last"]["url"]
            get_commits(
                    keyword,
                    last_com,
                    page_number,
                    response_text['items'],
                    current_token,
                )
        else:
            if TARGET == 'device':
                pattern = r'(\bCUDA Out of Memory\b|\bCUDA out of memory\b|\bCUDA compilation error\b|\bGPU temperature\b|\bMixed precision training\b|\bVulkan\b|\bVulkan backend\b|\bAMP\b|\bgpu version mismatch\b|\bGPU version mismatch\b|\bgpu hangs\b|\bGPU hangs\b|\bdriver issue\b|\bgpu driver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bdevice placement\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
            else:
                pattern = r"(FutureWarning:|Warning:|warning:)"

            title_match = False
            body_match = False

            for issue in response_text['items']:
            
                comment_flag = parse_comment(issue["comments_url"], current_token)
                
                if re.findall(pattern, issue["title"]):
                    title_match = True
                if re.findall(pattern, issue["body"]):
                    body_match = True

                _date = issue["created_at"]
                sdate = _date.split("-")
                print(sdate[0])
                if title_match or body_match or comment_flag:
                    _date = issue["created_at"]
                    sdate = _date.split("-")
                    with open(f"./output/issues/{TARGET}/all_issues.csv","a",newline="\n",) as fd:
                        writer_object = csv.writer(fd)
                        writer_object.writerow([issue["html_url"].split('/')[-3],issue["html_url"],issue["created_at"],])
            potential_commits = []

if __name__ == "__main__":
    main()
