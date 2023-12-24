import json
from datetime import date, timedelta
import os
import requests as r
import time, requests
import math
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

TOKEN1 = os.getenv("GIT_TOKEN1")
TOKEN2 = os.getenv("GIT_TOKEN2")
TOKEN3 = os.getenv("GIT_TOKEN3")
TOKEN4 = os.getenv("GIT_TOKEN4")

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

def get_repos(_link, per_page, page_num, first_repo, counter, lib):
    repo_list = []
    try:
        response = r.get(_link, headers={'Authorization': 'token {TOKEN1}'})
        response = json.loads(response.text)
        for i, item in enumerate(response['items']):
            if response['items'][i+1]['id'] == first_repo:
                return repo_list
            else:
                print(lib)
                print(f'Total number of repositories extracted so far ---> {counter}')
                repo_list.append(item['html_url'])
                counter += 1
    except Exception as e:
        print(e)
        page_num += 1
        _link = f"https://api.github.com/search/repositories?q={lib}%20in:name,description+created:2018-01-01..2018-01-31&python?language=python&sort=stars&per_page={per_page}&page={page_num}"
        get_repos(_link, per_page, page_num, first_repo ,counter, lib)

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

def write_list_to_txt4(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')

def write_list_to_txt2(data, filename):
    with open(filename+".txt", "a") as file:
        for row in data:
            file.write(row+'\n')

def determine_page_number(lib, v , per_page):
    _pre_link = f"https://api.github.com/search/repositories?q={lib}%20in:name,description+created:{v}&python?language=python&sort=stars&per_page={per_page}"
    response = requests_retry_session().get(_pre_link, headers={"Authorization": "token {}".format('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')})
    print(response.status_code)       
    response = json.loads(response.text)
    x = response['total_count']
    return x 

def main():
    page_num = 1
    per_page = 100
    k = 0
    i = 0

    # libs = [
    #     ['tensorflow', tensor_pg_size], 
    #     ['pytorch',torch_pg_size],
    #     ['keras',keras_pg_size],
    #     ['numpy',numpy_pg_size],
    #     ['pandas',pandas_pg_size],
    #     ['sklearn',sklearn_pg_size]
    #     ]
    libs = ['deep learning']
    years = [2020, 2021, 2022, 2023]

    for lib in libs:
        for item in years:
            start_dt = date(item, 1, 1)
            end_dt = date(item, 12, 29)
            d_list = []
            for dt in daterange(start_dt, end_dt):
                d_list.append(dt.strftime("%Y-%m-%d"))
            i = 0
            j = 6
            while(j < len(d_list)):
                try:
                    repo_list = []
                    v = d_list[i]+'..'+d_list[j]
                    i = j+1
                    j = j+7
                    pg_size = determine_page_number(lib, v , per_page)

                    for p in range(1, pg_size+1):
                        _link = f"https://api.github.com/search/repositories?q={lib}%20created:{v}&python?language=python&sort=stars&per_page={per_page}&page={p}"
                        time.sleep(2)
                        response = r.get(_link, headers={'Authorization': 'token {}'.format('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')})
                            
                        response = json.loads(response.text)

                        if response['total_count'] == 0:
                            print('Could not get any result!')
                        else:
                            print("Extracting from {0}, Year {1}, Period {2}, Page {3}".format(lib, item, v, p))
                            for x, rep in enumerate(response['items']):
                                #if rep['watchers_count'] >= 200:
                                if not os.path.exists('output/repos/'):
                                    os.makedirs('output/repos/')
                                write_list_to_txt4(rep['html_url'], f'output/repos/{lib}.txt')
                except Exception as e:
                    print(e)

if __name__ == '__main__':
    main()