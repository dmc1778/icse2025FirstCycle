import os, re, json
import xml.etree.ElementTree as ET
from colorama import Fore, Back, Style, init
from itertools import permutations, product

ROOT_DIR = "/media/nima/SSD/stackexchange/extracted"


def write_dict(data, stage):
    if not os.path.exists(f'logs/stage{stage}/'):
        os.makedirs(f'logs/stage{stage}/')

    file_path = f"logs/stage{stage}/data.json"

    # Read existing content or create an empty list if the file doesn't exist
    try:
        with open(file_path, "r") as json_file:
            existing_data = json.load(json_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        existing_data = []
    
    existing_data.append(data)


    with open(file_path, "w") as json_file:
        json.dump(existing_data, json_file, indent=4)

    # with open(f"logs/stage{stage}/data.json", "a") as json_file:
    #     json.dump(data, json_file, indent=4)
    #     json_file.write(',')
    #     json_file.write('\n')

REG_PTR = re.compile(r'(\<row)')
tags_pattern = re.compile(r'Tags="([^"]*)"')

def match_co_existance_tag(patterns, unscape_tag):
    flag = False
    for pattern in patterns:
        if re.findall(pattern, unscape_tag):
            flag = True
            break
    return flag
        # re.findall(r'(tensorflow|TensorFlow|tensorFlow|Tensorflow|tf|TF|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|MXnet|python|Python|scikit-learn|sklearn|Sklearn|Scikit-learn|anaconda|Anaconda|conda|Conda)', unscape_tag[0])

def get_keyword_coexist_pattern():
    lib_keyword = "tensorflow|TensorFlow|tensorFlow|Tensorflow|tf|TF|PyTorch|pytorch|Pytorch|pyTorch|torch|MXNet|mxnet|MXnet|scikit-learn|sklearn|Sklearn|Scikit-learn".split('|')
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

def xml_parse():
    patterns = get_keyword_coexist_pattern()
    for root, dirs, files in os.walk(ROOT_DIR):
        for dir in dirs:
            current_dir = os.path.join(ROOT_DIR, dir)
            dir_files = os.listdir(current_dir)
            try:
                with open(os.path.join(current_dir, 'Posts.xml'), encoding="utf-8") as fp:
                    xml_string = fp.read()
                decomposed_posts = decompose_detections(xml_string.split('\n'))
                for post in decomposed_posts:
                    match = tags_pattern.search(post[0])
                    unscape_tag = unscape_tags(match)
                    if unscape_tag and match_co_existance_tag(patterns, unscape_tag[0]):
                        stage_1_dict = {
                                'file_path': current_dir,
                                'post': post[0],
                        }
                        write_dict(stage_1_dict, stage=1)
                        
                        if re.findall(r'(warning:|Warning)', post[0]):
                            stage_1_dict = {
                                    'file_path': current_dir,
                                    'post': post[0],
                            }
                            write_dict(stage_1_dict, stage=2)
            except (FileNotFoundError, json.decoder.JSONDecodeError):
                pass



if __name__ == '__main__':
    xml_parse()