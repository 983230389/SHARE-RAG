from config.keys import Keys
from langchain_community.embeddings import (
    OpenAIEmbeddings,
    HuggingFaceEmbeddings,
    ModelScopeEmbeddings,
    HuggingFaceBgeEmbeddings
)

from modelscope import snapshot_download
import os
import torch
from modelscope import snapshot_download
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from sentence_transformers import SentenceTransformer
import torch

from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

class StableBGEEmbeddings(Embeddings):
    def __init__(self, model_path):
        self.model = SentenceTransformer(
            model_path,
            device="cpu"  # 永远不触发 meta tensor
        )

    def embed_documents(self, texts):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=8,
            show_progress_bar=False
        ).tolist()

    def embed_query(self, text):
        return self.model.encode(
            text,
            normalize_embeddings=True
        ).tolist()

def get_openaiEmbedding_model():
    return OpenAIEmbeddings(openai_api_key=Keys.OPENAI_API_KEY)

def get_huggingfaceEmbedding_model():
    return HuggingFaceEmbeddings(model_name="/home/weijiqing/miniconda3/envs/llmfl/sentence-t5-large")

def get_modelscopeEmbeddings():
    import os

    # 🚫 必须在 import transformers 之前
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["ACCELERATE_DISABLE"] = "1"
    os.environ["TRANSFORMERS_NO_ACCELERATE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    import torch
    from modelscope import snapshot_download
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings

    model_dir = "AI-ModelScope/bge-large-en-v1.5"
    model_cache_dir = os.path.expanduser(
        "~/.cache/modelscope/hub/models/AI-ModelScope/bge-large-en-v1.5"
    )

    if not os.path.exists(model_cache_dir):
        print("[Embedding] 下载模型")
        model_cache_dir = snapshot_download(model_dir)
    else:
        print(f"[Embedding] 使用本地模型：{model_cache_dir}")

    print("[Embedding] ✅ 强制 CPU + 禁用 accelerate（稳定模式）")

    # embeddings = HuggingFaceBgeEmbeddings(
    #     model_name=model_cache_dir,

    #     # 🔑 关键：显式 CPU + dtype
    #     model_kwargs={
    #         "device": "cpu",
    #         "torch_dtype": torch.float32
    #     },

    #     encode_kwargs={
    #         "normalize_embeddings": True,
    #         "batch_size": 8      # ✅ 防止 CPU OOM
    #     },

    #     query_instruction="为这个句子生成表示以用于检索相关文章："
    # )
    embeddings = StableBGEEmbeddings(
    "/home/weijiqing/.cache/modelscope/hub/models/AI-ModelScope/bge-large-en-v1.5"
    )
    return embeddings

def get_modelscopeEmbeddings_gpu():
    import os
    import torch
    from modelscope import snapshot_download
    from sentence_transformers import SentenceTransformer
    from langchain_community.embeddings import HuggingFaceEmbeddings

    os.environ["ACCELERATE_DISABLE"] = "1"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

    model_dir = "AI-ModelScope/bge-large-en-v1.5"
    model_path = snapshot_download(model_dir)

    print("[Embedding] 使用 GPU（禁用 accelerate）")

    # ⚠️ 手动加载 SentenceTransformer（绕开 LangChain）
    st_model = SentenceTransformer(
        model_path,
        device="cuda"
    )

    embeddings = HuggingFaceEmbeddings(
        client=st_model,
        encode_kwargs={"normalize_embeddings": True}
    )

    return embeddings
