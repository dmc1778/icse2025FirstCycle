import json


def convert():
    json_path_str = 'posts/stage2/data.json'
    data = json.load(json_path_str)
    print('')

if __name__ == '__main__':
    convert()