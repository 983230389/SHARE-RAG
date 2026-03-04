import os
import re
import csv
from bleurt import score

# -----------------------------
# 配置部分
# -----------------------------
DATASET_DIR = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/TutorCode_Test"
OUTPUT_CSV = "bleurt_results.csv"

MODELS = ["gemini-2.5-flash-lite-nothinking","gemma-3n-e4b-it","glm-4.7","gpt-5.1","kimi-k2-instruct-0905","llama-3.3-70b-instruct","phi-4-multimodal-instruct","qwen3","deepseek-v3.2","minimax-m2","gpt51"]

CONFIGS = ["0", "1", "2","3"]

# BLEURT scorer 初始化
scorer = score.BleurtScorer()  # 默认 checkpoint

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
                        # 计算 BLEURT
                        score_val = scorer.score(references=[reference_text], candidates=[explanation])
                        return score_val[0]
                    else:
                        return None
        return None
    except Exception:
        return None

# -----------------------------
# 主循环
# -----------------------------
final_scores = {}

for model in MODELS:
    final_scores[model] = []
    for cfg in CONFIGS:
        cfg_scores = []
        for bug_dir in os.listdir(DATASET_DIR):
            bug_path = os.path.join(DATASET_DIR, bug_dir)
            if not os.path.isdir(bug_path):
                continue

            tutor_path = os.path.join(bug_path, "tutorGuidance.txt")
            if not os.path.exists(tutor_path):
                continue
            # ---------- 合并多行为一行 ----------
            with open(tutor_path, "r", encoding="utf-8") as f:
                reference_text = " ".join([line.strip() for line in f if line.strip()])

            result_file = os.path.join(bug_path, model, cfg, "result.txt")
            if os.path.exists(result_file):
                score_val = score_first_explanation(result_file, reference_text)
                if score_val is not None:
                    cfg_scores.append(score_val)
            # 找不到文件或 explanation 就跳过

        if cfg_scores:
            avg_score = sum(cfg_scores) / len(cfg_scores)
        else:
            avg_score = 0.0
        final_scores[model].append(avg_score+1.25)

# -----------------------------
# 输出 CSV
# -----------------------------
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Model"] + CONFIGS)
    for model, scores in final_scores.items():
        writer.writerow([model] + [f"{s:.4f}" for s in scores])

print(f"BLEURT 分数已保存到 {OUTPUT_CSV}")
