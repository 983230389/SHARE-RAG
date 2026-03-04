import json


def build_zeroshot(zeroshot_prompt, code_location):
    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()
    prompt = zeroshot_prompt+"\n\n"
    prompt += "This is an incorrect code to the problem:\n" + code
    return prompt

def safe_json_parse(json_str):
    decoder = json.JSONDecoder()
    pos = 0
    length = len(json_str)
    while pos < length:
        try:
            obj, pos_new = decoder.raw_decode(json_str[pos:])
            if pos_new != 0:
                return obj  # Return the first successfully parsed JSON object
            pos += 1  # Increment position to continue if not successful
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError at pos {pos}: {e}")
            pos += 1  # Increment position to attempt to recover from error
    return None  # Return None if no valid JSON object was found

def process_res(res):
    json_objects = []
    for json_str in res:
        cleaned_json_str = json_str.strip()
        json_obj = safe_json_parse(cleaned_json_str)
        if json_obj is not None:
            json_objects.append(json_obj)
        else:
            print("No valid JSON object found in the string.")
    return json_objects

def build_twoshot(oneshot_prompt, code_location, res):
    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()
    prompt = oneshot_prompt+"\n\n"
    prompt += "This is an incorrect code to the problem:\n" + code + "\n\n"
    # res_str = "\n".join(res)
    # res_str = json.dumps(res, indent=2)
    json_objects = process_res(res)

    for obj in json_objects:
        formatted_json = json.dumps(obj, indent=2)
        prompt += "This is the similar code information retrieved for the relevant bug fix scenario:\n" + formatted_json + "\n\n"
    return prompt

def build_oneshot(oneshot_prompt, code_location, res):
    # with open(problem_location, 'r', encoding='utf-8') as file:
    #     problem = file.read()
    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()
    prompt = oneshot_prompt+"\n\n"
    # prompt += "This is a problemDescription:\n" + problem + "\n\n"
    prompt += "This is an incorrect code to the problem:\n" + code + "\n\n"
    # res_str = "\n".join(res)
    res_str = json.dumps(res, indent=2)

    prompt += "This is the similar code information retrieved for the relevant bug fix scenario:\n" + res_str + "\n\n"
    return prompt

def build_newoneshot(oneshot_prompt, code_location, fault_causes, fix_solution):
    # with open(problem_location, 'r', encoding='utf-8') as file:
    #     problem = file.read()

    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()
    prompt = oneshot_prompt+"\n\n"
    # prompt += "This is a problemDescription:\n" + problem + "\n\n"
    prompt += "This is an incorrect code to the problem:\n" + code + "\n\n"
    prompt += "This is the similar bug information retrieved for the relevant bug fix scenario:\n" + "Fault Causes:\n" + fault_causes + "\nFix Solution:\n" + fix_solution + "\n\n"
    return prompt

# def build_newoneshot(oneshot_prompt, code_location, res):
#     with open(code_location, 'r', encoding='utf-8') as file:
#         code = file.read()
#     prompt = oneshot_prompt+"\n\n"
#     prompt += "This is an incorrect code to the problem:\n" + code + "\n\n"
#     res_str = json.dumps(res, indent=2)
#     prompt += "This is the similar bug information retrieved for the relevant bug fix scenario:\n" + res_str + "\n\n"
#     return prompt