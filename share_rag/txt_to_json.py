import json


def merge_json(txt_file, lookup_file, output_file):
    # 2. 读取 lookup.json 并构建 id->对象 的查找表
    with open(lookup_file, 'r', encoding='utf-8') as f:
        lookup_data = json.load(f)

    # 假设 lookup.json 是一个包含多个对象的列表，每个对象都含有 "id" 字段
    lookup_dict = {item["id"]: item for item in lookup_data}

    merged_results = []
    # 1. 读取 txt 文件的每行 JSON
    with open(txt_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 去除末尾多余的逗号
            if line.endswith(','):
                line = line[:-1]

            data_obj = json.loads(line)
            item_id = data_obj.get("id")

            # 在查找表中找到对应的对象
            lookup_item = lookup_dict.get(item_id)
            merged_results.append(lookup_item)


    # 5. 将合并结果写入新的 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        # ensure_ascii=False 使得中文等非 ASCII 字符能正常保存在 JSON 文件中
        json.dump(merged_results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    merge_json(
        txt_file="/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_train.txt",
        lookup_file="/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_all.json",
        output_file="/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_filter.json"
    )
