import json
import ast
import os
import ReadJson


def extract_ans_gpt4(file_path):
    """从TutorCode-TOP1.txt中提取ans_gpt4的versionId集合"""
    with open(file_path, 'r') as f:
        content = f.read().strip()
        # 定位到ans_gpt4字段
        start_idx = content.find("ans_qwen:") + len("ans_qwen:")
        end_idx = content.find("}", start_idx) + 1
        ans_str = content[start_idx:end_idx].strip()
        # 安全解析字符串为Python集合
        return ast.literal_eval(ans_str)


def get_explanation(version_id, base_path):
    """读取指定versionId的result.txt中的首个explanation"""
    result_path = os.path.join(
        base_path,
        f"{version_id}/qwen-turbo-lyt/1/result.txt"
    )
    if not os.path.exists(result_path):
        return f"Error: {version_id} result.txt not found."

    try:
        with open(result_path, 'r') as f:
            file = f.read()
            data = ReadJson.extract_json_regular(file)
            faulty_locs = data['faultyLoc']
            if faulty_locs:
                return faulty_locs[0]['explanation']
            else:
                return "No faultyLoc entries."
    except json.JSONDecodeError:
        return "Error: Invalid JSON format."
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    # 输入文件路径
    input_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/TutorCode-TOP5.txt"
    # 输出文件路径
    output_file = "candidates.txt"
    # result.txt的基础路径
    base_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"

    # 提取ans_gpt4的versionId集合
    try:
        version_ids = extract_ans_gpt4(input_file)
    except Exception as e:
        print(f"Failed to parse input file: {str(e)}")
        return

    # 遍历每个versionId，收集explanation
    explanations = []
    for vid in version_ids:
        explanation = get_explanation(vid, base_path)
        explanations.append(f"{vid}: {explanation}")

    # 写入输出文件
    with open(output_file, 'w') as f:
        f.write("\n".join(explanations))
    print(f"Explanations saved to {output_file}")

def getTutor():
    # 请根据实际情况修改以下路径
    tutorcode_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/TutorCode-TOP5.txt"   # TutorCode-TOP1.txt 文件路径
    json_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_all.json"         # 包含 tutorGuidance 字段的 JSON 文件路径
    output_file = "reference.txt"                  # 输出的 txt 文件

    # 提取 TutorCode-TOP1.txt 中的 versionId 集合
    try:
        version_ids = extract_ans_gpt4(tutorcode_file)
    except Exception as e:
        print(f"解析输入文件失败: {e}")
        return

    # 加载 JSON 文件数据
    try:
        json_mapping = load_json_data(json_file)
    except Exception as e:
        print(f"加载 JSON 文件失败: {e}")
        return

    results = []
    for vid in version_ids:
        # 保证 version id 为字符串，便于和 JSON 数据中的 id 比较
        vid_str = str(vid)
        if vid_str in json_mapping:
            tutor_guidance = json_mapping[vid_str].get("tutorGuidance", "未找到 tutorGuidance 字段")
            results.append(f"{vid_str}: {tutor_guidance}")
        else:
            results.append(f"{vid_str}: JSON 中未找到该 versionId 对应的信息")

    # 将结果写入输出文件
    try:
        with open(output_file, 'w', encoding='utf-8') as outf:
            outf.write("\n".join(results))
        print(f"所有 tutorGuidance 信息已保存到 {output_file}")
    except Exception as e:
        print(f"写入输出文件失败: {e}")


def load_json_data(json_file):
    """
    加载 JSON 文件，并构建一个字典，键为对象的 id（转为字符串），值为整个对象
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    # 假设 JSON 文件是一个对象数组
    mapping = {}
    for item in data:
        # 使用 str(item["id"]) 作为键，确保与 TutorCode-TOP1.txt 中的 versionId 格式一致
        mapping[str(item.get("id"))] = item
    return mapping


import json


def parse_file(file_path):
    """
    解析文件，每一行格式为 "vid: text"，返回字典 {vid: text}
    注意：如果文本中含有冒号，仅按第一个冒号分割。
    """
    data = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # 按第一个冒号进行分割
            parts = line.split(":", 1)
            if len(parts) < 2:
                continue
            vid = parts[0].strip()
            text = parts[1].strip()
            data[vid] = text
    return data


def merge():
    # 请根据实际情况修改以下文件路径
    candidate_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/candidates.txt"  # 候选内容文件
    reference_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/reference.txt"  # 参考内容文件
    output_file = "sentence_pairs_top5.jsonl"  # 输出的 jsonl 文件

    # 解析两个文件
    candidates = parse_file(candidate_file)
    references = parse_file(reference_file)

    # 合并两个文件中相同 vid 的内容
    merged_items = []
    # 取两个文件中的所有 vid（如果只需要两边都有的，可取交集）
    all_vids = set(candidates.keys()).intersection(references.keys())
    for vid in sorted(all_vids, key=lambda x: (0, int(x)) if x.isdigit() else (1, x)):
        candidate_text = candidates.get(vid, "")
        reference_text = references.get(vid, "")
        item = {
            "candidate": candidate_text,
            "reference": reference_text
        }
        merged_items.append(item)

    # 写入 jsonl 文件，每一行一个 JSON 对象
    with open(output_file, "w", encoding="utf-8") as f_out:
        for item in merged_items:
            json_line = json.dumps(item, ensure_ascii=False)
            f_out.write(json_line + "\n")

    print(f"共合并 {len(merged_items)} 条记录，输出文件：{output_file}")


if __name__ == "__main__":
    main()
    getTutor()
    merge()