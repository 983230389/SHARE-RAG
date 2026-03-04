import difflib
import os

def compare_files(buggy_file_path, correct_file_path, output_path):
    """
    Compare the provided code files and identify erroneous lines.
    """
    with open(buggy_file_path, 'r', encoding='utf-8') as f:
        buggy_lines = [line.rstrip() for line in f.readlines()]

    with open(correct_file_path, 'r', encoding='utf-8') as f:
        correct_lines = [line.rstrip() for line in f.readlines()]

    differ = difflib.Differ()
    diff = list(differ.compare(correct_lines, buggy_lines))

    error_lines = []
    correct_line_num = 0
    buggy_line_num = 0

    for line in diff:
        if line.startswith(' '):
            correct_line_num += 1
            buggy_line_num += 1
        elif line.startswith('-'):
            correct_line_num += 1
        elif line.startswith('+'):
            error_lines.append(buggy_line_num + 1)
            buggy_line_num += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in error_lines:
            f.write(str(line) + '\n')

    return error_lines


def find_buggy_file(buggy_dir, valid_exts):
    """
    在 buggyCode 目录中查找 buggy_code.xxx
    """
    for file in os.listdir(buggy_dir):
        name, ext = os.path.splitext(file)
        if name == "buggy_code" and ext in valid_exts:
            return file, ext
    return None, None


def process_directory(base_dir):
    valid_extensions = ['.cpp', '.java', '.py']

    for id_folder in os.listdir(base_dir):
        id_folder_path = os.path.join(base_dir, id_folder)
        if not os.path.isdir(id_folder_path):
            continue

        buggy_folder = os.path.join(id_folder_path, "buggyCode")
        correct_folder = os.path.join(id_folder_path, "correctCode")

        if not (os.path.exists(buggy_folder) and os.path.exists(correct_folder)):
            continue

        # 1️⃣ 找 buggy_code 文件及其后缀
        buggy_file, ext = find_buggy_file(buggy_folder, valid_extensions)
        if buggy_file is None:
            continue

        # 2️⃣ 根据后缀匹配 true_code
        correct_file = f"true_code{ext}"

        buggy_path = os.path.join(buggy_folder, buggy_file)
        correct_path = os.path.join(correct_folder, correct_file)
        output_path = os.path.join(buggy_folder, "fault_lines.txt")

        if os.path.exists(correct_path):
            compare_files(buggy_path, correct_path, output_path)
        else:
            print(f"[Warning] Missing {correct_file} in {correct_folder}")


if __name__ == "__main__":
    base_directory = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_Test"
    process_directory(base_directory)
