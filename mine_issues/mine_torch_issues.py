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

TOKEN0 = os.getenv("GIT_TOKEN0")
TOKEN1 = os.getenv("GIT_TOKEN1")
TOKEN2 = os.getenv("GIT_TOKEN2")
TOKEN3 = os.getenv("GIT_TOKEN3")
PARAM = os.getenv('STATE')

tokens = {
    0: TOKEN0,
    1: TOKEN1,
    2: TOKEN2,
    3: TOKEN3,
}

tokens_status = {
    TOKEN0: True,
    TOKEN1: True,
    TOKEN2: True,
    TOKEN3: True,
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
    githubUser,
    currentRepo,
    qm,
    page,
    amp,
    sh_string,
    last_com,
    page_number,
    branch_sha,
    potential_commits,
    current_token,
):

    page_number += 1

    print("Current page number is: {}".format(page_number))

    if page_number == 1:
        first_100_commits = (
            "https://api.github.com/repos/"
            + githubUser
            + "/"
            + currentRepo
            + "/issues"
            + qm
            + page
        )

        response = requests_retry_session().get(
            first_100_commits,
            
            headers={"Authorization": "token {}".format(current_token)},
        )
        link_ = first_100_commits
    else:
        response = requests_retry_session().get(
            last_com,
            
            headers={
                "Authorization": "token {}".format(current_token)}
        )
        link_ = last_com

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            
            headers={"Authorization": "token {}".format(current_token)},
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            
            headers={"Authorization": "token {}".format(current_token)},
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            
            headers={"Authorization": "token {}".format(current_token)},
        )

    if response.status_code != 200:
        tokens_status[current_token] = False
        current_token = select_access_token(current_token)
        response = requests_retry_session().get(
            link_,
            
            headers={"Authorization": "token {}".format(current_token)},
        )

    first_100_commits = json.loads(response.text)

    if len(first_100_commits) == 1:
        return None
    for i, commit in enumerate(first_100_commits):

        memory_related_rules_strict = r"(Warning:|warning:)"

        title_match = False
        body_match = False

        if isinstance(commit["body"], str):
            if re.findall(r"(Describe\sthe\sbug)", commit["body"]) or re.findall(
                r"(Bug)", commit["body"]
            ):
                if re.findall(r"(torch\.|)", commit["title"]) or re.findall(
                    r"(torch\.)", commit["body"]
                ):
                    comment_flag = parse_comment(
                        commit["comments_url"], current_token)

                    match_version = False
                    if re.findall(memory_related_rules_strict, commit["title"]):
                        title_match = True
                    if re.findall(memory_related_rules_strict, commit["body"]):
                        body_match = True
                        pattern = r"PyTorch version: \S+"
                        match_version = re.search(pattern, commit["body"])

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
                        if match_version:
                            extracted_version = match_version.group()
                            data =  [currentRepo, commit["html_url"],commit["created_at"], extracted_version]
                        else:
                            data =  [currentRepo, commit["html_url"],commit["created_at"], 'No version']

                        with open(
                                f"./issues/device/{currentRepo}.csv",
                                "a",
                                newline="\n",
                            ) as fd:
                                writer_object = csv.writer(fd)
                                writer_object.writerow(data
                                )

        if i == len(first_100_commits) - 1:
            if page_number == 53:
                print("here!")
            last_com = response.links["next"]["url"]

            potential_commits = []

            get_commits(
                githubUser,
                currentRepo,
                qm,
                page,
                amp,
                sh_string,
                last_com,
                page_number,
                branch_sha,
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

    repo_list = ["https://github.com/pytorch/pytorch"]

    if not os.path.exists("./issues"):
        os.makedirs("./issues")

    current_token = tokens[0]
    for lib in repo_list:
        x = []

        potential_commits = []

        r_prime = lib.split("/")

        qm = "?"
        page = "per_page=" + str(100)
        amp = "&"
        sh_string = "sha="

        branchLink = "https://api.github.com/repos/{0}/{1}/branches".format(
            r_prime[3], r_prime[4]
        )

        response = requests_retry_session().get(
            branchLink,
             
            headers={
                "Authorization": "token {}".format(current_token)}
        )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, 
                
                headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, 
                
                headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, 
                
                headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, 
                
                headers={
                    "Authorization": "token {}".format(current_token)}
            )

        branches = json.loads(response.text)

        selected_branch = random.choice(branches)
        branch_sha = selected_branch["commit"]["sha"]

        page_number = 0

        first_100_commits = (
            "https://api.github.com/repos/"
            + r_prime[3]
            + "/"
            + r_prime[4]
            + "/issues"
            + qm
            + page
        )

        response = requests_retry_session().get(
            first_100_commits,
            headers={"Authorization": "token {}".format(current_token)},
        )
        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                first_100_commits,
                
                headers={"Authorization": "token {}".format(current_token)},
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                first_100_commits,
                
                headers={"Authorization": "token {}".format(current_token)},
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                first_100_commits,
                
                headers={"Authorization": "token {}".format(current_token)},
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                first_100_commits,
                
                headers={"Authorization": "token {}".format(current_token)},
            )

        first_100_commits = json.loads(response.text)

        if len(first_100_commits) >= 100:
            last_com = response.links["last"]["url"]

            get_commits(
                r_prime[3],
                r_prime[4],
                qm,
                page,
                amp,
                sh_string,
                last_com,
                page_number,
                branch_sha,
                potential_commits,
                current_token,
            )

        else:

            warning_ = r"(warning:|Warning:)"
            title_match = False
            body_match = False

            for i, commit in enumerate(first_100_commits):
                if isinstance(commit["body"], str) and re.findall(
                    r"(Describe\sthe\sbug)", commit["body"]
                ):
                    if re.findall(r"(torch\.)", commit["title"]) or re.findall(
                        r"(torch\.)", commit["body"]
                    ):
                        comment_flag = parse_comment(
                            commit["comments_url"], current_token
                        )

                        if re.findall(warning_, commit["title"]):
                            title_match = True
                        if re.findall(warning_, commit["body"]):
                            body_match = True

                        _date = commit["created_at"]
                        sdate = _date.split("-")
                        print(sdate[0])
                        if title_match or body_match or comment_flag:
                            _date = commit["created_at"]
                            sdate = _date.split("-")
                            
        
                            with open(
                                    f"./issues/device/{r_prime[4]}_new.csv",
                                    "a",
                                    newline="\n",
                                ) as fd:
                                    writer_object = csv.writer(fd)
                                    writer_object.writerow(
                                        [
                                            r_prime[4],
                                            commit["html_url"],
                                            commit["created_at"],
                                        ]
                                    )
            potential_commits = []


if __name__ == "__main__":
    main()
