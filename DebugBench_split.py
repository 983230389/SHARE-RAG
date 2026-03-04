import json
import random
import os
import shutil
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from models.embedding_model import get_modelscopeEmbeddings
from langchain_core.documents import Document
from code_features.ast_features import extract_ast_features
from code_features.cfg_features import extract_cfg_features
from code_features.dfg_features import extract_dfg_features



# 读取 JSON 数据
def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)


# 根据 language 选择后缀
def get_extension(language):
    lang = language.lower()
    if lang == "cpp":
        return ".cpp"
    elif lang == "java":
        return ".java"
    elif lang == "python3":
        return ".py"
    else:
        raise ValueError(f"Unsupported language type: {language}")

def build_content_document(item):
    instance_id = item["instance_id"]
    question = item.get("question", "")
    buggy_code = item.get("buggy_code", "")
    correct_code = item.get("correct_code", "")
    bug_exp = item.get("bug_explanation", "")
    sol_exp = item.get("solution_explanation", "")
    slug_id = item.get("slug_id")
    category = item.get("category")
    examples = item.get("examples")

    text = f"""
[Problem]
{question}

[Buggy Code]
{buggy_code}

[Bug Explanation]
{bug_exp}

[Correct Code]
{correct_code}

[Solution Explanation]
{sol_exp}

[slug_id]
{slug_id}

[category]
{category}

[examples]
{examples}
"""

    return Document(
        page_content=text,
        metadata={
            "id": instance_id,
            "type": "content"
        }
    )

def build_struct_document(item):
    instance_id = item["instance_id"]
    code = item.get("buggy_code", "")
    language = item["language"].lower()

    if language == "python3":
        language = "python"

    # ===== Extract features =====
    ast_feat = extract_ast_features(code, language)
    cfg_feat = extract_cfg_features(code, language)
    dfg_feat = extract_dfg_features(code, language)

    # ===== AST =====
    ast_shape = ast_feat.get("ast_shape", {})
    control_skeleton = ast_feat.get("control_skeleton", [])
    repair_anchors = ast_feat.get("repair_anchors", {})

    # ===== CFG =====
    cfg_shape = cfg_feat.get("control_flow_shape", {})

    # ===== DFG =====
    dfg_sem = dfg_feat.get("data_flow_semantics", {})

    # ===== Structure-aware embedding text =====
    struct_text = f"""
[AST Structure]
- Max Depth: {ast_shape.get("max_depth")}
- Avg Loop Depth: {ast_shape.get("avg_loop_depth")}
- Control Skeleton: {' -> '.join(control_skeleton)}

[AST Repair Anchors]
- Assignments-in-loop Ratio: {repair_anchors.get("assignments_in_loop_ratio")}

[CFG Structure]
- Num If: {cfg_shape.get("num_if")}
- Num If-Else: {cfg_shape.get("num_if_else")}
- Nested If: {cfg_shape.get("nested_if")}
- Num Loops: {cfg_shape.get("num_loops")}
- Early Exit in Loop: {cfg_shape.get("early_exit")}
- Conditional Loop Exit: {cfg_shape.get("loop_with_conditional_exit")}

[DFG Semantics]
- Update Patterns: {', '.join(dfg_sem.get("update_patterns", []))}
- Loop Controlled Vars: {', '.join(dfg_sem.get("loop_controlled_vars", []))}
""".strip()

    return Document(
        page_content=struct_text,
        metadata={
            "id": instance_id,
            "type": "structure",
            "language": language
        }
    )


def build_dual_documents(dataset):
    content_docs = []
    struct_docs = []

    for item in dataset:
        try:
            content_docs.append(build_content_document(item))
            struct_docs.append(build_struct_document(item))
        except Exception as e:
            print(f"[Skip] {item.get('instance_id')} : {e}")

    return content_docs, struct_docs

def build_vector_db(docs, db_path):
    embedding_model = get_modelscopeEmbeddings()

    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    db = FAISS.from_documents(docs, embedding_model)
    db.save_local(db_path)

    print(f"✔ Vector DB saved to {db_path}")
    return db


# 保存 buggy 与 correct 代码文件 + 文本说明
def save_code_files(instance_id, item, base_dir):
    language = item["language"]
    buggy_code = item["buggy_code"]
    correct_code = item["correct_code"]
    bug_exp = item.get("bug_explanation", "")
    sol_exp = item.get("solution_explanation", "")

    ext = get_extension(language)

    # 创建文件夹
    id_folder_path = os.path.join(base_dir, str(instance_id))
    buggy_dir = os.path.join(id_folder_path, "buggyCode")
    correct_dir = os.path.join(id_folder_path, "correctCode")

    os.makedirs(buggy_dir, exist_ok=True)
    os.makedirs(correct_dir, exist_ok=True)

    # ------ buggy code 文件 ------
    buggy_file = os.path.join(buggy_dir, "buggy_code" + ext)
    with open(buggy_file, "w", encoding="utf-8") as f:
        f.write(buggy_code)

    # ------ bug explanation (txt) ------
    bug_exp_file = os.path.join(buggy_dir, "bug_explanation.txt")
    with open(bug_exp_file, "w", encoding="utf-8") as f:
        if isinstance(bug_exp, list):
            f.write("\n".join(bug_exp))
        else:
            f.write(str(bug_exp))

    # ------ correct code 文件 ------
    correct_file = os.path.join(correct_dir, "true_code" + ext)
    with open(correct_file, "w", encoding="utf-8") as f:
        f.write(correct_code)

    # ------ solution explanation (txt) ------
    sol_exp_file = os.path.join(correct_dir, "solution_explanation.txt")
    with open(sol_exp_file, "w", encoding="utf-8") as f:
        f.write(sol_exp)


# 保存 question 文件
def save_problem(instance_id, question, base_dir):
    id_folder_path = os.path.join(base_dir, str(instance_id))
    problem_dir = os.path.join(id_folder_path, "ProblemDes")
    os.makedirs(problem_dir, exist_ok=True)

    problem_file = os.path.join(problem_dir, "problem.txt")
    with open(problem_file, "w", encoding="utf-8") as f:
        f.write(question)


# 8:2 分割数据集
def split_dataset(data, train_ratio=0.5):
    data_copy = data[:]
    random.shuffle(data_copy)
    split_idx = int(len(data_copy) * train_ratio)
    return data_copy[:split_idx], data_copy[split_idx:]


# 保存某组数据（全部或测试集）
def save_dataset(dataset, base_dir, save_by_language=False):
    for item in dataset:
        instance_id = item["instance_id"]
        question = item["question"]
        language = item["language"].lower()
        if language == "python3":
            language = "py"
        # 保存到基础目录
        save_problem(instance_id, question, base_dir)
        save_code_files(instance_id, item, base_dir)

        # 如果需要按语言分类保存
        if save_by_language:
            # 根据基础目录的后缀生成语言分类目录
            if "_All" in base_dir:
                language_base_dir = base_dir.replace("_All", f"_{language.capitalize()}")
            elif "_Test" in base_dir:
                language_base_dir = base_dir.replace("_Test", f"_{language}")
            else:
                # 默认处理：在基础目录后添加语言信息
                language_base_dir = f"{base_dir}_{language.capitalize()}"

            save_problem(instance_id, question, language_base_dir)
            save_code_files(instance_id, item, language_base_dir)


# 将训练集保存为 txt（每行一个 JSON）
def write_train_txt(train_data, output_path="Data/DebugBench_train.txt"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✔ 训练集 TXT 已生成：{output_path}")


# 加载DebugBench_train.txt文件
def extract_text(file_path):
    loader = TextLoader(file_path)
    text = loader.load()
    return text


# 将文本内容分割成块
def split_content(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
        separators=['\n']
    )
    chunks = text_splitter.split_documents(text)
    return chunks


# 将文本块保存到向量数据库
def save_vectorstore(content_chunks, embedding_model, db_path):
    db = FAISS.from_documents(content_chunks, embedding_model)
    db_location = os.path.join(db_path)
    # 如果目录存在，先删除
    if os.path.exists(db_location):
        shutil.rmtree(db_location)
    # 保存向量数据库
    db.save_local(db_location)
    return db


# 构建向量数据库
def build_vector_database(txt_file_path, db_path):
    # 加载文档
    text = extract_text(txt_file_path)
    # 将获取到的数据内容划分成块
    chunks = split_content(text)
    # 获取embedding模型 - 使用默认的HuggingFaceEmbeddings
    embedding_model = get_modelscopeEmbeddings()
    # 创建向量数据库对象，并将文本embedding后存入到里面
    db = save_vectorstore(chunks, embedding_model, db_path)
    print(f"✔ 向量数据库已保存到：{db_path}")
    return db


# 主逻辑
if __name__ == "__main__":
    json_path = "Data/DebugBench_compilable.json"
    data = read_json_file(json_path)

    test_data,train_data = split_dataset(data)

    # ===== 新增：构建内容 & 结构 Documents =====
    content_docs, struct_docs = build_dual_documents(train_data)

    # ===== 原有逻辑：保存数据 =====
    save_dataset(data, base_dir="dataset/DebugBench_All", save_by_language=False)
    save_dataset(test_data, base_dir="dataset/DebugBench_Test", save_by_language=True)
    print(len(train_data), len(test_data))

    # ===== 原有逻辑：txt + 内容向量 =====
    output_path = "Data/DebugBench_train.txt"
    write_train_txt(train_data, output_path=output_path)

    content_db_path = "Data/DebugBench_content_db"
    struct_db_path = "Data/DebugBench_struct_db"
    db_path = "Data/DebugBench_vector_db"
    
    build_vector_database(output_path, db_path)
    # ===== 新增：双向量库 =====
    build_vector_db(content_docs, content_db_path)
    build_vector_db(struct_docs, struct_db_path)

    print("✔ 内容向量库 + 结构向量库 构建完成")
