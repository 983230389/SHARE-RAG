import os.path
import re

from utils.utils1 import RAG
from utils.utils1 import final_RAG
from prompts import build_oneshot
from prompts import build_newoneshot
import getTokenNumber
import ReadJson
import pickle
import SendPrompt
import AddLineNumberC


def faultlocalization(prompt_location, code_location, res_path, db_path, files_loc, experiment_model, faultdata):
    result_txt_location = os.path.join(res_path, "result.txt")
    result_json_location = os.path.join(res_path, "result.pkl")
    result_topN_first = os.path.join(res_path, "topN_first.txt")
    result_topN_multi = os.path.join(res_path, "topN_multi.txt")
    prompt_RAG_location = os.path.join(res_path, "prompt_RAG.txt")
    # result_topN_location = os.path.join(res_path, "topN.txt")

    # topN已经计算过
    if os.path.exists(result_topN_first) or os.path.exists(result_topN_multi):
        return True

    # if os.path.exists(result_topN_location):
    #     print("这个topN已经计算过了，跳过他")
    #     return True

    # 读取提示词
    with open(prompt_location, 'r', encoding='utf-8') as file:
        oneshot_prompt = file.read()

    # RAG检索结果
    rrf_res = RAG(files_loc, db_path, res_path, code_location)
    # causes, fix = final_RAG(files_loc, db_path, res_path, code_location)
    prompt = build_oneshot(oneshot_prompt, code_location, rrf_res)

    with open(prompt_RAG_location, 'w') as file:
        file.write(prompt)

    # print("prompt", prompt)

    # 读取提示词
    # with open(prompt_location, 'r', encoding='utf-8') as file:
    #     prompt = file.read()

    tokens = getTokenNumber.get_openai_token_len(prompt, model="text-davinci-001")
    max_tokens = 128000

    if tokens > max_tokens:
        print("超出token限制跳过,"+code_location)
        # 计算允许的最大长度，并截断多余的部分
        truncated_prompt = prompt[:getTokenNumber.get_openai_token_len(prompt[:max_tokens], model="text-davinci-001")]
        prompt = truncated_prompt  # 更新为截断后的prompt


    repeat_time = 5
    repeat_nowttime = repeat_time
    while repeat_nowttime > 0:
        repeat_nowttime -= 1

        try:
            # 发送请求
            print(" 第 " + str(repeat_time - repeat_nowttime) + " 次请求。" + code_location)
            result_txt = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
        except:
            print(" 请求发送异常" + code_location)
            continue

        try:
            res_json_data = ReadJson.extract_json_regular(result_txt)
        except:
            print(" Json读取异常" + code_location)
            continue

        if res_json_data is None:
            print(code_location + " json读取到空")
            continue
            # if repeat_time_this == 1:
            #     print("请求次数达到最大，跳过")
            # return False
        else:
            if not os.path.exists(res_path):
                # 如果文件夹不存在，则创建它
                os.makedirs(res_path)
                print(f"文件夹 '{res_path}' 已创建")

            # 读取json信息

            # 判断是否替换
            ReplaceIndex = True

            topN = 0
            # faultlist = res_json_data['faultyLoc']
            # for index in range(len(faultlist)):
            #     try:
            #         if faultlist[index]['faultyLine']==faultdata:
            #             topN = index + 1
            #             break
            #     except:
            #         print("读取faultyLine失败")
            # print("topN: ", topN)

            faultlist = res_json_data['faultyLoc']

            topN_first = 0 # 统计第一个错误的位置
            topN_multi = [] # 统计每个错误的位置
            fault_seen = set()  # 用于记录已出现过的 fault

            for index in range(len(faultlist)):
                fault_line = faultlist[index]['faultyLine']
                for fault in faultdata:
                    if fault_line == fault:
                        if topN_first == 0:
                            topN_first = index + 1
                            break

            # 遍历所有 faultdata
            for fault in faultdata:
                matched = False  # 标记是否找到匹配的 faultyLine
                for index in range(len(faultlist)):
                    try:
                        # 读取 faultlist 中的 faultyLine
                        fault_line = faultlist[index]['faultyLine']

                        if fault == fault_line:
                            # 如果该 fault 还没有在 topN_multi 中记录过位置，记录它的位置
                            if fault not in fault_seen:
                                topN_multi.append(index + 1)  # 记录位置到 topN_multi
                                fault_seen.add(fault)  # 标记该 fault 为已记录
                            matched = True
                            break  # 找到第一个匹配就跳出循环
                    except:
                        print("读取faultyLine失败")

                # 如果没有匹配到任何 faultyLine，将 topN_multi 中对应的值设为 0
                if not matched:
                    topN_multi.append(0)

            print("topN_first", topN_first)
            print("topN_multi", topN_multi)

            if ReplaceIndex == True:
                with open(result_txt_location, 'w') as file:
                    file.write(result_txt)
                with open(result_json_location, 'wb') as file:
                    pickle.dump(res_json_data, file)

                if topN_first >= 0:
                    with open(result_topN_first, 'w') as file:
                        file.write(str(topN_first))
                if topN_multi:
                    with open(result_topN_multi, 'w') as file:
                        file.write(str(topN_multi))
                # with open(result_topN_location, 'w') as file:
                #     file.write(str(topN))
                # 跳出循环
            print("数据存储成功 "+code_location)
            return True
            break

    return False

# 获得错误位置行号
def get_fault_data(faultline_location):
    with open(faultline_location, 'r', encoding='utf-8') as file:
        faultline = file.read()
    # 提取出第一个数字
    faultline_index = re.search('\d+', faultline).group(0)
    faultline_index = [int(faultline_index)]
    return faultline_index


def get_faultline(faultline_location):
    with open(faultline_location, 'r', encoding='utf-8') as file:
        # 读取所有行并去除每行末尾的换行符
        faultline_indexes = [int(line.strip()) for line in file.readlines() if line.strip().isdigit()]
        print("fault", faultline_indexes)
    return faultline_indexes


def test_DebugBench(prompt_location, experiment_index, experiment_model, rangeIndex):
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_test/"
    with open("evaluate/DebugBench_Filter_Data.pkl", "rb") as f:
        DebugBench_Filter_Data = pickle.load(f)
    # DebugBench_Filter_Data = []

    existing_versions = []

    for version in range(1, rangeIndex):
        # version_str = "v" + str(version)
        version_str = str(version)
        # print("processing: "+ version_str)
        version_path = os.path.join(root_path, version_str)
        if os.path.exists(version_path):
            existing_versions.append(version_str)

    if not existing_versions:
        print("没有有效的版本")
        return

    for version_str in DebugBench_Filter_Data:
        print(f"正在处理版本: {version_str}")
        code_location = os.path.join(root_path, version_str, "buggyCode/buggy_code_numbered.txt")
        faultline_location = os.path.join(root_path, version_str, "buggyCode/fault_lines.txt")
        faultline_indexes = get_faultline(faultline_location)

        res_path = os.path.join(root_path, version_str, experiment_model)
        res_path = os.path.join(res_path, str(experiment_index))

        if not os.path.exists(res_path):
            # 如果文件夹不存在，则创建
            os.makedirs(res_path)
            print(f"文件夹 '{res_path}' 已创建")

        # 语料库位置
        files_loc = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_train.txt"
        # 向量存储位置
        db_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"

        isok = faultlocalization(prompt_location, code_location, res_path, db_path, files_loc, experiment_model, faultline_indexes)

        # if isok is True:
        #     DebugBench_Filter_Data.append(version_str)
        # else:
        #     print(code_location + "不可用")
        #     continue

        print("这是第" + str(len(DebugBench_Filter_Data)) + "个")
        # with open('evaluate/DebugBench_Filter_Data.pkl', 'wb') as file:
        #     pickle.dump(DebugBench_Filter_Data, file)


def run_DebugBench(prompt_location, experiment_index, experiment_model, rangeIndex):
    print("当前工作目录:", os.getcwd())
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_test/"
    with open("evaluate/DebugBench_Filter_Data.pkl", "rb") as f:
        DebugBench_Filter_Data = pickle.load(f)

    process_num = 0

    for version in range(1, 590):
        version_str = str(version)
        if version_str not in DebugBench_Filter_Data:
            print("跳过:"+version_str)
            continue

        process_num += 1

        if process_num > rangeIndex:
            break

        print("正在跑DebugBench上的 " + experiment_model + " 实验： " + str(experiment_index) + " 的第 " + str(
            process_num) + " 个程序")

        code_location = os.path.join(root_path, version_str, "buggyCode/buggy_code_numbered.txt")
        faultline_location = os.path.join(root_path, version_str, "buggyCode/fault_lines.txt")
        faultline_indexes = get_faultline(faultline_location)

        res_path = os.path.join(root_path, version_str, "test_data", experiment_model)
        res_path = os.path.join(res_path, str(experiment_index))

        if not os.path.exists(res_path):
            # 如果文件夹不存在，则创建
            os.makedirs(res_path)
            print(f"文件夹 '{res_path}' 已创建")

        # 语料库位置
        files_loc = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_train.txt"
        # 向量存储位置
        db_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"

        isok = faultlocalization(prompt_location, code_location, res_path, db_path, files_loc, experiment_model,
                                 faultline_indexes)


def test_TutorCode(prompt_location, experiment_index, experiment_model, rangeIndex):
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test/"
    with open("evaluate/TutorCode_Filter_Data.pkl", "rb") as f:
        TutorCode_Filter_Data = pickle.load(f)
    # TutorCode_Filter_Data = []

    existing_versions = []

    for version in range(1, rangeIndex):
        # version_str = "v" + str(version)
        version_str = str(version)
        # print("processing: "+ version_str)
        version_path = os.path.join(root_path, version_str)
        if os.path.exists(version_path):
            existing_versions.append(version_str)

    if not existing_versions:
        print("没有有效的版本")
        return

    for version_str in TutorCode_Filter_Data:
        print(f"正在处理版本: {version_str}")
        code_location = os.path.join(root_path, version_str, "buggyCode/buggy_code_numbered.txt")
        faultline_location = os.path.join(root_path, version_str, "buggyCode/fault_lines.txt")
        faultline_indexes = get_faultline(faultline_location)

        res_path = os.path.join(root_path, version_str, experiment_model)
        res_path = os.path.join(res_path, str(experiment_index))

        if not os.path.exists(res_path):
            # 如果文件夹不存在，则创建
            os.makedirs(res_path)
            print(f"文件夹 '{res_path}' 已创建")

        # 语料库位置
        files_loc = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode_train.txt"
        # 向量存储位置
        db_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"

        isok = faultlocalization(prompt_location, code_location, res_path, db_path, files_loc, experiment_model, faultline_indexes)

        # if isok is True:
        #     TutorCode_Filter_Data.append(version_str)
        # else:
        #     print(code_location + "不可用")
        #     continue

        # print("这是第" + str(len(TutorCode_Filter_Data)) + "个")
        # with open('evaluate/TutorCode_Filter_Data.pkl', 'wb') as file:
        #     pickle.dump(TutorCode_Filter_Data, file)

def test_CodeFlaws(prompt_location, experiment_index, experiment_model, rangeIndex):
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/codeflaws/version/"
    Codeflaws_Filter_Data = []

    for versionInt in range(1, rangeIndex):
        versionStr = "v" + str(versionInt)
        print(f"正在处理版本: {versionStr}")

        # 给代码增加行号
        AddLineNumberC.process_code(os.path.join(root_path, versionStr, "test_data/defect_root/source"), "tcas.c")
        code_location = os.path.join(root_path,versionStr,"test_data/defect_root/source/tcas.c_indexed.txt")
        faulte_data_path = os.path.join(root_path, versionStr, "test_data/defect_root/Fault_Record.txt")
        faulte_data_index = get_fault_data(faulte_data_path)

        # 输出的目录
        ans_path = os.path.join(root_path, versionStr, "test_data", experiment_model)
        ans_path = os.path.join(ans_path, str(experiment_index))

        if not os.path.exists(ans_path):
            # 如果文件夹不存在，则创建
            os.makedirs(ans_path)
            print(f"文件夹 '{ans_path}' 已创建")

        # 语料库位置
        files_loc = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/train.txt"
        # 向量存储位置
        db_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"

        isok = faultlocalization(prompt_location, code_location, ans_path, db_path, files_loc, experiment_model, faulte_data_index)

        if isok is True:
            Codeflaws_Filter_Data.append(versionStr)
        else:
            print(code_location + "不可用")
            continue

        print("这是第" + str(len(Codeflaws_Filter_Data)) + "个")
        with open('evaluate/Codeflaws_Filter_Data.pkl', 'wb') as file:
            pickle.dump(Codeflaws_Filter_Data, file)

def run_all(prompt_location):
    # 批量跑实验
    experiment_model = "qwen-turbo"
    for i in [2]:
        test_TutorCode(prompt_location, i, experiment_model, 1239)

if __name__=="__main__":
    prompt_location = "prompts/oneshot_prompt.txt"
    run_all(prompt_location)