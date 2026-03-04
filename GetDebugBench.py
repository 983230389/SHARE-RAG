import json
import os
from collections import OrderedDict


# 读取JSON文件
def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def add_line_number(code):
    lines = code.splitlines()
    numbered_lines = [f"{i+1} {line}" for i, line in enumerate(lines)]
    return '\n'.join(numbered_lines)


def process_and_update_data(data):
    """
    处理 JSON 数据中的 solution 和 buggy_code 字段，为它们的代码添加行号。
    """
    for index, item in enumerate(data):
        item['id'] = index + 1
        # if 'solution' in item:
        #     item['solution'] = add_line_number(item['solution'])
        # if 'buggy_code' in item:
        #     item['buggy_code'] = add_line_number(item['buggy_code'])

        # 创建一个新的字典，确保 'id' 是第一个字段
        item = {'id': item['id'], **{k: v for k, v in item.items() if k != 'id'}}

        # 替换原始项
        data[index] = item
    return data

# 写入TXT文件
def write_txt_file(data_list, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for index, data in enumerate(data_list):
            # 使用 OrderedDict 来确保 id 字段排在第一个
            ordered_data = OrderedDict(
                [('id', data['id'])] + [(key, value) for key, value in data.items() if key != 'id'])
            # 将数据转换为 JSON 字符串，不添加缩进和空格
            json_str = json.dumps(
                ordered_data,
                ensure_ascii=False,
                separators=(',', ':')
            )
            # 写入文件
            file.write(json_str)
            # 如果不是最后一个对象，添加逗号和换行符
            if index < len(data_list) - 1:
                file.write(',\n')
            else:
                file.write('\n')

# 写入json文件
def write_json_file(data_list, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)

# 筛选符合条件的数据
def filter_data(data, category):
    filtered_data = []
    required_keys = ['slug', 'language', 'category', 'subtype', 'question', 'examples', 'constraints', 'solution',
                     'solution_explanation', 'buggy_code', 'bug_explanation']

    for item in data:
        if item['category'] == category:
            # 选择需要保留的字段
            filtered_item = {key: item[key] for key in required_keys if key in item}
            filtered_data.append(filtered_item)

    return filtered_data


# 主逻辑
if __name__ == "__main__":
    # 创建保存路径
    basePath = os.getcwd()
    DataPath = os.path.join(basePath, "Data")
    os.makedirs(DataPath, exist_ok=True)

    # output_filename = os.path.join(DataPath, "DebugBench.txt")
    output_filename = os.path.join(DataPath, "DebugBench_all.json")

    input_filename = 'Data/eval.json'  # 输入文件名
    # output_filename = 'filtered_data.json'  # 输出文件名
    category_to_filter = 'logic error'  # 要筛选的类别

    # 读取数据
    dataset = read_json_file(input_filename)

    # 过滤数据
    filtered_dataset = filter_data(dataset, category_to_filter)

    # 处理数据，为代码添加行号
    processed_dataset = process_and_update_data(filtered_dataset)

    # 写入数据到新的JSON文件
    # write_txt_file(processed_dataset, output_filename)
    write_json_file(processed_dataset, output_filename)
    print(f"Filtered data has been written to {output_filename}.")
