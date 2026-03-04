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

def save_problem_to_file(id, problemDes, base_dir="/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"):
    # 创建以ID为名字的文件夹
    id_folder_path = os.path.join(base_dir, str(id))
    os.makedirs(id_folder_path, exist_ok=True)

    # 问题描述文件位置
    ProblemDes_path = os.path.join(id_folder_path, "ProblemDes")
    os.makedirs(ProblemDes_path, exist_ok=True)

    # 保存incorrectCode到对应的语言文件
    problem_file = os.path.join(ProblemDes_path, f"problem.txt")
    with open(problem_file, 'w', encoding='utf-8') as file:
        file.write(problemDes)


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
def extract_codes_and_save(test_data, base_dir="/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"):
    for item in test_data:
        id = item.get("id")
        incorrect_code = item.get("incorrectCode", "")
        # incorrect_code = item.get("buggy_code", "")
        ground_truth_code = item.get("groudTruthCode", "")

        problemDes = item.get("problemDescription", "")
        # ground_truth_code = item.get("solution", "")
        language = item.get("language", "")  # 获取语言类型
        # 保存数据到文件夹
        save_problem_to_file(id, problemDes, base_dir)


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


def get_ids_from_directory(directory):
    """ Return a set of IDs by listing directory names under a given directory """
    return set(os.listdir(directory))


def filter_json_data(json_path, ids_to_exclude, output_path):
    """ Filter JSON data by excluding certain IDs and write remaining data to a text file """
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Assuming data is a list of dictionaries
        filtered_data = [item for item in data if str(item.get('id')) not in ids_to_exclude]

        with open(output_path, 'w', encoding='utf-8') as file:
            for item in filtered_data:
                file.write(json.dumps(item) + '\n')

        print(f"Filtered data written to {output_path}")
    except Exception as e:
        print(f"Error occurred: {e}")


# 主逻辑
if __name__ == "__main__":
    # 设置文件路径
    input_filename = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_all.json'

    # 读取数据集
    data = read_json_file(input_filename)
    #
    # # 划分训练集和测试集
    # train_data, test_data = split_dataset(data)
    #
    # # 将训练集保存到txt中
    # write_train(train_data)
    #
    # 提取测试集的incorrectCode和groudTruthCode，并保存到文件
    extract_codes_and_save(data)
    #
    # base_directory = '/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_singlefault'
    # json_file_path = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_all.json'
    # output_file_path = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_newtrain.txt'
    #
    # # Get IDs from TutorCode_singlefault
    # ids_in_singlefault = get_ids_from_directory(base_directory)
    #
    # # Filter and write JSON data to a new file
    # filter_json_data(json_file_path, ids_in_singlefault, output_file_path)
