from openai import OpenAI
from zai import ZhipuAiClient
def send_prompt_openai_form(prompt, model):
    client = OpenAI(
        # base_url="http://127.0.0.1:9997/v1",
        base_url="http://127.0.0.1:8611/v1",
        api_key="666"
    )
    # print(mykey)
    if model == "chatGlm4":
        model = "glm-4-9b"
    if model == "chatGlm3":
        model = "chatglm3-6b"
    completion = client.chat.completions.create(
        model=model,  # 将模型更改
        messages=[
            {"role": "system", "content": "You are a highly skilled artificial intelligence engineer and algorithm teacher who is good at pinpointing errors in novice programs."},
            {"role": "user", "content": prompt}
        ]
    )
    result_txt = completion.choices[0].message.content
    print(result_txt)
    return result_txt

def send_prompt_openai_gpt(prompt,model):
    with open('/home/weijiqing/miniconda3/envs/llmfl/LLMFL/key.txt', 'r', encoding='utf-8') as file:
        # 读取文件内容并保存到字符串中
        mykey = file.read()
    url = "https://yunwu.ai/v1"
    if model == "qwen-turbo":
        model = "qwen-turbo-2024-11-01"
    if model == "qwen-turbo":
        model = "qwen-turbo-2024-11-01"
    if model == "Spark Lite":
        model = "lite"
        url = "https://spark-api-open.xf-yun.com/v1/"
        mykey = "LgSraNJfVjTopvhbjDMX:jbsqWYTWsmBESFPqNQgp"
    if model == "deepseek-v3.1":
        model = "xopdeepseekv32"
        url = "https://maas-api.cn-huabei-1.xf-yun.com/v1"
        mykey = "sk-SHdN3tPvrCivveWhAe33Cc333129492bBdD891D78d53A594"
    if "qwen" in model:
        model = "xop3qwen1b7"
        url = "https://maas-api.cn-huabei-1.xf-yun.com/v1"
        mykey = "sk-SHdN3tPvrCivveWhAe33Cc333129492bBdD891D78d53A594"
    if "nvida" in model:
        model = model[5:]
        url = "https://integrate.api.nvidia.com/v1"
        mykey = "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"
    if "glm" in model:
        model = "xopglm47blth2"
        url = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
        mykey = "dad381fd24f1c215be1a8c15aa87b18d:YWYxMzIyZGUyNDU0OWEzZjIyNDAwYjQ4"
    client = OpenAI(
        # your openai url
        # base_url="https://vip.apiyi.com/v1",
        base_url=url,
        timeout = 3600,
        # your key
        api_key=mykey
    )
    # client = OpenAI(api_key="sk-a20acefedb4f4eeebb14a8e16e876bb2", base_url="https://api.deepseek.com")
    # print(mykey)
    if "deepseek" in model:
        completion = client.chat.completions.create(
            model=model,  # 将模型更改
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            extra_body={"chat_template_kwargs": {"thinking":False}},
            stream=False
        )
    # elif "glm" in model:
    #     # client = ZhipuAiClient(api_key="892795a71d2543a3a9518dd5e0608500.EgVUokGxY48pp8WI")
    #     completion = client.chat.completions.create(
    #         model =model,
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         enable_thinking=False,
    #         stream = False
    #     )
    else:    
        completion = client.chat.completions.create(
            model=model,  # 将模型更改
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
    result_txt = completion.choices[0].message.content
    # print(result_txt)
    return result_txt
