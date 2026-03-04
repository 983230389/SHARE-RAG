import streamlit as st
from utils.utils import extract_text, split_content_into_chunks
from utils.utils import save_chunks_into_vectorstore, get_chat_chain, process_user_input
from models.embedding_model import get_openaiEmbedding_model
from models.embedding_model import get_huggingfaceEmbedding_model
from models.embedding_model import get_modelscopeEmbeddings

def main():
    # 配置界面
    st.set_page_config(page_title="基于BuctOJ数据集的QA ChatBot",
                       page_icon=":robot:")
    st.header("基于LangChain+LLM实现QA ChatBot")

    # session_state是Streamlit提供的用于存储会话状态的功能
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    # 1. 提供用户输入文本框
    user_input = st.text_input("基于上传的数据，请输入你的提问：")
    # 处理用户输入，并返回响应结果
    if user_input:
        process_user_input(user_input)

    with st.sidebar:
        # 2. 设置子标题
        st.subheader("你的数据")
        # 3. 上传数据
        files = st.file_uploader("上传数据，然后点击‘提交并处理’",
                                 accept_multiple_files=True)
        if st.button("提交并处理"):
            with st.spinner("请等待，处理中……"):
                # 4. 获取数据内容
                texts = extract_text(files)
                # 5. 将获取到的数据内容切分
                content_chunks = split_content_into_chunks(texts)
                #st.write(content_chunks)
                # 6. 对每个chunk计算embedding，并存入到向量数据库
                #   6.1 根据model_type和model_name创建embedding model对象
                # embedding_model = get_openaiEmbedding_model()
                embedding_model = get_modelscopeEmbeddings()
                #   6.2 创建向量数据库对象，并将文本embedding后存入到里面
                vector_store = save_chunks_into_vectorstore(content_chunks, embedding_model)
                # 7. 创建对话
                st.session_state.conversation = get_chat_chain(vector_store)

if __name__ == "__main__":
    main()