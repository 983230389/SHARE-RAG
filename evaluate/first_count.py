import os
import numpy as np

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
    # model = "gpt-5.1"
    models = ["gemini-2.5-flash-lite-nothinking","gemma-3n-e4b-it","glm-4.7","gpt-5.1","kimi-k2-instruct-0905","llama-3.3-70b-instruct","phi-4-multimodal-instruct","qwen3","deepseek-v3.2","minimax-m2"]
    dataset = 1  # 1 = TutorCode, 2 = DebugBench
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"

    # experiment_index -> 方法名称
    methods = [
        (0, "no rag"),
        (1, "rag"),
        (2, "new rag"),
        (3, "no rro")
        # (4, "cfg"),
        # (5, "dfg"),
    ]
    for model in models:
        output_dir = "./evaluate/TutorCode1"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{model}_TutorCode_all.txt")

        with open(output_path, "w") as f:
            for exp_idx, method_name in methods:
                result = analyze_DebugBench(
                    exp_idx,
                    model,
                    9999,
                    root_path,
                    dataset
                )
                f.write(f"{method_name}: {result}\n")
                # print(exp_idx)
    topk_results = {}

    for model in models:
        result = analyze_DebugBench(
            exp_idx,  # 比如 new rag
            model,
            9999,
            root_path,
            dataset
        )

        if result is None:
            continue

        total = sum(result)
        topk_results[model] = normalize_topk(result, total)

    std_result = compute_topk_std_across_models(topk_results)

    print("Top-K Std Across Models:")
    for k, v in std_result.items():
        print(f"{k}: {v:.4f}")

    print("over")
