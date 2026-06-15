import os
import re
import csv
import json
from collections import defaultdict
from bleurt import score

# -----------------------------
# 配置部分
# -----------------------------
DATASET_DIR = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"
OUTPUT_CSV = "bleurt_results_new_structure.csv"
RANGE_INDEX = 9999  # 循环的版本上限

MODELS = [
    "gemini-2.5-flash-lite-nothinking", "gemma-3n-e4b-it", "glm-4.7",
    "gpt-5.1", "kimi-k2-instruct-0905", "llama-3.3-70b-instruct",
    "phi-4-multimodal-instruct", "qwen3", "deepseek-v3.2", "minimax-m2"
]

# BLEURT scorer 初始化
print("正在初始化 BLEURT Scorer，请稍候...")
scorer = score.BleurtScorer()  # 默认使用官方标准 checkpoint

# -----------------------------
# 函数：获取第一个 explanation 并计算分数
# -----------------------------
def score_first_explanation(result_path, reference_text):
    """
    找 result.txt 中第一行包含 "explanation": 的行
    提取 explanation 内容，与 reference_text 计算 BLEURT 分数
    如果找不到 explanation，返回 None
    """
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            for line in f:
                if '"explanation":' in line:
                    # 提取 "explanation" 后的内容
                    match = re.search(r'"explanation"\s*:\s*"(.*?)"', line)
                    if match:
                        explanation = match.group(1).strip()
                        # 计算 BLEURT 分数
                        score_val = scorer.score(references=[reference_text], candidates=[explanation])
                        return score_val[0]
                    else:
                        return None
        return None
    except Exception:
        return None

# -----------------------------
# 主统计逻辑
# -----------------------------
tutor_test_path = os.path.join(DATASET_DIR, "TutorCode_Test")

# 存储分数的嵌套字典: final_scores[model][method] = [score1, score2, ...]
final_scores = defaultdict(lambda: defaultdict(list))

print("开始遍历新目录结构并计算 BLEURT 分数...\n")

for model in MODELS:
    # 动态构建每个模型需要检查的子目录映射
    methods_to_check = [
        ("6", "Full_Adaptive"),
        ("6", "w_o_Struct"),
        ("6", "w_o_HyDE"),
        ("6", "w_o_RRO"),
        ("6", "Baseline_RAG")
    ]
    
    # 针对 qwen3 追加 7/rag 目录
    if model == "qwen3":
        methods_to_check.append(("7", "rag"))

    # 遍历所有可能存在的版本目录 (1 ~ RANGE_INDEX)
    for version in range(1, RANGE_INDEX):
        version_str = str(version)
        version_path = os.path.join(tutor_test_path, version_str)
        
        # 获取当前版本的 tutorGuidance.txt
        tutor_path = os.path.join(version_path, "tutorGuidance.txt")
        if not os.path.exists(tutor_path):
            continue
            
        # 读取金标准指导并合并多行为一行
        try:
            with open(tutor_path, "r", encoding="utf-8") as f:
                reference_text = " ".join([line.strip() for line in f if line.strip()])
        except Exception:
            continue

        # 检查该模型下的各个实验方法
        for folder_num, method in methods_to_check:
            result_file = os.path.join(tutor_test_path, version_str, model, folder_num, method, "result.txt")
            
            if os.path.exists(result_file):
                score_val = score_first_explanation(result_file, reference_text)
                if score_val is not None:
                    final_scores[model][method].append(score_val)

# -----------------------------
# 整理汇总结果并输出 CSV
# -----------------------------
# 汇总所有涉及到的全部独有实验方法列名
all_methods = ["Full_Adaptive", "w_o_Struct", "w_o_HyDE", "w_o_RRO", "Baseline_RAG", "rag"]

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # 写入表头
    writer.writerow(["Model"] + all_methods)
    
    for model in MODELS:
        row = [model]
        for method in all_methods:
            scores_list = final_scores[model].get(method, [])
            if scores_list:
                # 计算该方法在所有版本上的平均分
                avg_score = sum(scores_list) / len(scores_list)
                row.append(f"{avg_score:.4f}")
            else:
                # 若无匹配样本或该模型不具备该方法（如非qwen3模型没有rag列），填入 0.0000 或留空
                row.append("0.0000")
        writer.writerow(row)

print(f"\n统计完成！所有模型的各消融组件 BLEURT 平均分数已成功保存到: {OUTPUT_CSV}")
