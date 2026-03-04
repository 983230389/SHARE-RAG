import json
import random
import os
import shutil


def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


# 创建文件夹并保存数据到文件
def save_code_to_file(id, incorrect_code, ground_truth_code, base_dir="/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"):
    # 创建以ID为名字的文件夹
    id_folder_path = os.path.join(base_dir, str(id))
    os.makedirs(id_folder_path, exist_ok=True)

    # 错误代码文件位置
    buggyCode_path = os.path.join(id_folder_path, "buggyCode")
    os.makedirs(buggyCode_path, exist_ok=True)

    # 正确代码文件位置
    correctCode_path = os.path.join(id_folder_path, "correctCode")
    os.makedirs(correctCode_path, exist_ok=True)

    # 根据语言类型决定文件扩展名
    # if language == 'cpp':
    #     ext = '.cpp'
    # elif language == 'java':
    #     ext = '.java'
    # elif language == 'python3':
    #     ext = '.py'
    # else:
    #     raise ValueError(f"Unsupported language: {language}")

    # 保存incorrectCode到对应的语言文件
    incorrect_code_file = os.path.join(buggyCode_path, f"buggy_code.cpp")
    with open(incorrect_code_file, 'w', encoding='utf-8') as file:
        file.write(incorrect_code)

    # 保存groundTruthCode到对应的语言文件
    ground_truth_code_file = os.path.join(correctCode_path, f"true_code.cpp")
    with open(ground_truth_code_file, 'w', encoding='utf-8') as file:
        file.write(ground_truth_code)


# 按 8:2 划分数据集
def split_dataset(data, train_ratio=0.8):
    # 只保留id在1到590之间的数据
    filtered_data = [item for item in data if 1 <= item['id'] <= 1239]
    # filtered_data = [item for item in data if 1 <= item['id'] <= 590]
    random.shuffle(filtered_data)  # 随机打乱数据
    split_index = int(len(filtered_data) * train_ratio)
    train_data = filtered_data[:split_index]
    test_data = filtered_data[split_index:]
    return train_data, test_data


# 提取incorrectCode和groudTruthCode
def extract_codes_and_save(data, base_dir="/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_all"):
    for item in data:
        id = item.get("id")
        incorrect_code = item.get("incorrectCode", "")
        # incorrect_code = item.get("buggy_code", "")
        ground_truth_code = item.get("groudTruthCode", "")
        # ground_truth_code = item.get("solution", "")
        language = item.get("language", "")  # 获取语言类型
        # 保存数据到文件夹
        save_code_to_file(id, incorrect_code, ground_truth_code, base_dir)


def write_train(train_data, base_dir="Data"):
    txt_file_path = os.path.join(base_dir, "TutorCode_train.txt")

    # 数据写入txt文件
    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        for index, data in enumerate(train_data):
            # 将数据转换为 JSON 字符串，不添加缩进和空格
            json_str = json.dumps(
                data,
                ensure_ascii=False,
                separators=(',', ':')
            )
            # 写入文件
            txt_file.write(json_str)
            # 如果不是最后一个对象，添加逗号和换行符
            if index < len(train_data) - 1:
                txt_file.write(',\n')
            else:
                txt_file.write('\n')

    print(f"已生成 TXT 文件：{txt_file_path}")



def clean(base_dir="Data"):
    for i in range(1, 591):
        # 生成以 id 为名称的文件夹路径
        id_folder_path = os.path.join(base_dir, str(i))
        # 检查文件夹是否存在
        if os.path.exists(id_folder_path):
            # 删除该文件夹及其中的所有内容
            shutil.rmtree(id_folder_path)
            print(f"已删除文件夹: {id_folder_path}")
        else:
            print(f"文件夹 {id_folder_path} 不存在")


# 主逻辑
if __name__ == "__main__":
    # 设置文件路径
    input_filename = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_all.json'

    # 读取数据集
    data = read_json_file(input_filename)

    # 提取测试集的incorrectCode和groudTruthCode，并保存到文件
    extract_codes_and_save(data)

