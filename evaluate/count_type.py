import os

import os
from collections import defaultdict

def analyze_DebugBench(
        experiment_index,
        experiment_model,
        rangeIndex,
        root_path,
        dataset,
        meta_map
):
    # category / level -> topN 统计
    category_stats = defaultdict(lambda: [0, 0, 0, 0, 0, 0])
    level_stats = defaultdict(lambda: [0, 0, 0, 0, 0, 0])

    if dataset == 2:
        root_path = os.path.join(root_path, "DebugBench_Test")
    else:
        root_path = os.path.join(root_path, "TutorCode_Test")

    for version in range(1, rangeIndex):
        version_str = str(version)
        version_path = os.path.join(root_path, version_str)
        if not os.path.exists(version_path):
            continue

        res_path = os.path.join(
            version_path,
            experiment_model,
            str(experiment_index)
        )

        topN_path = os.path.join(res_path, "topN_first.txt")

        try:
            with open(topN_path, 'r') as f:
                topN_Index = int(f.read().strip())
        except:
            continue

        if version_str not in meta_map:
            continue

        categories, level = meta_map[version_str]

        def update(stat):
            if topN_Index == 0: return
            if topN_Index <= 1: stat[0] += 1
            if topN_Index <= 2: stat[1] += 1
            if topN_Index <= 3: stat[2] += 1
            if topN_Index <= 4: stat[3] += 1
            if topN_Index <= 5: stat[4] += 1
            if topN_Index <= 10: stat[5] += 1

        # 多 category
        for c in categories:
            update(category_stats[c])

        # 单 level
        if level:
            update(level_stats[level])

    return category_stats, level_stats

import json

def load_debugbench_meta(json_path):
    """
    instance_id -> (categories, level)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = {}
    for item in data:
        instance_id = str(item["instance_id"])
        categories = item.get("category", [])
        level = item.get("level")
        meta[instance_id] = (categories, level)

    return meta


if __name__ == "__main__":
    models = [
        "gemini-3-flash-preview","gemma-3n-e4b-it","glm-4-flash",
        "gpt-5.1","kimi-k2-instruct-0905","llama-3.3-70b-instruct",
        "phi-4-multimodal-instruct","qwen3","deepseek-v3.1","minimax-m2"
    ]

    dataset = 2
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"
    json_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_compilable.json"

    methods = [
        (0, "no rag"),
        (1, "rag"),
        (2, "new rag"),
        (3, "ast"),
        (4, "cfg"),
        (5, "dfg"),
    ]

    meta_map = load_debugbench_meta(json_path)

    output_dir = "./evaluate/DebugBench_by_category_level"
    os.makedirs(output_dir, exist_ok=True)

    for model in models:
        output_path = os.path.join(output_dir, f"{model}_DebugBench.txt")

        with open(output_path, "w") as f:
            for exp_idx, method_name in methods:
                category_stats, level_stats = analyze_DebugBench(
                    exp_idx, model, 9999, root_path, dataset, meta_map
                )

                f.write(f"\n===== {method_name} =====\n")

                f.write("【Category】\n")
                for c, stats in category_stats.items():
                    f.write(f"{c}: {stats}\n")

                f.write("【Level】\n")
                for l, stats in level_stats.items():
                    f.write(f"{l}: {stats}\n")

    print("over")

