import os
import json
import logging
import re


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def get_alltests(root_dir, json_dir):
    # 获取所有在root_dir目录中的ID（这些ID对应每个子目录）
    ids = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
    ]

    # 遍历每个JSON文件并提取其中的输入和输出
    json_filename = os.path.join(json_dir, "DebugBench_all.json")  # 假设json文件名是data.json，您可以根据实际文件名修改
    try:
        data = read_json_file(json_filename)

        # 处理每个JSON对象
        for entry in data:
            id = entry.get("id")
            # 如果当前id在ids列表中，则处理它
            if str(id) in ids:
                logging.info(f"Processing ID {id}...")
                # 获取该ID对应的输入和输出目录
                inputs_dir = os.path.join(root_dir, str(id), "inputs")
                outputs_dir = os.path.join(root_dir, str(id), "outputs")

                # 创建目录
                os.makedirs(inputs_dir, exist_ok=True)
                os.makedirs(outputs_dir, exist_ok=True)

                # 提取输入输出数据
                examples = entry.get('examples', [])
                for i, example in enumerate(examples):
                    # 使用正则表达式提取 Input 和 Output，确保不包括 Explanation 部分
                    input_match = re.search(r"Input: (.*?)(?=\nOutput:)", example, re.DOTALL)
                    output_match = re.search(r"Output: (.*?)(?=\nExplanation:|$)", example, re.DOTALL)

                    if input_match and output_match:
                        input_data = input_match.group(1).strip()  # 获取input
                        output_data = output_match.group(1).strip()  # 获取output

                        # 保存到文件
                        input_file = os.path.join(inputs_dir, f"{i + 1}.in")
                        output_file = os.path.join(outputs_dir, f"{i + 1}.out")

                        with open(input_file, 'w', encoding='utf-8') as infile:
                            infile.write(input_data)

                        with open(output_file, 'w', encoding='utf-8') as outfile:
                            outfile.write(output_data)

                        logging.info(f"Saved input and output for example {i + 1} in ID {id}")

    except Exception as e:
        logging.error(f"Error processing JSON file: {e}")

def get_problem(root_dir, json_dir):
    # 获取所有在root_dir目录中的ID（这些ID对应每个子目录）
    ids = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
    ]

    # 遍历每个JSON文件并提取其中的输入和输出
    json_filename = os.path.join(json_dir, "DebugBench_all.json")  # 假设json文件名是data.json，您可以根据实际文件名修改
    try:
        data = read_json_file(json_filename)

        # 处理每个JSON对象
        for entry in data:
            id = entry.get("id")
            # 如果当前id在ids列表中，则处理它
            if str(id) in ids:
                logging.info(f"Processing ID {id}...")

                problem_dir = os.path.join(root_dir, str(id), "problemDes")
                # 创建目录
                os.makedirs(problem_dir, exist_ok=True)

                problem_file = os.path.join(problem_dir, f"problem.txt")

                promblem = entry.get('question')

                with open(problem_file, 'w', encoding='utf-8') as file:
                    file.write(promblem)

                logging.info(f"Saved")

    except Exception as e:
        logging.error(f"Error processing JSON file: {e}")


# Example usage
root_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_test"  # Set the appropriate root directory
json_dir = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"
setup_logging()
get_problem(root_dir, json_dir)
