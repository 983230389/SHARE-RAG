from langchain.chat_models import ChatOpenAI
from langchain_community.llms import HuggingFaceHub
from config.keys import Keys

def get_openai_model():
    llm_model = ChatOpenAI(openai_api_key=Keys.OPEN_API_KEY)
    return llm_model

def get_huggingfacehub():
    llm_model = HuggingFaceHub(repo_id="google/flan-t5-base")
    return llm_model

def get_model():
    model = ChatOpenAI(model='chatGlm3', base_url="http://222.199.230.149:8611/v1", api_key="666")
    return model