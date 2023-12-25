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
TAG_PATTERN = re.compile(r'Tags="([^"]*)"')
TAG_CONTENT = re.compile('Tags=((.|\n)*?)&gt;')

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
    if not os.path.exists(f'output/posts/stage{stage}/'):
        os.makedirs(f'output/posts/stage{stage}/')

    file_path = f"output/posts/stage{stage}/stage{stage}_{target}.csv"

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
    lib_keyword = "deep learning|neural network|tensorflow|TensorFlow|tensorFlow|Tensorflow|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|JAX|jax|MXnet".split('|')
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

def get_tags(queue, patterns_co_existence, patterns_other, target):
    GLOBAL_POST_COUNTER = 0
    while True:
        current_dir = queue.get()
        if current_dir is None:
            break 
        print(current_dir)
        xml_string = load_line_by_line(os.path.join(current_dir, 'Posts.xml'))
        for idx, post in enumerate(xml_string):
            if '<row' in post:
                GLOBAL_POST_COUNTER += 1
                #post = '''<row Id="1" PostTypeId="1" AcceptedAnswerId="3" CreationDate="2016-08-02T15:39:14.947" Score="11" ViewCount="819" Body="&lt;p&gt;What does &quot;backprop&quot; mean? Is the &quot;backprop&quot; term basically the same as &quot;backpropagation&quot; or does it have a different meaning?&lt;/p&gt;&#xA;" OwnerUserId="8" LastEditorUserId="2444" LastEditDate="2019-11-16T17:56:22.093" LastActivityDate="2021-07-08T10:45:23.250" Title="What is &quot;backprop&quot;?" Tags="&lt;neural-networks&gt;&lt;backpropagation&gt;&lt;terminology&gt;&lt;definitions&gt;" AnswerCount="5" CommentCount="0" ContentLicense="CC BY-SA 4.0" />'''
                match = TAG_PATTERN.search(post)
                unscape_tag = unscape_tags(match)
                if unscape_tag:
                    tags_split = unscape_tag[0].split('><')
                    if len(tags_split) > 1:
                        if re.findall(r'()', unscape_tag[0]):
                            write_csv(unscape_tag,'tags', stage=1)

def process_directory(queue, patterns_co_existence, patterns_other, target):
    GLOBAL_POST_COUNTER = 0 
    while True:
        current_dir = queue.get()
        if current_dir is None:
            break  # Signal to exit

        print(current_dir)
        try:
            xml_string = load_line_by_line(current_dir)
            for idx, post in enumerate(xml_string):
                if '<row' in post:
                    GLOBAL_POST_COUNTER += 1
                match = TAG_PATTERN.search(post)
                unscape_tag = unscape_tags(match)
                # if unscape_tag and match_pattern(patterns_co_existence, unscape_tag[0], iterate_patterns=True):
                if unscape_tag and re.findall("(deep learning|neural network|tensorflow|TensorFlow|tensorFlow|Tensorflow|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|JAX|jax|MXnet)", unscape_tag[0]):
                    stage_1_dict = [current_dir, post]
                    write_csv(stage_1_dict, target, stage=1,)
                    if match_pattern(patterns_other, post):
                        stage_1_dict = [current_dir, post]
                        write_csv(stage_1_dict, target,stage=2,)
                        if re.findall(r'(warning:|Warning)', post) and target == 'warning':
                            stage_1_dict = [current_dir, post]
                            write_csv(stage_1_dict,target, stage=3,)
            write_to_txt(f'output/posts/postCounter_{target}.txt', GLOBAL_POST_COUNTER)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            print(f"{Back.RED}{'Sorry! the requested file does not exist'}{Style.RESET_ALL}")
                

def main():
    target = 'device'

    patterns_co_existence = get_keyword_coexist_pattern()

    if target == 'device':
        patterns_device_bugs = r'(\bERROR: OpenGL error\b|\bfail\b|ROCm fails|ROCm runtime|NCCL error\b|CPU error\b|\bmkldnn error\b|\brocm driver error\b|\bGPUassert\b|\bDLA_RUNTIME Error\b|\bCUDA compilation error\b|\bCUDA MMU fault\b|\bGPU temperature\b|\bVulkan error\b|\bvulkan validation error\b|\bOpenGL Error\b|\bVulkan errors\b|\bGPU version mismatch\b|\bGPU hangs\b|\bdriver issue\b|\bGPU driver issue\b|\bGPU memory issue\b|\bTensorRT error\b|\bGPU compatibility\b|\bcuDNN error\b|\bCUDA error\b|\bGPU support\b|\bGPU error\b|\bGPU utilization\b|\bGPU memory\b)'
    else:
        patterns_dependency = ['from sklearn.','from sklearn','import tensorflow as tf','import torch','from mxnet','from mxnet.gluon']
    
    queue = Queue()

    for root, dirs, files in os.walk(ROOT_DIR):
        for dir in dirs:
            p = os.path.join(ROOT_DIR, dir, 'Posts.xml')
            p = p.replace("\\\\", "\\")
            if os.path.isfile(p):
                queue.put(os.path.join(ROOT_DIR, dir, 'Posts.xml'))

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