import json
import random
import os
import shutil

# LangChain 新版导入路径
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from code_features.ast_features import extract_ast_features
from code_features.cfg_features import extract_cfg_features
from code_features.dfg_features import extract_dfg_features
from collections import Counter

from models.embedding_model import get_modelscopeEmbeddings


def read_json_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


# 创建文件夹并保存数据到文件
def save_code_to_file(id, incorrect_code, ground_truth_code, base_dir):
    id_folder_path = os.path.join(base_dir, str(id))
    os.makedirs(id_folder_path, exist_ok=True)

    buggyCode_path = os.path.join(id_folder_path, "buggyCode")
    os.makedirs(buggyCode_path, exist_ok=True)

    correctCode_path = os.path.join(id_folder_path, "correctCode")
    os.makedirs(correctCode_path, exist_ok=True)

    incorrect_code_file = os.path.join(buggyCode_path, "buggy_code.cpp")
    with open(incorrect_code_file, 'w', encoding='utf-8') as file:
        file.write(incorrect_code)

    ground_truth_code_file = os.path.join(correctCode_path, "true_code.cpp")
    with open(ground_truth_code_file, 'w', encoding='utf-8') as file:
        file.write(ground_truth_code)


def save_problem_to_file(id, problemDes, base_dir):
    id_folder_path = os.path.join(base_dir, str(id))
    os.makedirs(id_folder_path, exist_ok=True)

    ProblemDes_path = os.path.join(id_folder_path, "ProblemDes")
    os.makedirs(ProblemDes_path, exist_ok=True)

    problem_file = os.path.join(ProblemDes_path, "problem.txt")
    with open(problem_file, 'w', encoding='utf-8') as file:
        file.write(problemDes)


# 按 8:2 划分数据集
def split_dataset(data, train_ratio=0.5):
    filtered_data = [item for item in data if 1 <= item['id'] <= 1239]
    random.shuffle(filtered_data)
    split_index = int(len(filtered_data) * train_ratio)
    train_data = filtered_data[:split_index]
    test_data = filtered_data[split_index:]
    return train_data, test_data


# 提取incorrectCode和groudTruthCode并输出到对应目录
def extract_codes_and_save(dataset, base_dir):
    for item in dataset:
        id = item.get("id")
        incorrect_code = item.get("incorrectCode", "")
        ground_truth_code = item.get("groudTruthCode", "")
        problemDes = item.get("problemDescription", "")

        save_problem_to_file(id, problemDes, base_dir)
        save_code_to_file(id, incorrect_code, ground_truth_code, base_dir)


def write_train(train_data, base_dir="Data"):
    txt_file_path = os.path.join(base_dir, "TutorCode_train.txt")

    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        for index, data in enumerate(train_data):
            json_str = json.dumps(
                data,
                ensure_ascii=False,
                separators=(',', ':')
            )
            txt_file.write(json_str)
            if index < len(train_data) - 1:
                txt_file.write(',\n')
            else:
                txt_file.write('\n')

    print(f"已生成训练集文件：{txt_file_path}")


# 加载TutorCode_train.txt文件
def extract_text(file_path):
    loader = TextLoader(file_path, encoding="utf-8")
    text = loader.load()
    return text


# 文本分块
def split_content(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=0,
        length_function=len,
        separators=['\n']
    )
    chunks = text_splitter.split_documents(text)
    return chunks

def build_content_document(sample,index):
    code = sample.get("incorrectCode", "")
    problem = sample.get("problemDescription", "")
    correct = sample.get("groudTruthCode","")
    solution = sample.get("solutionDescription","")
    tutor = sample.get("tutorGuidance","")
    sample_id = sample.get("id")
    problem_id = sample.get("problemId")
    judgeResult = sample.get("judgeResult")

    text = f"""
[Problem]
{problem}

[Buggy Code]
{code}

[Correct Code]
{correct}

[solutionDescription]
{solution}

[tutorGuidance]
{tutor}

[problemId]
{problem_id}

[judgeResult]
{judgeResult}
"""
    if index == 0:
        print(text)
    return Document(
        page_content=text,
        metadata={
            "id": sample_id,
            "type": "content"
        }
    )

def build_struct_document(sample, index):
    code = sample.get("incorrectCode", "")
    sample_id = sample.get("id")
    language = "cpp"

    ast_feat = extract_ast_features(code, language)
    cfg_feat = extract_cfg_features(code, language)
    dfg_feat = extract_dfg_features(code, language)

    # ========= AST =========
    ast_shape = ast_feat.get("ast_shape", {})
    control_skeleton = ast_feat.get("control_skeleton", [])
    repair_anchors = ast_feat.get("repair_anchors", {})

    # ========= CFG =========
    cfg_shape = cfg_feat.get("control_flow_shape", {})

    # ========= DFG =========
    dfg_sem = dfg_feat.get("data_flow_semantics", {})

    # 🔥 核心：结构感知 + 可嵌入文本
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
"""

    if index == 0:
        print(struct_text)

    return Document(
        page_content=struct_text.strip(),
        metadata={
            "id": sample_id,
            "type": "structure",
            "language": language
        }
    )


def build_dual_documents(dataset):
    content_docs = []
    struct_docs = []
    index = 0
    for sample in dataset:
        try:
            content_docs.append(build_content_document(sample,index))
            struct_docs.append(build_struct_document(sample,index))
            index += 1
        except Exception as e:
            print(f"[Skip] {sample.get('id')} : {e}")

    return content_docs, struct_docs


# 保存向量数据库
def save_vectorstore(content_chunks, embedding_model, db_path):
    db = FAISS.from_documents(content_chunks, embedding_model)

    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    db.save_local(db_path)
    return db


# 构建向量数据库
def build_vector_database(txt_file_path, db_path):
    text = extract_text(txt_file_path)
    chunks = split_content(text)

    embedding_model = get_modelscopeEmbeddings()

    db = save_vectorstore(chunks, embedding_model, db_path)
    print(f"向量数据库已保存到：{db_path}")
    return db

def build_vector_db(docs, db_path):
    embedding_model = get_modelscopeEmbeddings()

    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    db = FAISS.from_documents(docs, embedding_model)
    db.save_local(db_path)

    print(f"Vector DB saved to {db_path}")
    return db


# 主程序
if __name__ == "__main__":
    input_filename = 'Data/TutorCode.json'
    data = read_json_file(input_filename)

    train_data, test_data = split_dataset(data)

    content_docs, struct_docs = build_dual_documents(train_data)
    write_train(train_data)

    txt_file_path = os.path.join("Data", "TutorCode_train.txt")
    db_path = os.path.join("Data", "TutorCode_vector_db")
    content_path = os.path.join("Data", "TutorCode_content_db")
    struct_path = os.path.join("Data", "TutorCode_struct_db")

    build_vector_db(content_docs, content_path)
    build_vector_db(struct_docs, struct_path)
    build_vector_database(txt_file_path, db_path)

    extract_codes_and_save(test_data, base_dir="dataset/TutorCode_Test")
    extract_codes_and_save(data, base_dir="dataset/TutorCode_All")

    print("✔ 测试集与全量数据保存完成！")
