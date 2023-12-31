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

from dotenv import load_dotenv
load_dotenv()

TOKEN0 = os.getenv("GIT_TOKEN0")
TOKEN1 = os.getenv("GIT_TOKEN1")
TOKEN2 = os.getenv("GIT_TOKEN2")
TOKEN3 = os.getenv("GIT_TOKEN3")
TARGET = os.getenv('TARGET')

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

if TARGET == 'device':
    pattern = r'(\bERROR: OpenGL error\b|\bfail\b|ROCm fails|ROCm runtime|NCCL error\b|CPU error\b|\bmkldnn error\b|\brocm driver error\b|\bGPUassert\b|\bDLA_RUNTIME Error\b|\bCUDA compilation error\b|\bCUDA MMU fault\b|\bGPU temperature\b|\bVulkan error\b|\bvulkan validation error\b|\bOpenGL Error\b|\bVulkan errors\b|\bGPU version mismatch\b|\bGPU hangs\b|\bdriver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
else:
    pattern = r"(FutureWarning:|Warning:|warning:)"

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


def parse_comment(first_100_commits, current_token):
    match_flag = False
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

    if first_100_commits:
        try:
            for i, com in enumerate(first_100_commits):

                body_match_sec = re.findall(pattern, com["body"])

                if body_match_sec:
                    match_flag = True
        except Exception as e:
            print(e)

    return match_flag