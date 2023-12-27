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

'''
You need to put four github access token in the following dictionaries
'''
from dotenv import load_dotenv
load_dotenv()

TOKEN0 = os.getenv("GIT_TOKEN1")
TOKEN1 = os.getenv("GIT_TOKEN2")
TOKEN2 = os.getenv("GIT_TOKEN3")
TOKEN3 = os.getenv("GIT_TOKEN4")

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

def get_version(sbody):
    version = []
    try:
        for j, item in enumerate(sbody):
            if 'TensorFlow version' in item:
                version.append(sbody[j+2])
                break
    except Exception as e:
        print(e)
    return version

def match_label(labels):
    label_flag = False
    for l in labels:
        if "type:bug" in l["name"] or "prtype:bugfix" in l["name"]:
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
            last_com, headers={
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

        warning_ = 'Warning:|warning:'
        patterns_device_bugs = r'(\bCUDA Out of Memory\b|\bCUDA out of memory\b|\bCUDA compilation error\b|\bGPU temperature\b|\bMixed precision training\b|\bVulkan\b|\bVulkan backend\b|\bAMP\b|\bgpu version mismatch\b|\bGPU version mismatch\b|\bgpu hangs\b|\bGPU hangs\b|\bdriver issue\b|\bgpu driver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bNVIDIA GPU\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bdevice placement\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
        title_match = False
        body_match = False

        if isinstance(commit["body"], str):
            if match_label(commit["labels"]):
                if re.findall(r"(tf\.)", commit["title"]) or re.findall(
                    r"(tf\.)", commit["body"]
                ):
                    comment_flag = parse_comment(
                        commit["comments_url"], current_token)

                    if re.findall(patterns_device_bugs, commit["title"]):
                        title_match = True
                    if re.findall(patterns_device_bugs, commit["body"]):
                        body_match = True
                        
                    sbody = commit['body'].split('\n')
                    
                    version = get_version(sbody)

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

                        if version:
                            data =  [currentRepo, commit["html_url"],commit["created_at"], version]
                        else:
                            data =  [currentRepo, commit["html_url"],commit["created_at"], 'No version']
                            
                        with open(
                            f"./issues/device/{currentRepo}.csv",
                            "a",
                            newline="\n",
                        ) as fd:
                            writer_object = csv.writer(fd)
                            writer_object.writerow(data)

        if i == len(first_100_commits) - 1:
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

    repo_list = ["https://github.com/tensorflow/tensorflow"]

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
            branchLink, headers={
                "Authorization": "token {}".format(current_token)}
        )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={
                    "Authorization": "token {}".format(current_token)}
            )

        if response.status_code != 200:
            tokens_status[current_token] = False
            current_token = select_access_token(current_token)
            response = requests_retry_session().get(
                branchLink, headers={
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
            patterns_device_bugs = r'(\bCUDA Out of Memory\b|\bCUDA out of memory\b|\bCUDA compilation error\b|\bGPU temperature\b|\bMixed precision training\b|\bVulkan\b|\bVulkan backend\b|\bAMP\b|\bgpu version mismatch\b|\bGPU version mismatch\b|\bgpu hangs\b|\bGPU hangs\b|\bdriver issue\b|\bgpu driver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bNVIDIA GPU\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bdevice placement\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
            title_match = False
            body_match = False

            for i, commit in enumerate(first_100_commits):
                if isinstance(commit["body"], str):
                    if match_label(commit["labels"]):
                        if re.findall(r"(tf\.)", commit["title"]) or re.findall(
                            r"(tf\.)", commit["body"]
                        ):
                            comment_flag = parse_comment(
                                commit["comments_url"], current_token
                            )
                            if re.findall(r"(tf\.)", commit["title"]) or re.findall(
                                r"(tf\.)", commit["body"]
                            ):
                                comment_flag = parse_comment(
                                    commit["comments_url"], current_token
                                )

                                if re.findall(
                                    patterns_device_bugs, commit["title"]
                                ):
                                    title_match = True
                                if re.findall(
                                    patterns_device_bugs, commit["body"]
                                ):
                                    body_match = True

                                _date = commit["created_at"]
                                sdate = _date.split("-")
                                tf_version = re.findall(
                                    r"(tf\s\d{1,2}[.]\d{1,2})", commit["body"]
                                )
                                print(sdate[0])
                                if title_match or body_match or comment_flag:
                                    _date = commit["created_at"]
                                    sdate = _date.split("-")

                                    with open(
                                        f"./issues/device/{r_prime[4]}.csv",
                                        "a",
                                        newline="\n",
                                    ) as fd:
                                        writer_object = csv.writer(fd)
                                        writer_object.writerow(
                                            [
                                                r_prime[4],
                                                commit["html_url"],
                                                commit["created_at"],
                                                tf_version,
                                            ]
                                        )
                    potential_commits = []


if __name__ == "__main__":
    main()