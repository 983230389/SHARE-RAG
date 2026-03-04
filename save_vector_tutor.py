import os
import json
import shutil

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from code_features.ast_features import extract_ast_features
from code_features.cfg_features import extract_cfg_features
from code_features.dfg_features import extract_dfg_features

from models.embedding_model import get_modelscopeEmbeddings



# ========== 路径配置 ==========
ALL_JSON_PATH = "Data/TutorCode_all.json"
TEST_DIR = "dataset/TutorCode_Test"
VECTOR_DB_ROOT = "Data"


# ========== 工具函数 ==========
def load_all_data(json_path: str) -> list[dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_test_ids(test_dir: str) -> set:
    return {
        int(name) for name in os.listdir(test_dir)
        if name.isdigit() and os.path.isdir(os.path.join(test_dir, name))
    }


def filter_train_data(all_data: list[dict], test_ids: set) -> list[dict]:
    return [item for item in all_data if item.get("id") not in test_ids]


def save_faiss(docs: list[Document], save_path: str):
    if os.path.exists(save_path):
        shutil.rmtree(save_path)
    db = FAISS.from_documents(docs, get_modelscopeEmbeddings())
    db.save_local(save_path)
    print(f"✔ Saved vector DB -> {save_path}")


# ========== Document 构建 ==========
def build_text_doc(sample: dict) -> Document:
    text = f"""
[Problem]
{sample.get("problemDescription", "")}

[Buggy Code]
{sample.get("incorrectCode", "")}

[Correct Code]
{sample.get("groudTruthCode", "")}

[Solution]
{sample.get("solutionDescription", "")}

[Tutor Guidance]
{sample.get("tutorGuidance", "")}
"""
    return Document(page_content=text, metadata={"id": sample["id"], "type": "text"})


def build_original_doc(sample: dict) -> Document:
    text = f"""
[Buggy Code]
{sample.get("incorrectCode", "")}
"""
    return Document(page_content=text, metadata={"id": sample["id"], "type": "original"})


def build_ast_doc(sample: dict) -> Document:
    ast = extract_ast_features(sample["incorrectCode"], "cpp")
    text = f"""
AST Summary:
- num_nodes: {ast['num_ast_nodes']}
- max_depth: {ast['max_ast_depth']}
- num_function_defs: {ast['num_function_defs']}
- num_function_calls: {ast['num_function_calls']}
- top_node_types: {ast['top_node_types']}
"""
    return Document(page_content=text, metadata={"id": sample["id"], "type": "ast"})


def build_cfg_doc(sample: dict) -> Document:
    cfg = extract_cfg_features(sample["incorrectCode"], "cpp")
    text = f"""
CFG Summary:
- num_control: {cfg['num_control']}
- num_if: {cfg['num_if']}
- num_loop: {cfg['num_loop']}
- max_branch_depth: {cfg['max_branch_depth']}
- cyclomatic_proxy: {cfg['cyclomatic_proxy']}
"""
    return Document(page_content=text, metadata={"id": sample["id"], "type": "cfg"})


def build_dfg_doc(sample: dict) -> Document:
    dfg = extract_dfg_features(sample["incorrectCode"], "cpp")
    text = f"""
DFG Summary:
- num_vars: {dfg['num_vars']}
- num_defs: {dfg['num_defs']}
- num_uses: {dfg['num_uses']}
- num_edges: {dfg['num_dfg_edges']}
- avg_fan_in: {dfg['avg_fan_in']}
- avg_fan_out: {dfg['avg_fan_out']}
"""
    return Document(page_content=text, metadata={"id": sample["id"], "type": "dfg"})


def build_all_static_doc(sample: dict) -> Document:
    return Document(
        page_content="\n".join([
            build_ast_doc(sample).page_content,
            build_cfg_doc(sample).page_content,
            build_dfg_doc(sample).page_content
        ]),
        metadata={"id": sample["id"], "type": "all_static"}
    )


# ========== 主流程 ==========
def main():
    print("🔍 Loading data...")
    all_data = load_all_data(ALL_JSON_PATH)
    test_ids = load_test_ids(TEST_DIR)
    train_data = filter_train_data(all_data, test_ids)

    print(f"📊 Train samples: {len(train_data)}")

    text_docs, original_docs = [], []
    ast_docs, cfg_docs, dfg_docs, all_static_docs = [], [], [], []

    for sample in train_data:
        try:
            text_docs.append(build_text_doc(sample))
            original_docs.append(build_original_doc(sample))
            ast_docs.append(build_ast_doc(sample))
            cfg_docs.append(build_cfg_doc(sample))
            dfg_docs.append(build_dfg_doc(sample))
            all_static_docs.append(build_all_static_doc(sample))
        except Exception as e:
            print(f"[Skip] ID={sample.get('id')} | {e}")

    os.makedirs(VECTOR_DB_ROOT, exist_ok=True)

    save_faiss(text_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_content_db"))
    save_faiss(original_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_vector_db"))
    save_faiss(ast_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_ast_db"))
    save_faiss(cfg_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_cfg_db"))
    save_faiss(dfg_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_dfg_db"))
    save_faiss(all_static_docs, os.path.join(VECTOR_DB_ROOT, "TutorCode_struct_db"))

    print("🎉 All vector databases built successfully!")


if __name__ == "__main__":
    main()
