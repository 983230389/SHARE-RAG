import shutil
import subprocess
import json
import logging
import os

def add_line_numbers(code):
    if code is None:
        return None  # 如果代码为空，则直接返回None
    lines = code.splitlines()  # 将代码分割成单独的行
    numbered_lines = [f"{i + 1} {line}" for i, line in enumerate(lines)]  # 为每一行添加行号
    return '\n'.join(numbered_lines)  # 将行重新组合成一个字符串并返回


# 设置日志记录
logging.basicConfig(level=logging.INFO)

data_list = []

for id in range(1, 1240):
    try:
        # 获取id对应的代码信息
        fetch_command = ['python3', 'tutorcode_api.py', 'fetch', str(id)]
        fetch_result = subprocess.run(fetch_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if fetch_result.returncode != 0:
            logging.error(f"获取ID {id} 时出错：{fetch_result.stderr}")
            continue
        fetch_data = json.loads(fetch_result.stdout)

        # 提取指定字段
        incorrectCode = fetch_data.get('incorrectCode')
        problemId = fetch_data.get('problemId')
        problemDescription = fetch_data.get('problemDescription')
        tutorGuidance = fetch_data.get('tutorGuidance')
        solutionDescription = fetch_data.get('solutionDescription')
        groudTruthCode = fetch_data.get('groudTruthCode')
        judgeResult = fetch_data.get("judgeResult")

        if not problemId:
            logging.error(f"ID {id} 未找到  problemId")
            continue

        # 获取第一个测试用例的数据
        testcase_command = ['python3', 'tutorcode_api.py', 'testcase', str(problemId), '1']
        testcase_result = subprocess.run(testcase_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if testcase_result.returncode != 0:
            logging.error(f"获取 promblemId {problemId} 的测试用例时出错： {testcase_result.stderr}")
            continue
        testcase_data = json.loads(testcase_result.stdout)
        input_data = testcase_data.get('input')
        output_data = testcase_data.get('output')

        # 组合数据
        id_data = {
            'id': id,
            'incorrectCode': incorrectCode,
            'problemId': problemId,
            'problemDescription': problemDescription,
            'tutorGuidance': tutorGuidance,
            'solutionDescription': solutionDescription,
            'groudTruthCode': groudTruthCode,
            'judgeResult':judgeResult,
            'input': input_data,
            'output': output_data
        }
        data_list.append(id_data)
        logging.info(f"已处理ID {id}")
    except Exception as e:
        logging.error(f"处理ID {id} 时出现异常：{e}")
        continue


# 创建保存路径
basePath = os.getcwd()
DataPath = os.path.join(basePath, "Data")
os.makedirs(DataPath, exist_ok=True)

# txt_file_path = os.path.join(DataPath, "Tutor_min.txt")
json_file_path = os.path.join(DataPath, "TutorCode.json")


with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(data_list, f, ensure_ascii=False, indent=4)

# 数据写入txt 文件
# with open(txt_file_path, "w", encoding="utf-8") as txt_file:
#     for index, data in enumerate(data_list):
#         # 将数据转换为 JSON 字符串，不添加缩进和空格
#         json_str = json.dumps(
#             data,
#             ensure_ascii=False,
#             separators=(',', ':')
#         )
#         # 写入文件
#         txt_file.write(json_str)
#         # 如果不是最后一个对象，添加逗号和换行符
#         if index < len(data_list) - 1:
#             txt_file.write(',\n')
#         else:
#             txt_file.write('\n')
#
# print(f"已生成 TXT 文件：{txt_file_path}")

# def clean():
#     if os.path.exists(DataPath):
#         shutil.rmtree(DataPath)
#     os.makedirs(DataPath)
#
# clean()
