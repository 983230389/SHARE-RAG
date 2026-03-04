import json
import os

# 定义文件路径
txt_file_path = os.path.join(os.getcwd(), "Data", "Tutor.txt")

# 读取文件内容，并在首尾添加方括号
with open(txt_file_path, 'r', encoding='utf-8') as file:
    content = file.read()
    # 在开头添加 '['，在结尾添加 ']'
    json_content = '[' + content + ']'

# 解析 JSON 数组
try:
    data_list = json.loads(json_content)
except json.JSONDecodeError as e:
    print(f"解析 JSON 时出错：{e}")
    data_list = []

# 创建一个字典来统计 problemId 的数量
problem_id_counts = {}

for data in data_list:
    problem_id = data.get('problemId')
    if problem_id is not None:
        problem_id_counts[problem_id] = problem_id_counts.get(problem_id, 0) + 1
    else:
        print(f"警告：找到没有 problemId 的数据项：{data}")

sum = 0
# 输出统计结果
print("各个 problemId 对应的 JSON 对象数量：")
for problem_id, count in problem_id_counts.items():
    sum += count

# print(f"problemId {problem_id}: {count} 个对象")
print(sum/35)
print(35*35.4)