import json
import re

def extract_json(input_string):
    """
    提取输入字符串中的JSON字符串。

    :param input_string: 输入字符串
    :return: 如果找到JSON字符串，则返回它。否则，返回None。
    """

    # 找到 JSON 字符串开始的位置
    start = input_string.find('{')
    if start == -1:
        return None,None
    else:
        # 初始化大括号计数器
        brace_count = 1
        # 从 JSON 字符串开始的位置之后开始循环
        jump_flag = False
        for i, char in enumerate(input_string[start + 1:], start=start + 1):
            if char == '"':
                jump_flag=not jump_flag
            if jump_flag:
                continue
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                # 如果大括号平衡了，则找到 JSON 字符串的结束位置
                if brace_count == 0:
                    return input_string[start: i + 1],i+1
    return None,None

def extract_json_regular(string):
    """
    终极提取函数，能够处理：
    1. 有/无 ```json 包裹的情况
    2. 标准数组 / 标准对象
    3. 多个散落的对象 (逗号分隔或无分隔)
    4. 严重的语法错误 (如 "faultyLine":点多17)
    """
    
    content = ""
    
    # ================= 1. 智能定位内容区域 =================
    # 策略 A: 优先寻找 ```json 或 ``` 包裹的内容
    # (?:json)? 表示 json 是可选的，\s* 忽略空白
    pattern_block = r'```(?:json)?\s*(.*?)\s*```'
    match = re.search(pattern_block, string, re.S | re.IGNORECASE)
    
    if match:
        content = match.group(1).strip()
    else:
        # 策略 B: 如果没有代码块标记，则假设整个字符串包含 JSON
        # 为了提高 json.loads 的成功率，我们尝试寻找第一个 [ 或 { 作为起点
        # 寻找最后一个 ] 或 } 作为终点
        start_match = re.search(r'[\[\{]', string)
        if start_match:
            start_index = start_match.start()
            # 从起点开始截取
            potential_content = string[start_index:]
            # 尝试找到最后一个闭合符，去掉后面的杂乱文本
            end_match_list = [m.start() for m in re.finditer(r'[\]\}]', potential_content)]
            if end_match_list:
                end_index = end_match_list[-1] + 1
                content = potential_content[:end_index]
            else:
                content = potential_content
        else:
            # 既没有代码块，也没找到括号，说明没数据
            return None

    # 最终我们要收集的对象列表
    extracted_objects = []

    # ================= 2. 尝试整体标准解析 (Happy Path) =================
    try:
        # 尝试直接解析提取出的内容
        data = json.loads(content)
        
        if isinstance(data, dict):
            # 如果包含 faultyLoc 且是列表
            if "faultyLoc" in data and isinstance(data["faultyLoc"], list):
                extracted_objects = data["faultyLoc"]
            # 如果是单个对象，或者包含 faultyLoc 但不是列表
            elif "faultyLoc" in data:
                 extracted_objects = [data["faultyLoc"]]
            else:
                # 只是一个普通对象，包裹起来
                extracted_objects = [data]
                
        elif isinstance(data, list):
            # 是一个标准数组
            extracted_objects = data
            
        return {"faultyLoc": extracted_objects}

    except json.JSONDecodeError:
        # 解析失败，说明数据“脏”或者是“散落对象”，进入暴力提取模式
        pass

    # ================= 3. 暴力分块提取 / 容错解析 (Dirty Path) =================
    # 正则逻辑：非贪婪匹配最内层的大括号对 {}
    # 这可以把 [ {obj1}, {obj2} ] 或者 {obj1} {obj2} 切分成单独的块
    object_pattern = r'(\{.*?\})'
    potential_objects = re.findall(object_pattern, content, re.S)

    for obj_str in potential_objects:
        # 3.1 对切分出的小块尝试标准解析
        try:
            single_data = json.loads(obj_str)
            if "faultyLoc" in single_data and isinstance(single_data["faultyLoc"], list):
                extracted_objects.extend(single_data["faultyLoc"])
            elif "faultyLine" in single_data: 
                extracted_objects.append(single_data)
            continue 
        except json.JSONDecodeError:
            pass
        
        # 3.2 深度脏数据清洗 (针对 "点多17" 等情况)
        # 手动提取 key-value
        f_line_match = re.search(r'"faultyLine"\s*:\s*([^,}]+)', obj_str, re.S)
        expl_match = re.search(r'"explanation"\s*:\s*"(.*?)"', obj_str, re.S)
        
        if f_line_match or expl_match:
            new_obj = {}
            
            # 清洗 faultyLine
            if f_line_match:
                raw_val = f_line_match.group(1).strip()
                # 提取数字逻辑：如果包含数字，提取第一组连续数字，否则保留原样
                num_match = re.search(r'\d+', raw_val)
                if num_match:
                    new_obj["faultyLine"] = int(num_match.group(0)) 
                else:
                    new_obj["faultyLine"] = raw_val 
            else:
                new_obj["faultyLine"] = None

            # 提取 explanation
            if expl_match:
                new_obj["explanation"] = expl_match.group(1)
            else:
                new_obj["explanation"] = "Unknown"
            
            extracted_objects.append(new_obj)

    return {"faultyLoc": extracted_objects}

# def extract_json_regular(text):
#     """
#     从 ```json ... ``` 中提取 JSON：
#     - 单个 JSON：
#         - 数组 -> {"faultyLoc": [...]}
#         - 对象 -> 原样返回
#     - 多个 JSON：
#         - 先组成数组，再 -> {"faultyLoc": [...]}
#     """

#     pattern = r"```json\s*(.*?)\s*```"
#     matches = re.findall(pattern, text, re.S)

#     parsed_blocks = []

#     for json_str in matches:
#         json_str = json_str.strip()

#         try:
#             parsed = json.loads(json_str)
#             parsed_blocks.append(parsed)
#         except json.JSONDecodeError as e:
#             print("无法解析 JSON 数据:", e)

#     if not parsed_blocks:
#         return None

#     # ====== 只有一个 json 块 ======
#     if len(parsed_blocks) == 1:
#         single = parsed_blocks[0]

#         # 如果是数组，包成对象
#         if isinstance(single, list):
#             return {"faultyLoc": single}

#         # 如果已经是对象，直接返回
#         if isinstance(single, dict):
#             return single

#     # ====== 多个 json 块 ======
#     # 统一包成数组，再包成对象
#     return {"faultyLoc": parsed_blocks}

if __name__ == "__main__":
    # with open("./result.txt", 'r', encoding='utf-8') as file:
    #     # ��ȡ�ļ����ݲ����浽�ַ�����
    #     response = file.read()

    # res= extract_json(response)
    # print(res)
    response = """
```json
[
    {
        "faultyLine":23,
        "explanation": "Line 23 outputs 'b' and 'a' in the wrong order. The problem likely requires outputting 'a' then 'b' when b0 != a0, not 'b' then 'a'."
    },
    {
        "faultyLine":25,
        "explanation": "The condition 'a0 != b0' is identical to line 21's condition, making this else-if redundant and unreachable. Should likely be a different condition."
    }
]
```
"""
    response = """
```json
{
    "faultyLoc": [
        {
            "faultyLine": 17,
            "explanation": "The formula calculates travel time incorrectly. 'time=5*p[n]+4*p[n]' is redundant (9*p[n]) instead of '5*p[n] + 5*n' or similar proper elevator travel time calculation. It also incorrectly uses the same term twice."
        },
        {
            "faultyLine": 18,
            "explanation": "The loop 'for(i=0;i<=1000;i++)' uses a magic number 1000 without explanation, suggesting a fixed constraint not justified by the problem. It should likely depend on n or MAX."
        }
    ]
}
```
"""

    response = """
```json
{
    "faultyLine": 是17,
    "explanation": "The formcxula calculates travel time incorrectly. 'time=5*p[n]+4*p[n]' is redundant (9*p[n]) instead of '5*p[n] + 5*n' or similar proper elevator travel time calculation. It also incorrectly uses the same term twice."
},
{
    "faultyLine": 18,
    "explanation": "The loop 'for(i=0;i<=1000;i++)' uses a magic number 1000 without explanation, suggesting a fixed constraint not justified by the problem. It should likely depend on n or MAX."
}
```
"""   

    data = extract_json_regular(response)
    print(data)
    # 使用正则表达式查找包含整个 JSON 数据的部分
    # pattern = r'\{.*\[.*\].*\}'  # 匹配整个 JSON 数据，包括换行符和空格
    # matches = re.findall(pattern, response,re.S)
    # # xi
    # for json_str in matches:
    #     try:
    #         data = json.loads(json_str)
    #         # 这里可以对提取出的 JSON 数据进行处理
    #         print("从文本中提取的 JSON 数据:")
    #         print("intentOfThisFunction:", data["intentOfThisFunction"])
    #         print("faultLocalization:", data["faultLocalization"])
    #     except json.JSONDecodeError as e:
    #         print("无法解析 JSON 数据:", e)