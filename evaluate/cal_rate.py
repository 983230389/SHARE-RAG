import os
from collections import Counter

def read_rank(path):
    """
    读取 topN_first.txt
    返回：
      int rank（1-based）
      None 表示无结果或异常
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            r = int(f.read().strip())
        return r if r > 0 else None
    except:
        return None


def analyze_top1_shift(
        model,
        root_path,
        dataset,
        rangeIndex=9999,
        rag_idx=1,
        newrag_idx=2
):
    if dataset == 2:
        root_path = os.path.join(root_path, "DebugBench_Test")
    else:
        root_path = os.path.join(root_path, "TutorCode_Test")

    degrade_cases = []     # rag=1, newrag!=1
    improve_cases = []     # newrag=1, rag!=1
    shift_counter = Counter()

    for version in range(1, rangeIndex):
        version_path = os.path.join(root_path, str(version))
        if not os.path.exists(version_path):
            continue

        rag_path = os.path.join(
            version_path, model, str(rag_idx), "topN_first.txt"
        )
        newrag_path = os.path.join(
            version_path, model, str(newrag_idx), "topN_first.txt"
        )

        rag_rank = read_rank(rag_path)
        newrag_rank = read_rank(newrag_path)

        if rag_rank is None or newrag_rank is None:
            continue

        # Top-1 退化
        if rag_rank == 1 and newrag_rank != 1:
            degrade_cases.append((version, rag_rank, newrag_rank))
            shift_counter[newrag_rank] += 1

        # Top-1 提升
        if newrag_rank == 1 and rag_rank != 1:
            improve_cases.append((version, rag_rank, newrag_rank))

    return {
        "num_degrade": len(degrade_cases),
        "num_improve": len(improve_cases),
        "degrade_cases": degrade_cases,
        "improve_cases": improve_cases,
        "shift_distribution": dict(shift_counter)
    }


if __name__ == "__main__":
    model = "gpt-5.1"
    dataset = 1
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset"

    result = analyze_top1_shift(
        model=model,
        root_path=root_path,
        dataset=dataset
    )

    print(f"Top-1 degrade samples: {result['num_degrade']}")
    print(f"Top-1 improve samples: {result['num_improve']}")

    print("\nNewRAG rank distribution (for degraded samples):")
    for rank, cnt in sorted(result["shift_distribution"].items()):
        print(f"  newrag_rank = {rank}: {cnt}")

    print("\nExample degraded cases (first 10):")
    for v, r1, r2 in result["degrade_cases"][:10]:
        print(f"  Problem {v}: rag={r1}, newrag={r2}")
