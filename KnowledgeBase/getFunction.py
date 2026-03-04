import json
import SendPrompt
import os
import re

def load_json_data(filepath):
    """加载 JSON 文件并返回数据列表。"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


# 生成功能语义
def generate_function(prompt_location1, experiment_model, question, buggy_code):
    # 读取提示词
    with open(prompt_location1, 'r', encoding='utf-8') as file:
        prompt1 = file.read()

    prompt = f"{prompt1}\nQuestion: {question}\nBuggy Code:\n{buggy_code}\n\n"
    results = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
    return results

# 生成错误原因和修复方案
# def generate_CauseFix(prompt_location2, experiment_model, buggy_code, solution, bug_explanation):
#     # 读取提示词
#     with open(prompt_location2, 'r', encoding='utf-8') as file:
#         prompt2 = file.read()
#
#     prompt = f"{prompt2}\nBuggyCode: {buggy_code}\nSolution:\n{solution}\nExplanation: {bug_explanation}\n\n"
#     results = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
#     return results

def generate_CauseFix(prompt_location2, experiment_model, buggy_code, correct_code, tutorGuidance, solution):
    # 读取提示词
    with open(prompt_location2, 'r', encoding='utf-8') as file:
        prompt2 = file.read()

    prompt = f"{prompt2}\nBuggyCode: {buggy_code}\nCorrectCode:\n{correct_code}\nTutorCode: {tutorGuidance}\nSolution: {solution}\n\n"
    results = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
    return results

def extract_json(results_str):
    """提取并解析 JSON 数据。"""
    # 1. 去掉可能存在的三引号标记（```json ... ```）
    pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
    match = re.search(pattern, results_str)
    if match:
        json_str = match.group(1)  # 提取出花括号包裹的 JSON 内容
    else:
        # 如果没有找到 ```json``` 标记，尝试直接匹配花括号中的 JSON
        brace_pattern = r"(\{[\s\S]*\})"
        brace_match = re.search(brace_pattern, results_str)
        if brace_match:
            json_str = brace_match.group(1)
        else:
            print("未找到可解析的 JSON 数据")
            return {}

    # 2. 解析 JSON 字符串
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        print("无法解析 JSON 数据:", e)
        return {}

def append_result_to_file(result, txt_file_path):
    """将单个 result 追加到 TXT 文件中，每行一个 JSON 对象。"""
    with open(txt_file_path, "a", encoding="utf-8") as txt_file:
        json_str = json.dumps(result, ensure_ascii=False)
        txt_file.write(json_str + '\n')

def generate_knowledgeBase(prompt_location1, prompt_location2, experiment_model, output_file_path):
    json_data = load_json_data('/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_filter.json')

    for idx, item in enumerate(json_data):
        # 1. 提取字段
        # question = item.get('question', '')
        # solution = item.get('solution', '')
        # buggy_code = item.get('buggy_code', '')
        # bug_explanation = item.get('bug_explanation', '')

        question = item.get('problemDescription', '')
        correct_code = item.get('groudTruthCode', '')
        buggy_code = item.get('incorrectCode', '')
        tutorGuidance = item.get('tutorGuidance', '')
        solution = item.get('solutionDescription', '')

        # 2. 生成功能语义
        function_response = generate_function(prompt_location1, experiment_model, question, buggy_code)
        function = extract_json(function_response)

        # 3. 生成错误原因和修复方案
        # cause_fix_response = generate_CauseFix(prompt_location2, experiment_model, buggy_code, solution, bug_explanation)
        cause_fix_response = generate_CauseFix(prompt_location2, experiment_model, buggy_code, correct_code, tutorGuidance, solution)
        cause_fix = extract_json(cause_fix_response)

        # 4. 组合json
        result = {
            "Primary Purpose": function.get("Primary Purpose", ""),
            "Detailed functionalities": function.get("Detailed functionalities", ""),  # 根据最新要求修改字段名
            "Fault Causes": cause_fix.get("Fault Causes", ""),
            "Fix Solution": cause_fix.get("Fix Solution", "")
        }

        # 5. 追加到文件
        append_result_to_file(result, output_file_path)
        print(f"Item {idx+1}: 处理并写入成功。")

    print("所有未处理的项已完成。")

def main():
    prompt_location1 = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/prompts/function_prompt.txt"
    prompt_location2 = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/prompts/cause_solution_prompt.txt"
    output_file_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_base.txt"
    experiment_model = "gpt-3.5-turbo"

    generate_knowledgeBase(prompt_location1, prompt_location2, experiment_model, output_file_path)

if __name__ == "__main__":
    main()
