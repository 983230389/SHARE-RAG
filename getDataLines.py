import os
import json

# ---------- Part 1: 统计 reverse_labels 平均长度 ----------
def avg_reverse_labels_length(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_len = 0
    count = 0

    for item in data:
        if "reverse_labels" in item and isinstance(item["reverse_labels"], list):
            total_len += len(item["reverse_labels"])
            count += 1

    avg_len = total_len / count if count > 0 else 0
    return avg_len, count


# ---------- Part 2: 统计 buggy_code 平均行数 ----------
def avg_buggy_code_lines(root_dir):
    total_lines = 0
    file_count = 0

    for subdir in os.listdir(root_dir):
        subdir_path = os.path.join(root_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue

        buggy_dir = os.path.join(subdir_path, "buggyCode")
        if not os.path.isdir(buggy_dir):
            continue

        for filename in os.listdir(buggy_dir):
            if filename.startswith("buggy_code") and filename.endswith((".cpp", ".py", ".java")):
                file_path = os.path.join(buggy_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        file_count += 1
                except Exception as e:
                    print(f"无法读取文件: {file_path}, 错误: {e}")

    avg_lines = total_lines / file_count if file_count > 0 else 0
    return avg_lines, file_count


if __name__ == "__main__":
    json_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_compilable.json"
    dataset_root = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_All"

    avg_rev_len, rev_count = avg_reverse_labels_length(json_path)
    avg_lines, file_count = avg_buggy_code_lines(dataset_root)

    print("===== Reverse Labels 统计 =====")
    print(f"对象数量: {rev_count}")
    print(f"reverse_labels 平均长度: {avg_rev_len:.2f}")

    print("\n===== Buggy Code 行数统计 =====")
    print(f"buggy_code 文件数量: {file_count}")
    print(f"buggy_code 平均行数: {avg_lines:.2f}")
