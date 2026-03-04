from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from models.llm_model import get_openai_model, get_huggingfacehub, get_model
import streamlit as st
from config.templates import bot_template, user_template
from PyPDF2 import PdfReader

# def extract_text(files):
#     documents = ""
#     for txt in files:
#         loader = TextLoader(txt)
#         documents = loader.load()
#     return documents

def extract_text(files):
    text = ""
    for pdf in files:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def split_content_into_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
        separators=['\n']
    )
    chunks = text_splitter.split_text(text)
    return chunks

def save_chunks_into_vectorstore(content_chunks, embedding_model):
    # FAISS
    # pip install faiss-gpu (pip install faiss-cpu)
    vectorstore = FAISS.from_texts(texts=content_chunks,
                                   embedding=embedding_model)
    return vectorstore

def get_chat_chain(vector_store):
    # 1. 获取LLM model
    # llm = get_openai_model()
    llm = get_model()

    # 2. 存储历史记录，保存对话历史记录的对象
    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)

    # 3. 对话链
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(),
        memory=memory
    )
    return conversation_chain

def process_user_input(user_input):
    # 调用函数st.session_state.conversation，并把用户输入的内容作为一个问题传入，返回响应。
    response = st.session_state.conversation({'question': user_input})
    # session状态是Streamlit中的一个特性，允许在用户的多个请求之间保存数据
    st.session_state.chat_history = response['chat_history']
    # 显示聊天记录
    # chat_history : 一个包含之前聊天记录的表
    for i, message in enumerate(st.session_state.chat_history):
        # 用户输入
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True) # unsafe_allow_html=True表示允许HTML内容被渲染
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
