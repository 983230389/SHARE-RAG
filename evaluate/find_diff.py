import os

def get_top1_versions(root_path, model, dataset, experiment_index, max_version=9999):
    """
    返回 Top-1 的题目编号集合
    """
    if dataset == 2:
        base_path = os.path.join(root_path, "DebugBench_Test")
    else:
        base_path = os.path.join(root_path, "TutorCode_Test")

    top1_versions = set()

    for version in range(1, max_version):
        version_path = os.path.join(
            base_path,
            str(version),
            model,
            str(experiment_index),
            "topN_first.txt"
        )

        if not os.path.exists(version_path):
            continue

        try:
            with open(version_path, "r") as f:
                topN = int(f.read().strip())
            if topN == 1:
                top1_versions.add(version)
        except:
            continue

    return top1_versions


def compare_rag_newrag_top1(root_path, model, dataset):
    """
    对比 rag vs newrag 的 Top-1 题目
    """
    rag_idx = 1
    newrag_idx = 2

    rag_top1 = get_top1_versions(
        root_path, model, dataset, rag_idx
    )
    newrag_top1 = get_top1_versions(
        root_path, model, dataset, newrag_idx
    )

    # rag 是 top1，但 newrag 不是
    rag_only = sorted(rag_top1 - newrag_top1)

    # newrag 是 top1，但 rag 不是
    newrag_only = sorted(newrag_top1 - rag_top1)

    return rag_only, newrag_only


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

    dataset = 1  # 1 = TutorCode, 2 = DebugBench
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"

    output_dir = "./evaluate/compare_rag_newrag_debug"
    os.makedirs(output_dir, exist_ok=True)

    for model in models:
        rag_only, newrag_only = compare_rag_newrag_top1(
            root_path, model, dataset
        )

        output_path = os.path.join(output_dir, f"{model}_diff.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=== RAG Top-1 but NewRAG NOT Top-1 ===\n")
            f.write(",".join(map(str, rag_only)) + "\n\n")

            f.write("=== NewRAG Top-1 but RAG NOT Top-1 ===\n")
            f.write(",".join(map(str, newrag_only)) + "\n")

        print(f"[{model}] done")

    print("over")
