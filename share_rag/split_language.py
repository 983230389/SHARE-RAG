import os
import shutil
import json


def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


def split_language(root_dir, json_dir):
    # 获取所有以id命名的文件夹
    ids = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
    ]

    # 加载json文件
    json_file = os.path.join(json_dir, "DebugBench_all.json")
    try:
        data = read_json_file(json_file)

        # 遍历json中的所有条目
        for entry in data:
            id = entry.get("id")
            language = entry.get("language")

            # 如果当前id在目录中存在，则处理该id
            if str(id) in ids:
                # 获取该id对应的文件夹路径
                id_folder_path = os.path.join(root_dir, str(id))

                # 根据语言判断目标目录
                if language == "java":
                    target_dir = DebugBench_java_dir
                elif language == "python3":
                    target_dir = DebugBench_py_dir
                elif language == "cpp":
                    target_dir = DebugBench_cpp_dir
                else:
                    continue  # 如果语言不是这三种之一，跳过

                # 复制id对应的文件夹到目标目录
                destination_path = os.path.join(target_dir, str(id))
                shutil.copytree(id_folder_path, destination_path, dirs_exist_ok=True)
                print(f"Copied {id_folder_path} to {destination_path}")

    except Exception as e:
        print(f"Error processing JSON file: {e}")


# Example usage
root_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_test"  # 设置您的根目录路径
json_dir = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"  # 设置包含DebugBench_all.json的目录路径
DebugBench_java_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_java"
DebugBench_py_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_py"
DebugBench_cpp_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_cpp"

split_language(root_dir, json_dir)
