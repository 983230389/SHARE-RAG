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
    client = OpenAI(
        # your openai url
        # base_url="https://vip.apiyi.com/v1",
        base_url=url,
        timeout = 3600,
        # your key
        api_key=mykey
    )
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
