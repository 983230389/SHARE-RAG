from langchain_community.retrievers import BM25Retriever
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
import numpy as np
import math
import jieba
from rank_bm25 import BM25Okapi
import os.path
from models.embedding_model import get_modelscopeEmbeddings, get_modelscopeEmbeddings_gpu
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import SendPrompt
from KnowledgeBase.getFunction import extract_json
import json
from code_features.ast_features import extract_ast_features
from code_features.cfg_features import extract_cfg_features
from code_features.dfg_features import extract_dfg_features
import re

RERANK_MODEL_PATH = "/home/weijiqing/.cache/modelscope/hub/BAAI/bge-reranker-base"
try:
    rerank_tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL_PATH)
    rerank_model = AutoModelForSequenceClassification.from_pretrained(RERANK_MODEL_PATH)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rerank_model = rerank_model.to(device)
    rerank_model.eval() # 开启评估模式
except Exception as e:
    print(f"Warning: Rerank model load failed: {e}")
    rerank_model = None
    rerank_tokenizer = None
    device = "cpu"
# 加载排序模型
# tokenizer = AutoTokenizer.from_pretrained('../hugging-face-model/BAAI/bge-reranker-base/')
# rerank_model = AutoModelForSequenceClassification.from_pretrained('../hugging-face-model/BAAI/bge-reranker-base/')
# rerank_model.cuda()

HYDE_PROMPT_TEMPLATE = """
You are an expert debugger. Below is a piece of buggy code.
Please analyze the code, identify the potential logic error, and provide a CORRECTED version of the code.
Do not provide explanations, only output the fixed code block.

Buggy Code:
{code}

Fixed Code:
"""

# 自反式评估 Prompt (Evaluator)
REFLECTION_PROMPT_TEMPLATE = """
You are a code retrieval evaluator. 
Query Code (Buggy): 
{query}

Retrieved Reference Case:
{retrieved}

Task: Determine if the retrieved reference case provides a useful fix pattern or similar logical structure for the query code.
Output "YES" if it is useful/relevant, or "NO" if it is irrelevant.
"""

def extract_text(files_loc):
    loader = TextLoader(files_loc)
    text = loader.load()
    return text


def split_content(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
        separators=['\n']
    )
    chunks = text_splitter.split_documents(text)
    return chunks


def save_vectorstore(content_chunks, embedding_model, db_path):
    db = FAISS.from_documents(content_chunks, embedding_model)
    db_location = os.path.join(db_path)
    db.save_local(db_location)
    return db


def preprocessing_func(text: str) -> List[str]:
    return list(jieba.cut(text))


def retrieve(content_chunks, prompts, db):
    texts = [i.page_content for i in content_chunks]
    texts_processed = [preprocessing_func(t) for t in texts]
    vectorizer = BM25Okapi(texts_processed)
    # 文本召回
    bm25_res = vectorizer.get_top_n(preprocessing_func(prompts), texts, n=10)
    # 向量召回
    vector_res = db.similarity_search(prompts, k=10)
    # print("bm25", bm25_res)
    # print("vector", vector_res)
    return bm25_res, vector_res


# 多路召回，加权
def rrf(vector_results: List[str], text_results: List[str], k: int = 1, m: int = 60):
    """
    使用RRF算法对两组检索结果进行重排序

    params:
    vector_results (list): 向量召回的结果列表,每个元素是专利ID
    text_results (list): 文本召回的结果列表,每个元素是专利ID
    k(int): 排序后返回前k个
    m (int): 超参数

    return:
    重排序后的结果列表,每个元素是(文档ID, 融合分数)
    """

    doc_scores = {}

    # 遍历两组结果,计算每个文档的融合分数
    for rank, doc_id in enumerate(vector_results):
        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1 / (rank + m)
    for rank, doc_id in enumerate(text_results):
        doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1 / (rank + m)

    # 将结果按融合分数排序
    # sorted_dict = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)
    sorted_results = [d for d, _ in sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:k]]
    return sorted_results


# 重排序函数
def rerank_with_model(pairs):
    if rerank_model is None:
        return torch.zeros(len(pairs))

    inputs = rerank_tokenizer(
        pairs, padding=True, truncation=True,
        return_tensors='pt', max_length=512
    )
    with torch.no_grad():
        inputs = {k: v.to(device) for k, v in inputs.items()}
        scores = rerank_model(**inputs).logits.view(-1).float()
    return scores



def order(bm25_res, vector_res, query, res_path):
    vector_docs = vector_res          # List[Document]
    bm25_docs = [doc for doc in bm25_res if hasattr(doc, "page_content")]

    # RRF（用 content 但映射回 Document）
    doc_scores = {}
    content_to_doc = {}

    for rank, doc in enumerate(vector_docs):
        content_to_doc[doc.page_content] = doc
        doc_scores[doc.page_content] = doc_scores.get(doc.page_content, 0) + 1 / (rank + 60)

    for rank, doc in enumerate(bm25_docs):
        content_to_doc[doc.page_content] = doc
        doc_scores[doc.page_content] = doc_scores.get(doc.page_content, 0) + 1 / (rank + 60)

    sorted_contents = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
    final_docs = [content_to_doc[c] for c, _ in sorted_contents[:5]]

    return final_docs  # ✅ List[Document]



# 生成功能语义
def generate_function(prompt_location1, experiment_model, code):
    # 读取提示词
    with open(prompt_location1, 'r', encoding='utf-8') as file:
        prompt1 = file.read()

    prompt = f"{prompt1}\nBuggy Code:\n{code}\n\n"
    results = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
    function = extract_json(results)

    combined_query = f"{code}\nFunctional Semantics: {function}"
    return combined_query


def build_ast_query(code: str, language="cpp"):
    ast = extract_ast_features(code, language)

    return f"""
AST Shape:
- max_depth: {ast['ast_shape']['max_depth']}
- avg_loop_depth: {ast['ast_shape']['avg_loop_depth']}

Control Skeleton:
- control_sequence: {ast['control_skeleton']}

Repair Anchors:
- assignments_in_loop_ratio: {ast['repair_anchors']['assignments_in_loop_ratio']}
"""


def build_cfg_query(code: str, language="cpp"):
    cfg = extract_cfg_features(code, language)["control_flow_shape"]

    return f"""
Control Flow Shape:
- num_if: {cfg['num_if']}
- num_if_else: {cfg['num_if_else']}
- nested_if: {cfg['nested_if']}
- num_loops: {cfg['num_loops']}
- early_exit_in_loop: {cfg['early_exit']}
"""


def build_dfg_query(code: str, language="cpp"):
    dfg = extract_dfg_features(code, language)["data_flow_semantics"]

    return f"""
Data Flow Semantics:
- update_patterns: {dfg['update_patterns']}
- loop_controlled_vars: {dfg['loop_controlled_vars']}
"""


def retrieve_by_single_structure(
        code: str,
        struct_db_path: str,
        build_query_func,
        embedding_model,
        topk=20
):
    struct_db = FAISS.load_local(
        struct_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    struct_query = build_query_func(code)
    docs = struct_db.similarity_search(struct_query, k=topk)

    return [d.metadata["id"] for d in docs]


def new_RAG_ast(files_loc, db_path, res_path, code_location, db):
    with open(code_location, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        embedding_model = get_modelscopeEmbeddings()
    except Exception as e:
        embedding_model = get_modelscopeEmbeddings_gpu()

    if db == 1:
        struct_db_path = os.path.join(db_path, "TutorCode_ast_db")
        content_db_path = os.path.join(db_path, "TutorCode_content_db")
    else:
        struct_db_path = os.path.join(db_path, "DebugBench_ast_db")
        content_db_path = os.path.join(db_path, "DebugBench_content_db")

    candidate_ids = retrieve_by_single_structure(
        code, struct_db_path, build_ast_query, embedding_model
    )

    content_db = FAISS.load_local(
        content_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    text = extract_text(files_loc)
    chunks = split_content(text)

    vector_res = content_db.similarity_search(
        code, k=5, filter={"id": {"$in": candidate_ids}}
    )

    bm25_res, _ = retrieve(chunks, code, content_db)
    return order(bm25_res, vector_res, code,res_path)


def new_RAG_cfg(files_loc, db_path, res_path, code_location, db):
    with open(code_location, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        embedding_model = get_modelscopeEmbeddings()
    except Exception as e:
        embedding_model = get_modelscopeEmbeddings_gpu()

    if db == 1:
        struct_db_path = os.path.join(db_path, "TutorCode_cfg_db")
        content_db_path = os.path.join(db_path, "TutorCode_content_db")
    else:
        struct_db_path = os.path.join(db_path, "DebugBench_cfg_db")
        content_db_path = os.path.join(db_path, "DebugBench_content_db")

    candidate_ids = retrieve_by_single_structure(
        code, struct_db_path, build_cfg_query, embedding_model
    )

    content_db = FAISS.load_local(
        content_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    text = extract_text(files_loc)
    chunks = split_content(text)

    vector_res = content_db.similarity_search(
        code, k=5, filter={"id": {"$in": candidate_ids}}
    )

    bm25_res, _ = retrieve(chunks, code, content_db)
    return order(bm25_res, vector_res, code,res_path)


def new_RAG_dfg(files_loc, db_path, res_path, code_location, db):
    with open(code_location, 'r', encoding='utf-8') as f:
        code = f.read()

    try:
        embedding_model = get_modelscopeEmbeddings()
    except Exception as e:
        embedding_model = get_modelscopeEmbeddings_gpu()

    if db == 1:
        struct_db_path = os.path.join(db_path, "TutorCode_dfg_db")
        content_db_path = os.path.join(db_path, "TutorCode_content_db")
    else:
        struct_db_path = os.path.join(db_path, "DebugBench_dfg_db")
        content_db_path = os.path.join(db_path, "DebugBench_content_db")

    candidate_ids = retrieve_by_single_structure(
        code, struct_db_path, build_dfg_query, embedding_model
    )

    content_db = FAISS.load_local(
        content_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    text = extract_text(files_loc)
    chunks = split_content(text)

    vector_res = content_db.similarity_search(
        code, k=5, filter={"id": {"$in": candidate_ids}}
    )

    bm25_res, _ = retrieve(chunks, code, content_db)
    return order(bm25_res, vector_res, code,res_path)


def build_struct_query_from_code(code: str, language="cpp"):
    ast = extract_ast_features(code, language)
    cfg = extract_cfg_features(code, language)["control_flow_shape"]
    dfg = extract_dfg_features(code, language)["data_flow_semantics"]

    return f"""
[AST]
- max_depth: {ast['ast_shape']['max_depth']}
- avg_loop_depth: {ast['ast_shape']['avg_loop_depth']}
- control_skeleton: {ast['control_skeleton']}
- assignments_in_loop_ratio: {ast['repair_anchors']['assignments_in_loop_ratio']}

[CFG]
- num_if: {cfg['num_if']}
- num_if_else: {cfg['num_if_else']}
- nested_if: {cfg['nested_if']}
- num_loops: {cfg['num_loops']}
- early_exit: {cfg['early_exit']}

[DFG]
- update_patterns: {dfg['update_patterns']}
- loop_controlled_vars: {dfg['loop_controlled_vars']}
"""


def retrieve_by_structure(code, struct_db_path, embedding_model, topk=20):
    struct_db = FAISS.load_local(
        struct_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    struct_query = build_struct_query_from_code(code)
    docs = struct_db.similarity_search(struct_query, k=topk)

    candidate_ids = [d.metadata["id"] for d in docs]
    return candidate_ids


def RAG(files_loc, db_path, res_path, code_location, db):
    # ========= 1. 加载文档 =========
    text = extract_text(files_loc)
    chunks = split_content(text)

    # ========= 2. Embedding =========
    try:
        embedding_model = get_modelscopeEmbeddings()
    except:
        embedding_model = get_modelscopeEmbeddings_gpu()

    if db == 1:
        vector_path = os.path.join(db_path, "TutorCode_content_db")
    else:
        vector_path = os.path.join(db_path, "DebugBench_content_db")

    vector_db = FAISS.load_local(
        vector_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    # ========= 3. 读取错误代码 =========
    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()

    # ========= 4. 检索 =========
    bm25_res, vector_res = retrieve(chunks, code, vector_db)

    # ========= 5. 排序（RRF） =========
    final_docs = order(bm25_res, vector_res, code, res_path)

    # ========= 6. 提取用于 Prompt 的文本 =========
    retrieved_texts = [doc.page_content for doc in final_docs]

    # ========= 7. 提取用于评估的 ID =========
    retrieved_ids = extract_ids_from_docs(final_docs, db)

    return retrieved_texts, retrieved_ids



def new_RAG(files_loc, db_path, res_path, code_location, db):
    # ========= 1. 读取 buggy code =========
    with open(code_location, 'r', encoding='utf-8') as file:
        code = file.read()

    # ========= 2. Embedding 模型 =========
    try:
        embedding_model = get_modelscopeEmbeddings()
    except Exception as e:
        embedding_model = get_modelscopeEmbeddings_gpu()
    if db == 1:
        struct_db_path = os.path.join(db_path, "TutorCode_struct_db")
        content_db_path = os.path.join(db_path, "TutorCode_content_db")
    else:
        struct_db_path = os.path.join(db_path, "DebugBench_struct_db")
        content_db_path = os.path.join(db_path, "DebugBench_content_db")

    # ========= 3. 结构库粗召回（新增） =========
    # struct_db_path = os.path.join(db_path, "DebugBench_struct_db")
    candidate_ids = retrieve_by_structure(
        code,
        struct_db_path,
        embedding_model,
        topk=20
    )

    # ========= 4. 加载内容向量库（不是新建！） =========
    # content_db_path = os.path.join(db_path, "DebugBench_content_db")
    content_db = FAISS.load_local(
        content_db_path,
        embedding_model,
        allow_dangerous_deserialization=True
    )

    # ========= 5. 加载训练文本（BM25 用，原逻辑） =========
    text = extract_text(files_loc)
    chunks = split_content(text)

    # ========= 6. 内容检索（带 filter） =========
    # 向量召回
    vector_res = content_db.similarity_search(
        code,
        k=5,
        filter={"id": {"$in": candidate_ids}}
    )

    # BM25 召回（你原有）
    bm25_res, _ = retrieve(chunks, code, content_db)

    # ========= 7. RRF 融合（原逻辑） =========
    rrf_res = order(bm25_res, vector_res, code,res_path)
    return rrf_res


def final_RAG(files_loc, db_path, res_path, code_location):
    # RAG检索结果
    rrf_res = RAG(files_loc, db_path, res_path, code_location)
    # 提取RAG检索结果中的 Fault Causes 和 Fix Solution
    fault_causes = []
    fix_solutions = []

    res_data = json.loads(rrf_res)
    try:
        fault_cause = res_data.get("Fault Causes", "")
        fix_sol = res_data.get("Fix Solution", "")
        if fault_cause:
            fault_causes.append(fault_cause)
        if fix_sol:
            fix_solutions.append(fix_sol)
    except json.JSONDecodeError:
        print("无法解析")

    # 将多个Fault Causes和Fix Solutions合并为单个字符串
    fault_causes_str = "\n".join(fault_causes)
    fix_solutions_str = "\n".join(fix_solutions)

    return fault_causes_str, fix_solutions_str


def generate_hypothetical_fix(code, experiment_model):
    """
    第一轮：利用 LLM 生成假设性修复代码
    """
    prompt = HYDE_PROMPT_TEMPLATE.format(code=code)
    try:
        # 使用你现有的 SendPrompt 模块
        fixed_code = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
        # 简单清洗，去掉 markdown 符号
        fixed_code = fixed_code.replace("```cpp", "").replace("```c++", "").replace("```", "").replace("```python", "").replace("```python3", "").replace("```java", "").strip()
        return fixed_code
    except Exception as e:
        print(f"[HyDE Error] Generation failed: {e}")
        return code  # 降级策略：如果生成失败，使用原始代码

def evaluate_relevance(query, retrieved_doc_content, experiment_model):
    """ 自反式评估 """
    if not retrieved_doc_content: return False
    prompt = REFLECTION_PROMPT_TEMPLATE.format(query=query, retrieved=retrieved_doc_content)
    try:
        res = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
        return "YES" in res.upper()
    except:
        return True # 默认放行，避免过度过滤

def evaluate_retrieval_relevance(query_code, retrieved_docs, experiment_model):
    """
    自反评估：判断检索结果是否有效
    返回: True (有效) / False (无效)
    """
    # 这里只评估 Top-1 的相关性以节省 token，也可以评估 Top-3
    if not retrieved_docs:
        return False

    prompt = REFLECTION_PROMPT_TEMPLATE.format(
        query=query_code,
        retrieved=retrieved_docs
    )
    try:
        response = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
        return "YES" in response.upper()
    except:
        return True



def calculate_metrics(retrieved_ids, ground_truth_id):
    """
    计算 Recall@K, Precision@K, nDCG@K 和 MRR

    Args:
        retrieved_ids (list): 检索到的 ID 列表 (str)
        ground_truth_id (str): 正确的 ID (str)

    Returns:
        dict: 包含所有指标的字典
    """
    metrics = {}

    # 数据清洗：转字符串并去除空格
    gt = str(ground_truth_id).strip()
    r_ids = [str(rid).strip() for rid in retrieved_ids]

    # 定义需要计算的 K 值
    k_list = [1, 3, 5]

    for k in k_list:
        # 截取前 K 个结果
        top_k_ids = r_ids[:k]

        # 判断 Ground Truth 是否在 Top-K 中
        if gt in top_k_ids:
            is_hit = 1
            # 找到具体的排名 (0-based index 转 1-based rank)
            rank_in_top_k = top_k_ids.index(gt) + 1
        else:
            is_hit = 0
            rank_in_top_k = 0

        # 1. Recall@K
        # 对于单目标检索，Recall 要么是 1 (找到了)，要么是 0 (没找到)
        metrics[f'Recall@{k}'] = is_hit

        # 2. Precision@K
        # P@K = (相关文档数) / K
        # 因为只有一个正确答案，如果找到了，精度就是 1/K
        metrics[f'Precision@{k}'] = is_hit / k

        # 3. nDCG@K
        # nDCG = DCG / IDCG
        # 只有 1 个正确答案，IDCG 恒为 1.0 (1 / log2(1+1) = 1)
        # 所以 nDCG 等于 DCG
        if is_hit:
            dcg = 1.0 / math.log2(rank_in_top_k + 1)
            metrics[f'nDCG@{k}'] = dcg
        else:
            metrics[f'nDCG@{k}'] = 0.0

    # 4. MRR (Mean Reciprocal Rank) - 针对整个列表
    try:
        # 在整个检索结果中找
        rank = r_ids.index(gt) + 1
        metrics['MRR'] = 1.0 / rank
    except ValueError:
        metrics['MRR'] = 0.0

    return metrics


def adaptive_RAG(files_loc, db_path, res_path, code_location, db, experiment_model,rank_type=1):
    """
    自适应 RAG (Coarse-to-Fine Strategy):
    1. Round 1: Structure-Aware Retrieval (AST) - 探索结构相似案例
    2. Reflection: 评估检索质量
    3. Round 2 (Conditional): HyDE Retrieval - 如果结构检索失效，使用假设性修复进行语义纠偏
    4. Rerank: BGE 重排序
    """

    # ========= 0. 基础设置 =========
    # 读取 Query 代码
    with open(code_location, 'r', encoding='utf-8') as f:
        query_code = f.read()

    # 加载 Embedding 模型
    try:
        embedding_model = get_modelscopeEmbeddings()
    except:
        embedding_model = get_modelscopeEmbeddings_gpu()

    # 设置数据库路径
    if db == 1:  # TutorCode
        content_db_path = os.path.join(db_path, "TutorCode_content_db")
        struct_db_path = os.path.join(db_path, "TutorCode_struct_db")
    else:  # DebugBench
        content_db_path = os.path.join(db_path, "DebugBench_content_db")
        struct_db_path = os.path.join(db_path, "DebugBench_struct_db")

    # 加载数据库
    content_db = FAISS.load_local(content_db_path, embedding_model, allow_dangerous_deserialization=True)

    # ========= Round 1: Structure-Aware Retrieval (AST) =========
    # print("[Adaptive RAG] Round 1: Structure-Aware Retrieval (Exploration)...")

    # 1.1 检索结构库获取 ID
    struct_ids = retrieve_by_single_structure(
        query_code, struct_db_path, build_ast_query, embedding_model, topk=20
    )

    # 1.2 利用 ID 过滤内容库 (Filter Content DB)
    if struct_ids:
        vector_docs = content_db.similarity_search(
            query_code, k=10, filter={"id": {"$in": struct_ids}}
        )
    else:
        # 如果代码太烂提取不出结构，回退到原始向量检索
        # print("[Adaptive RAG] Structure extraction failed, fallback to raw vector search.")
        vector_docs = content_db.similarity_search(query_code, k=10)

    first_round_ids = extract_ids_from_docs(vector_docs, db)
    # ========= Reflection: Self-Evaluation =========
    # print("[Adaptive RAG] Reflecting on Structural Relevance...")

    # 取 Top-1 结果的内容进行评估
    if vector_docs:
        top_doc = vector_docs[0]
        top_doc_content = (
            top_doc.page_content if hasattr(top_doc, "page_content") else str(top_doc)
        )
    else:
        top_doc_content = ""
    is_relevant = evaluate_retrieval_relevance(query_code, top_doc_content, experiment_model)

    final_vector_docs = []

    if is_relevant:
        # === Case A: 结构检索有效 ===
        # print("[Adaptive RAG] Structure Search Accepted. (Found structurally similar bug)")
        final_vector_docs = vector_docs
    else:
        # === Case B: 结构检索无效 -> 启动 HyDE ===
        # print("[Adaptive RAG] Structure Search Rejected (Irrelevant). Switching to HyDE (Exploitation)...")
        save_second_round_flag(res_path)
        ground_truth_id = get_ground_truth_id(code_location, db)

        # === NEW ③：计算并保存第一轮指标 ===
        save_first_round_metrics(
            first_round_ids,
            ground_truth_id,
            res_path
        )
        # 3.1 生成假设性修复
        hypothetical_fix = generate_hypothetical_fix(query_code, experiment_model)

        # 3.2 使用修复代码进行语义检索 (不再限制于 Struct ID)
        # 这一步是为了跳出“结构相似但逻辑无关”的局部极小值
        # final_vector_docs = content_db.similarity_search(hypothetical_fix, k=10)
        hypo_struct_ids = retrieve_by_structure(
            hypothetical_fix,
            struct_db_path,
            embedding_model,
            topk=20
        )

        # 2. 再用 fix 做内容检索（受限）
        final_vector_docs = content_db.similarity_search(
            hypothetical_fix,
            k=10,
            filter={"id": {"$in": hypo_struct_ids}}
        )

    # ========= Final Step: Fusion & Rerank =========
    # print("[Adaptive RAG] Final Fusion and Reranking...")

    # 1. 准备 BM25 (始终使用原始 Query 进行文本字面匹配)
    text_data = extract_text(files_loc)
    chunks = split_content(text_data)
    bm25_docs, _ = retrieve_with_ids(chunks, query_code, content_db, filter_ids=struct_ids)

    # 2. 调用核心排序函数 (RRF -> Save -> BGE Rerank -> Order)
    # 注意：这里传入 res_path 用于保存中间文件
    if rank_type == 1:
        final_sorted_docs = order_with_rerank(bm25_docs, final_vector_docs, query_code, res_path)
    else:
        final_sorted_docs = order_with_rerank_without_rro(bm25_docs, final_vector_docs, query_code, res_path)    

    # 3. 提取结果用于 Metrics 计算和 Prompt 构建
    final_texts = [d.page_content for d in final_sorted_docs]
    retrieved_ids = extract_ids_from_docs(final_sorted_docs, db)

    return final_texts, retrieved_ids

def get_ground_truth_id(code_location, db):
    """
    根据代码路径获取对应题目的ID。
    Args:
        code_location (str): buggy code路径
        db (int): 1表示TutorCode, 其他表示DebugBench
    Returns:
        str: 题目ID (problemId / slug_id)
    """
    import json

    path_parts = os.path.normpath(code_location).split(os.sep)

    # 假设路径中倒数第二层是数据条目唯一ID
    # 例如 .../instance_id/buggyCode/... -> 取倒数第2个
    try:
        if 'buggyCode' in path_parts:
            data_id_index = path_parts.index('buggyCode') - 1
            data_id = path_parts[data_id_index]
        else:
            print("Error: Cannot extract data instance ID from path")
            return "UNKNOWN"
    except Exception as e:
        print(f"Failed to extract data_id from path: {e}")
        return "UNKNOWN"

    # 根据数据集查找题目ID
    if db == 1:  # TutorCode
        json_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode.json"
        key_data_id = "id"
        key_question_id = "problemId"
    else:  # DebugBench
        json_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_compilable.json"
        key_data_id = "instance_id"
        key_question_id = "slug_id"

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        # 查找匹配条目
        for item in data_list:
            if str(item.get(key_data_id)) == str(data_id):
                return str(item.get(key_question_id))
        # 没找到
        print(f"Warning: Cannot find ground truth question ID for data_id={data_id}")
        return "UNKNOWN"
    except Exception as e:
        print(f"Failed to load {json_file}: {e}")
        return "UNKNOWN"

def order_with_rerank(bm25_docs, vector_docs, query, res_path):
    """
    核心排序函数：融合了 RRF、文件保存、BGE重排序、Metadata保留
    Args:
        bm25_docs: BM25检索到的 Document 对象列表
        vector_docs: 向量检索到的 Document 对象列表
        query: 查询代码
        res_path: 结果保存路径
    Returns:
        final_sorted_docs: 排序后的 Document 对象列表
    """
    # 1. RRF 融合 (基于 Content, 但保留 Doc 映射)
    doc_scores = {}
    content_to_doc_map = {}

    # 映射 Vector 结果
    for rank, doc in enumerate(vector_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + 60)

    # 映射 BM25 结果
    for rank, doc in enumerate(bm25_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + 60)

    # 初步 RRF 排序 (按 RRF 分数降序)
    # 取前 20 个给重排序模型 (太长了速度慢)
    rrf_sorted_items = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:20]
    rrf_sorted_contents = [item[0] for item in rrf_sorted_items]

    # === 保存 RRF 中间结果 (sorted_2.txt) ===
    if not os.path.exists(res_path):
        os.makedirs(res_path)

    # sorted_results_location = os.path.join(res_path, "sorted_2.txt")
    # with open(sorted_results_location, 'w', encoding='utf-8') as file:
    #     file.write(str(rrf_sorted_contents))

    # 2. BGE-Reranker 重排序(RRO)
    pairs = [[query, content] for content in rrf_sorted_contents]
    print(f"Reranking {len(pairs)} candidates...")

    scores = rerank_with_model(pairs)  # 得到 tensor scores

    # === 保存分数 (score_2.txt) ===
    # scores_location = os.path.join(res_path, 'score_2.txt')
    # with open(scores_location, 'w', encoding='utf-8') as file:
    #     file.write(str(scores.cpu().numpy().tolist()))

    # print("Rerank Scores:", scores)

    # 3. 根据分数最终排序
    # argsort 返回的是从小到大的索引，所以需要反转 [::-1]
    sorted_indices = scores.cpu().numpy().argsort()[::-1]

    final_sorted_docs = []
    final_sorted_contents = []  # 仅用于打印预览

    for idx in sorted_indices:
        content = rrf_sorted_contents[idx]
        final_sorted_contents.append(content)
        # 找回原始 Document 对象 (包含 metadata ID)
        if content in content_to_doc_map:
            final_sorted_docs.append(content_to_doc_map[content])

    if len(final_sorted_contents) > 0:
        print("Top-1 Result (sogi):", final_sorted_contents[0][:100] + "...")

    return final_sorted_docs

def order_with_rerank_without_rro(bm25_docs, vector_docs, query, res_path):
    """
    核心排序函数：仅使用 RRF 融合（去除 BGE reranker）
    Args:
        bm25_docs: BM25检索到的 Document 对象列表
        vector_docs: 向量检索到的 Document 对象列表
        query: 查询代码（保留接口一致性，不再使用）
        res_path: 结果保存路径
    Returns:
        final_sorted_docs: 排序后的 Document 对象列表
    """
    # 1. RRF 融合 (基于 Content, 但保留 Doc 映射)
    doc_scores = {}
    content_to_doc_map = {}

    # Vector 结果
    for rank, doc in enumerate(vector_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + 60)

    # BM25 结果
    for rank, doc in enumerate(bm25_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + 60)

    # 2. RRF 排序（直接作为最终结果）
    rrf_sorted_items = sorted(
        doc_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    final_sorted_docs = []
    final_sorted_contents = []

    for content, score in rrf_sorted_items:
        if content in content_to_doc_map:
            final_sorted_docs.append(content_to_doc_map[content])
            final_sorted_contents.append(content)

    if final_sorted_contents:
        print("Top-1 Result (RRF only):", final_sorted_contents[0][:100] + "...")

    return final_sorted_docs


def retrieve_with_ids(content_chunks, query, db, filter_ids=None):
    texts = []
    content_map = {}

    for doc in content_chunks:
        if filter_ids is None or doc.metadata.get("id") in filter_ids:
            texts.append(doc.page_content)
            content_map[doc.page_content] = doc

    if not texts:
        return [], []

    texts_processed = [preprocessing_func(t) for t in texts]
    vectorizer = BM25Okapi(texts_processed)

    bm25_top_texts = vectorizer.get_top_n(preprocessing_func(query), texts, n=10)
    bm25_docs = [content_map[t] for t in bm25_top_texts]

    vector_docs = db.similarity_search(query, k=10, filter={"id": {"$in": filter_ids}}) if filter_ids else db.similarity_search(query, k=10)

    return bm25_docs, vector_docs



def rrf_with_id_mapping(vector_docs, bm25_docs, k=5, m=60):
    """
    修改版 RRF：基于 Content 做融合，但保留 metadata 用于返回 ID
    """
    doc_scores = {}
    content_to_doc_map = {}  # 用于最后还原 Document 对象

    # 映射 Vector 结果
    for rank, doc in enumerate(vector_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + m)

    # 映射 BM25 结果
    for rank, doc in enumerate(bm25_docs):
        content = doc.page_content
        content_to_doc_map[content] = doc
        doc_scores[content] = doc_scores.get(content, 0) + 1 / (rank + m)

    # 排序
    sorted_contents = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:k]

    # 还原结果
    final_docs = []
    for content, score in sorted_contents:
        if content in content_to_doc_map:
            final_docs.append(content_to_doc_map[content])

    return final_docs

def save_second_round_flag(res_path):
    if not os.path.exists(res_path):
        os.makedirs(res_path)

    flag_path = os.path.join(res_path, "second_round_triggered.txt")
    with open(flag_path, "w", encoding="utf-8") as f:
        f.write("Second round (HyDE) retrieval was triggered.\n")

def save_first_round_metrics(
        first_round_ids,
        ground_truth_id,
        res_path
):
    metrics = calculate_metrics(first_round_ids, ground_truth_id)

    metrics_path = os.path.join(res_path, "first_round_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return metrics


def extract_ids_from_docs(docs, db_type):
    """
    根据数据集类型提取对应的 ID
    db=1 -> TutorCode -> problemId
    db=2 -> DebugBench -> slug_id
    """
    
    ids = []
    for doc in docs:
        # print(doc.page_content)
        if db_type == 1:
            m = re.search(r"\[problemId\]\s*(\d+)", doc.page_content)
        else:
            m = re.search(r"\[slug_id\]\s*(\d+)", doc.page_content)

        if m:
            ids.append(int(m.group(1)))   # ✅ 关键在这里
        else:
            # m = doc.page_content.problemId
            # print(m)
            ids.append(None) 
    # print(ids)
    return ids