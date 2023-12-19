import json
import pandas as pd


def convert():
    json_path_str = 'posts/stage1/stage1_data.csv'
    data = pd.read_csv(json_path_str)
    for idx, row in data.iterrows():
        print(row.iloc[1])

if __name__ == '__main__':
    convert()