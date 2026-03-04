import os
import pickle

def analyze_DebugBench(experiment_index, experiment_model, rangeIndex, root_path):
    top1 = top2 = top3 = top4 = top5 = top10 = topNull = 0
    err_list = []

    top1_list = set()
    top3_list = set()
    top5_list = set()
    top10_list = set()

    existing_versions = []

    # 确定存在的版本
    for version in range(1, rangeIndex):
        version_str = str(version)
        version_path = os.path.join(root_path, version_str)
        if os.path.exists(version_path):
            existing_versions.append(version_str)

    if not existing_versions:
        print("没有有效的版本")
        return

    for version_str in existing_versions:
    # with open("/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/DebugBench_Filter_Data.pkl", "rb") as f:
    #     DebugBench_Filter_Data = pickle.load(f)
    # for versionInt in range(1, 590):
    #     version_str = "v" + str(versionInt);
    #     if version_str not in DebugBench_Filter_Data:
    #         print("跳过:" + version_str)
    #         continue

        res_path = os.path.join(root_path, version_str, experiment_model, str(experiment_index))

        topN_multi_path = os.path.join(res_path, "topN_multi.txt")

        topN_multi = []
        try:
            with open(topN_multi_path, 'r') as file:
                topN_multi_content = file.read().strip()
                if topN_multi_content:
                    # 假设 topN_multi.txt 中存储的是一个列表，例如 "[1, 3, 5]"
                    topN_multi = eval(topN_multi_content)
                else:
                    print(f"topN_multi.txt 内容为空: {topN_multi_path}")
        except Exception as e:
            print(f"读取 topN_multi.txt 失败: {topN_multi_path}, 错误: {e}")
            continue  # 跳过当前版本，继续下一个

        # 统计每个错误的位置
        for topN_Index in topN_multi:
            if 0 < topN_Index <= 1:
                top1 += 1
                top1_list.add(version_str)
            if 0 < topN_Index <= 2:
                top2 += 1
            if 0 < topN_Index <= 3:
                top3 += 1
                top3_list.add(version_str)
            if 0 < topN_Index <= 4:
                top4 += 1
            if 0 < topN_Index <= 5:
                top5 += 1
                top5_list.add(version_str)
            if 0 < topN_Index <= 10:
                top10 += 1
                top10_list.add(version_str)
            else:
                topNull += 1

    nums = [top1, top2, top3, top4, top5, top10]
    return nums

def analyze_Codeflaws(experiment_index, experiment_model, rangeIndex, root_path):
    top1 = top2 = top3 = top4 = top5 = top10 = topNull = 0

    top1_list = set()
    top3_list = set()
    top5_list = set()
    top10_list = set()
    # root_path = "D:/私人资料/论文/大模型相关/大模型错误定位实证研究/data/codeflaws/version"
    Codeflaws_Filter_Data = []
    with open("/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/Codeflaws_Filter_Data.pkl", "rb") as f:
        Codeflaws_Filter_Data = pickle.load(f)

    process_num = 0

    for versionInt in range(1, 1544):
        versionStr = "v" + str(versionInt)
        if versionStr not in Codeflaws_Filter_Data:
            print("跳过:" + versionStr)
            continue

        process_num += 1
        if process_num > rangeIndex:
            break

        print(f"正在跑Codeflaws上的 {experiment_model} 实验： {experiment_index} 的第 {process_num} 个程序")
        print("processing: " + versionStr)

        # 数据目录
        ans_path = os.path.join(root_path, versionStr, "test_data", experiment_model, str(experiment_index))
        topN_multi_path = os.path.join(ans_path, "topN_multi.txt")

        topN_multi = []
        try:
            with open(topN_multi_path, 'r') as file:
                topN_multi_content = file.read().strip()
                if topN_multi_content:
                    # 假设 topN_multi.txt 中存储的是一个列表，例如 "[1, 3, 5]"
                    topN_multi = eval(topN_multi_content)
                else:
                    print(f"topN_multi.txt 内容为空: {topN_multi_path}")
        except Exception as e:
            print(f"读取 topN_multi.txt 失败: {topN_multi_path}, 错误: {e}")
            continue  # 跳过当前版本，继续下一个

        # 处理 topN_multi 数据，并统计每一个程序的 Top-N
        for topN_Index in topN_multi:
            if 0 < topN_Index <= 1:
                top1 += 1
                top1_list.add(versionInt)
            if 0 < topN_Index <= 2:
                top2 += 1
            if 0 < topN_Index <= 3:
                top3 += 1
                top3_list.add(versionInt)
            if 0 < topN_Index <= 4:
                top4 += 1
            if 0 < topN_Index <= 5:
                top5 += 1
                top5_list.add(versionInt)
            if 0 < topN_Index <= 10:
                top10 += 1
                top10_list.add(versionInt)
            else:
                topNull += 1

    nums = [top1, top2, top3, top4, top5, top10, topNull]
    return top1_list

if __name__ == "__main__":
    title = "TutorCode-base"
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"
    ans_gpt4o = analyze_DebugBench(2, "gpt-4o", 1239, root_path)
    ans_gpt3_5 = analyze_DebugBench(2, "gpt-3.5-turbo", 1239, root_path)
    ans_chatGlm3 = analyze_DebugBench(1, "glm-3-turbo", 1239, root_path)
    ans_llama = analyze_DebugBench(1, "llama-3.1-70b", 1239, root_path)
    ans_deepseek = analyze_DebugBench(1, "deepseek-chat", 1239, root_path)
    ans_o1preview = analyze_DebugBench(1, "o1-preview-lyt", 1239, root_path)
    ans_o3mini = analyze_DebugBench(2, "o3-mini", 1239, root_path)
    ans_claude = analyze_DebugBench(2, "claude-3-haiku-20240307", 1239, root_path)
    ans_qwen = analyze_DebugBench(2, "qwen-turbo", 1239, root_path)

    with open("./"+title+".txt", 'w') as file:
        file.write("name:  top1 top2 top3 top4 top5 top10" + '\n')
        file.write("ans_gpt4: "+str(ans_gpt4o)+'\n')
        file.write("ans_gpt3_5: " + str(ans_gpt3_5)+'\n')
        file.write("ans_chatGlm3: " + str(ans_chatGlm3)+'\n')
        file.write("ans_llama: " + str(ans_llama)+'\n')
        file.write("ans_deepseek: " + str(ans_deepseek)+'\n')
        file.write("ans_o1preview: " + str(ans_o1preview)+'\n')
        file.write("ans_o3mini: " + str(ans_o3mini) + '\n')
        file.write("ans_claude: " + str(ans_claude) + '\n')
        file.write("ans_qwen: " + str(ans_qwen) + '\n')
    print("over")

