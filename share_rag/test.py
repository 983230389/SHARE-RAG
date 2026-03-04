# import os

# path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_All"

# count = 0
# with os.scandir(path) as entries:
#     for entry in entries:
#         if entry.is_dir():
#             count += 1

# print("子文件夹数量：", count)


import os
import json
from collections import Counter

# 路径配置
json_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_compilable.json"
test_root = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_Test"

# 1. 读取 JSON 文件
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. 构建 id -> (category, level) 映射
id_map = {}
# print(data)
for item in data:
    item_id = str(item.get("instance_id"))
    category = item.get("category")
    level = item.get("level")
    id_map[item_id] = (category, level)

# 3. 遍历 DebugBench_Test 目录下的所有子目录
category_counter = Counter()
level_counter = Counter()

for name in os.listdir(test_root):
    subdir_path = os.path.join(test_root, name)
    if not os.path.isdir(subdir_path):
        continue

    # 子目录名作为 id
    if name in id_map:
        category, level = id_map[name]

        if category is not None:
            for c in category:
                category_counter[c] += 1
        if level is not None:
            level_counter[level] += 1

# 4. 输出统计结果
print("===== Category 统计结果 =====")
for k, v in category_counter.items():
    print(f"{k}: {v}")

print("\n===== Level 统计结果 =====")
for k, v in level_counter.items():
    print(f"{k}: {v}")
