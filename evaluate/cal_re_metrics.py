import os
import json
from collections import defaultdict
import numpy as np

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

    dataset = 2  # 1 = TutorCode, 2 = DebugBench
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"

    methods = [
        (1, "rag"),
        (2, "new rag")
    ]

    output_dir = "./evaluate/retrieval_metrics2"
    os.makedirs(output_dir, exist_ok=True)

    for model in models:
        output_path = os.path.join(output_dir, f"{model}_retrieval_avg.txt")

        with open(output_path, "w") as f:
            f.write(f"Model: {model}\n")
            f.write("=" * 50 + "\n")

            for exp_idx, method_name in methods:
                result = analyze_retrieval_metrics(
                    exp_idx,
                    model,
                    9999,
                    root_path,
                    dataset
                )

                if result is None:
                    f.write(f"{method_name}: No valid samples\n\n")
                    continue

                f.write(f"{method_name} (samples={result['num_samples']}):\n")
                for k, v in sorted(result.items()):
                    if k != "num_samples":
                        f.write(f"  {k}: {v:.4f}\n")
                f.write("\n")

    print("Retrieval metrics analysis done.")
    retrieval_results = {}

    for model in models:
        result = analyze_retrieval_metrics(
            2,   # new rag
            model,
            9999,
            root_path,
            dataset
        )
        if result:
            retrieval_results[model] = result
    metrics = [
    "MRR",
    "Precision@1",
    "Recall@1",
    "nDCG@3",
    "nDCG@5"
    ]   

    print("Retrieval Metric Std Across Models:")
    for m in metrics:
        std = compute_metric_std(retrieval_results, m)
        print(f"{m}: {std:.4f}")


