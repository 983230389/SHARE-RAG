import os
import json
from collections import defaultdict

def analyze_second_round_first_metrics(
        experiment_index,
        experiment_model,
        rangeIndex,
        root_path,
        dataset
):
    """
    统计：
    1）进入第二轮检索的题目号
    2）这些题目第一轮检索指标的平均值
    """

    if dataset == 2:
        root_path = os.path.join(root_path, "DebugBench_Test")
    else:
        root_path = os.path.join(root_path, "TutorCode_Test")

    metric_sum = defaultdict(float)
    count = 0
    count1 = 0
    second_round_versions = []

    for version in range(1, rangeIndex):
        
        version_path = os.path.join(root_path, str(version))
        if not os.path.exists(version_path):
            continue

        exp_path = os.path.join(
            version_path,
            experiment_model,
            str(experiment_index)
        )

        if not os.path.exists(exp_path):
            continue
        count1 +=1
        # ---------- 判定是否进入第二轮 ----------
        second_round_flag = os.path.join(exp_path, "second_round_triggered.txt")
        if not os.path.exists(second_round_flag):
            continue

        # ---------- 读取第一轮指标 ----------
        first_round_path = os.path.join(exp_path, "first_round_metrics.json")
        if not os.path.exists(first_round_path):
            continue

        try:
            with open(first_round_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            continue

        second_round_versions.append(version)

        for k, v in metrics.items():
            metric_sum[k] += v

        count += 1

    if count == 0:
        return None

    metric_avg = {k: v / count for k, v in metric_sum.items()}
    metric_avg["num_samples"] = count
    metric_avg["second_round_versions"] = second_round_versions
    # metric_avg["total"] = count1
    # print(count1)
    return metric_avg

if __name__ == "__main__":
    models = [
        "gemini-2.5-flash-lite-nothinking",
        "gemma-3n-e4b-it",
        "glm-4.7",
        "gpt-5.1",
        "kimi-k2-instruct-0905",
        "llama-3.3-70b-instruct",
        "phi-4-multimodal-instruct",
        "qwen3",
        "deepseek-v3.2",
        "minimax-m2",
        "gpt51"
    ]

    dataset = 2
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"
    exp_idx = 2

    for model in models:
        result = analyze_second_round_first_metrics(
            exp_idx,
            model,
            9999,
            root_path,
            dataset
        )

        if result is None:
            print(f"{model}: No second-round samples")
            continue

        print(f"\nModel: {model}")
        print(f"Second-round samples: {result['num_samples']}")
        print(f"Problem IDs: {result['second_round_versions'][:10]} ...")
        print(f"total: {result['total']}")
        # print(f"Total Problem IDs: {len(result['second_round_versions'])} ...")

        for k, v in result.items():
            if k not in ("num_samples", "second_round_versions"):
                print(f"  {k}: {v:.4f}")
