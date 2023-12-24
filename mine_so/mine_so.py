import os, re, json, csv
import xml.etree.ElementTree as ET
from colorama import Fore, Back, Style, init
from itertools import permutations, product
import threading, time
from queue import Queue
import platform

platform_ = platform.system()
if 'Linux' in platform_:
    ROOT_DIR = "/media/nima/SSD/stackexchange/extracted"
else:
    ROOT_DIR = "F:\\stackexchange\\extracted"

REG_PTR = re.compile(r'(\<row)')
tags_pattern = re.compile(r'Tags="([^"]*)"')
TIMEOUT = 60

def load_line_by_line(file_path):
    splited_lines = []
    with open(file_path, 'r', encoding="utf-8") as file:
        for line in file:
            splited_lines.append(line) 
    return splited_lines

def write_to_txt(file_path, value):
    with open(file_path, 'w') as file:
        file.write(str(value))

def write_csv(data, target, stage):
    if not os.path.exists(f'posts/stage{stage}/'):
        os.makedirs(f'posts/stage{stage}/')

    file_path = f"posts/stage{stage}/stage{stage}_{target}.csv"

    with open(file_path, 'a', newline='\n', encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

def match_pattern(patterns, unscape_tag, iterate_patterns=False):
    flag = False
    if iterate_patterns:
        for pattern in patterns:
            if re.findall(pattern, unscape_tag):
                flag = True
                break
    else:
        if re.findall(patterns, unscape_tag):
            matched_patterns = re.findall(patterns, unscape_tag)
            flag = True
    return flag
        # re.findall(r'(tensorflow|TensorFlow|tensorFlow|Tensorflow|tf|TF|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|MXnet|python|Python|scikit-learn|sklearn|Sklearn|Scikit-learn|anaconda|Anaconda|conda|Conda)', unscape_tag[0])

def get_keyword_coexist_pattern():
    lib_keyword = "tensorflow|TensorFlow|tensorFlow|Tensorflow|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|JAX|jax|MXnet".split('|')
    python_keyword = "python|Python".split('|')
    # keyword_permutations = list(permutations(keywords_list, 2))
    permutations_result = list(product(lib_keyword, python_keyword))

    regex_patterns = [f"{kw1}.*{kw2}|{kw2}.*{kw1}" for kw1, kw2 in permutations_result]
    return regex_patterns

def decompose_detections(splitted_lines):
    super_temp = []
    j = 0
    indices = []
    while j < len(splitted_lines):
        if REG_PTR.search(splitted_lines[j]):
            indices.append(j)
        j += 1

    if len(indices) == 1:
        for i, item in enumerate(splitted_lines):
            if i != 0:
                super_temp.append(item)
        super_temp = [super_temp]
    else:
        i = 0
        j = 1
        while True:
            temp = [] 
            for row in range(indices[i], indices[j]):
                temp.append(splitted_lines[row])
            super_temp.append(temp)
            if j == len(indices)-1:
                temp = [] 
                for row in range(indices[j], len(splitted_lines)):
                    temp.append(splitted_lines[row])
                super_temp.append(temp)
                break
            i+= 1
            j+= 1

    return super_temp

def unscape_tags(match):
    output = []
    if match:
        tags_value = match.group(1)
        tags_unescaped = re.sub(r'&lt;', '<', re.sub(r'&gt;', '>', tags_value))
        output.append(tags_unescaped)
    return output

def process_directory(queue, patterns_co_existence, patterns_other, target):
    GLOBAL_POST_COUNTER = 0 

    while True:
        current_dir = queue.get()
        if current_dir is None:
            break  # Signal to exit

        print(current_dir)
        dir_files = os.listdir(current_dir)

        for root, dirs, files in os.walk(ROOT_DIR):
            for dir in dirs:
                print(dir)
                current_dir = os.path.join(ROOT_DIR, dir)
                dir_files = os.listdir(current_dir)
                try:
                    xml_string = load_line_by_line(os.path.join(current_dir, 'Posts.xml'))
                    for idx, post in enumerate(xml_string):
                        if '<row' in post:
                            GLOBAL_POST_COUNTER += 1
                        match = tags_pattern.search(post)
                        unscape_tag = unscape_tags(match)
                        if unscape_tag and match_pattern(patterns_co_existence, unscape_tag[0], iterate_patterns=True):
                            stage_1_dict = [current_dir, post]
                            write_csv(stage_1_dict, target, stage=1,)
                            if match_pattern(patterns_other, post):
                                stage_1_dict = [current_dir, post]
                                write_csv(stage_1_dict, target,stage=2)
                                if re.findall(r'(warning:|Warning)', post) and target == 'warning':
                                    stage_1_dict = [current_dir, post]
                                    write_csv(stage_1_dict,target, stage=3)
                    write_to_txt(f'posts/postCounter_{target}.txt', GLOBAL_POST_COUNTER)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    print(f"{Back.RED}{'Sorry! the requested file does not exist'}{Style.RESET_ALL}")
                

def main():
    target = 'device'

    patterns_co_existence = get_keyword_coexist_pattern()

    if target == 'device':
        patterns_device_bugs = r'(\bCUDA Out of Memory\b|\bCUDA out of memory\b|\bCUDA compilation error\b|\bGPU temperature\b|\bMixed precision training\b|\bVulkan\b|\bVulkan backend\b|\bAMP\b|\bgpu version mismatch\b|\bGPU version mismatch\b|\bgpu hangs\b|\bGPU hangs\b|\bdriver issue\b|\bgpu driver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bNVIDIA GPU\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bdevice placement\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
    else:
        patterns_dependency = ['from sklearn.','from sklearn','import tensorflow as tf','import torch','from mxnet','from mxnet.gluon']
    
    queue = Queue()

    for root, dirs, files in os.walk(ROOT_DIR):
        for dir in dirs:
            queue.put(os.path.join(ROOT_DIR, dir))

    num_threads = min(4, queue.qsize()) 
    threads = [threading.Thread(target=process_directory, args=(queue,patterns_co_existence, patterns_device_bugs, target)) for _ in range(num_threads)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join(timeout=TIMEOUT)

        if thread.is_alive():
            print(f"Thread {thread.ident} exceeded the timeout and will be restarted for a new task.")
            queue.put(None)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()