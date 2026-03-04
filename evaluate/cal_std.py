import os
import json
from collections import defaultdict
import numpy as np

def compute_std_across_models(results_dict):
    """
    results_dict:
      model -> metric_value (float)

    return:
      std (float)
    """
    values = list(results_dict.values())
    if len(values) < 2:
        return 0.0
    return np.std(values, ddof=1)

def compute_topk_std_for_method(models, exp_idx, root_path, dataset):
    """
    return:
      dict: Top-K -> std
    """
    topk_results = defaultdict(dict)

    for model in models:
        result = analyze_DebugBench(
            exp_idx,
            model,
            9999,
            root_path,
            dataset
        )

        if result is None:
            continue

        total = sum(result)
        if total == 0:
            continue

        normalized = [v / total for v in result]
        keys = ["Top-1", "Top-2", "Top-3", "Top-4", "Top-5", "Top-10"]

        for k, v in zip(keys, normalized):
            topk_results[k][model] = v

    return {k: compute_std_across_models(v) for k, v in topk_results.items()}

def compute_retrieval_std_for_method(models, exp_idx, root_path, dataset):
    metric_values = defaultdict(dict)

    for model in models:
        result = analyze_retrieval_metrics(
            exp_idx,
            model,
            9999,
            root_path,
            dataset
        )

        if result is None:
            continue

        for k, v in result.items():
            if k == "num_samples":
                continue
            metric_values[k][model] = v

    return {k: compute_std_across_models(v) for k, v in metric_values.items()}


def compute_metric_std(results, metric_name):
    values = [v[metric_name] for v in results.values()]
    return np.std(values, ddof=1)


def analyze_retrieval_metrics(experiment_index, experiment_model, rangeIndex, root_path, dataset):
    """
    统计某一个 model + 方法(exp_index) 下的检索指标平均值
    """
    if dataset == 2:
        root_path = os.path.join(root_path, "DebugBench_Test")
    else:
        root_path = os.path.join(root_path, "TutorCode_Test")

    metric_sum = defaultdict(float)
    count = 0

    for version in range(1, rangeIndex):
        version_path = os.path.join(root_path, str(version))
        if not os.path.exists(version_path):
            continue

        metrics_path = os.path.join(
            version_path,
            experiment_model,
            str(experiment_index),
            "retrieval_metrics.txt"
        )

        if not os.path.exists(metrics_path):
            continue

        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except:
            continue

        for k, v in metrics.items():
            metric_sum[k] += v

        count += 1

    if count == 0:
        return None

    # 计算平均值
    metric_avg = {k: v / count for k, v in metric_sum.items()}
    metric_avg["num_samples"] = count

    return metric_avg


def normalize_topk(topk_counts, total):
    return [v / total for v in topk_counts]

def compute_topk_std_across_models(results):
    """
    results: dict
      model -> [top1, top2, top3, top4, top5, top10]
    """
    arr = np.array(list(results.values()))
    stds = np.std(arr, axis=0, ddof=1)
    return {
        "Top-1": stds[0],
        "Top-2": stds[1],
        "Top-3": stds[2],
        "Top-4": stds[3],
        "Top-5": stds[4],
        "Top-10": stds[5],
    }


def analyze_DebugBench(experiment_index, experiment_model, rangeIndex, root_path, dataset):
    top1 = top2 = top3 = top4 = top5 = top10 = topNull = 0

    if dataset == 2:
        root_path = os.path.join(root_path, "DebugBench_Test")
    else:
        root_path = os.path.join(root_path, "TutorCode_Test")

    existing_versions = []
    for version in range(1, rangeIndex):
        version_path = os.path.join(root_path, str(version))
        if os.path.exists(version_path):
            existing_versions.append(str(version))

    if not existing_versions:
        print("没有有效的版本")
        return None

    for version_str in existing_versions:
        res_path = os.path.join(
            root_path,
            version_str,
            experiment_model,
            str(experiment_index)
        )

        topN_Index = None
        topN_path = os.path.join(res_path, "topN_first.txt")

        try:
            with open(topN_path, 'r') as file:
                topN_Index = int(file.read().strip())
        except:
            # 没有结果，视为 Top-10 之外
            topNull += 1
            continue
        if topN_Index == 0:
            continue
        if topN_Index <= 1:
            top1 += 1
        if topN_Index <= 2:
            top2 += 1
        if topN_Index <= 3:
            top3 += 1
        if topN_Index <= 4:
            top4 += 1
        if topN_Index <= 5:
            top5 += 1
        if topN_Index <= 10:
            top10 += 1
        else:
            topNull += 1

    return [top1, top2, top3, top4, top5, top10]

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
        "minimax-m2"
    ]

    dataset = 1  # 1 = TutorCode
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"

    methods = {
        "RAG": 1,
        "New RAG": 2
    }

    print("\n===== Top-K Ranking Stability (Std Across Models) =====")
    topk_std_results = {}

    for name, idx in methods.items():
        stds = compute_topk_std_for_method(
            models, idx, root_path, dataset
        )
        topk_std_results[name] = stds
        print(f"\n{name}:")
        for k, v in stds.items():
            print(f"  {k}: {v:.4f}")

    print("\n===== Retrieval Metric Stability (Std Across Models) =====")
    retrieval_std_results = {}

    for name, idx in methods.items():
        stds = compute_retrieval_std_for_method(
            models, idx, root_path, dataset
        )
        retrieval_std_results[name] = stds
        print(f"\n{name}:")
        for k, v in stds.items():
            print(f"  {k}: {v:.4f}")

    print("\n===== Stability Comparison (RAG → New RAG) =====")
    for metric in retrieval_std_results["RAG"]:
        rag_std = retrieval_std_results["RAG"][metric]
        new_std = retrieval_std_results["New RAG"][metric]
        diff = rag_std - new_std
        arrow = "↓" if diff > 0 else "↑"
        print(f"{metric}: {rag_std:.4f} → {new_std:.4f} ({arrow}{abs(diff):.4f})")

