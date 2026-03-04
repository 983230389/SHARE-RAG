import json
import os.path
import re

from utils.utils1 import new_RAG
from utils.utils1 import RAG,new_RAG_dfg,new_RAG_cfg,new_RAG_ast
from utils.utils1 import final_RAG
from prompts import build_oneshot
from prompts import build_zeroshot
from prompts import build_newoneshot
import getTokenNumber
import ReadJson
import pickle
import SendPrompt
import AddLineNumberC
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.utils1 import adaptive_RAG, calculate_metrics # 引入新函数

def get_ground_truth_id(code_location, db):
    """
    根据代码路径获取对应题目的ID。
    Args:
        code_location (str): buggy code路径
        db (int): 1表示TutorCode, 其他表示DebugBench
    Returns:
        str: 题目ID (problemId / slug_id)
    """
    import json

    path_parts = os.path.normpath(code_location).split(os.sep)

    # 假设路径中倒数第二层是数据条目唯一ID
    # 例如 .../instance_id/buggyCode/... -> 取倒数第2个
    try:
        if 'buggyCode' in path_parts:
            data_id_index = path_parts.index('buggyCode') - 1
            data_id = path_parts[data_id_index]
        else:
            print("Error: Cannot extract data instance ID from path")
            return "UNKNOWN"
    except Exception as e:
        print(f"Failed to extract data_id from path: {e}")
        return "UNKNOWN"

    # 根据数据集查找题目ID
    if db == 1:  # TutorCode
        json_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode.json"
        key_data_id = "id"
        key_question_id = "problemId"
    else:  # DebugBench
        json_file = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_compilable.json"
        key_data_id = "instance_id"
        key_question_id = "slug_id"

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        # 查找匹配条目
        for item in data_list:
            if str(item.get(key_data_id)) == str(data_id):
                return str(item.get(key_question_id))
        # 没找到
        print(f"Warning: Cannot find ground truth question ID for data_id={data_id}")
        return "UNKNOWN"
    except Exception as e:
        print(f"Failed to load {json_file}: {e}")
        return "UNKNOWN"

def faultlocalization(prompt_location, code_location, res_path, db_path, files_loc, experiment_model, faultdata, type,
                      db):
    result_txt_location = os.path.join(res_path, "result.txt")
    result_json_location = os.path.join(res_path, "result.pkl")
    result_topN_first = os.path.join(res_path, "topN_first.txt")
    result_topN_multi = os.path.join(res_path, "topN_multi.txt")
    prompt_RAG_location = os.path.join(res_path, "prompt_RAG.txt")
    # result_topN_location = os.path.join(res_path, "topN.txt")
    result_metrics_location = os.path.join(res_path, "retrieval_metrics.txt")
    # topN已经计算过
    if os.path.exists(result_topN_first) or os.path.exists(result_topN_multi):
        return True

    # if os.path.exists(result_topN_location):
    #     print("这个topN已经计算过了，跳过他")
    #     return True

    # 读取提示词
    with open(prompt_location, 'r', encoding='utf-8') as file:
        prompt_model = file.read()

    rrf_res_text = []  # 用于构建 prompt 的文本列表
    retrieved_ids = []  # 用于计算指标的 ID 列表

    # RAG检索结果
    if type == 1:
        rrf_res_text, retrieved_ids = RAG(
            files_loc, db_path, res_path, code_location, db
        )
        prompt = build_oneshot(prompt_model, code_location, rrf_res_text)
    # elif type == 2:
    #     rrf_res = new_RAG(files_loc, db_path, res_path, code_location, db)
    #     prompt = build_oneshot(prompt_model, code_location, rrf_res)
    # elif type == 3:
    #     rrf_res = new_RAG_ast(files_loc, db_path, res_path, code_location, db)
    #     prompt = build_oneshot(prompt_model, code_location, rrf_res)
    # elif type == 4:
    #     rrf_res = new_RAG_cfg(files_loc, db_path, res_path, code_location, db)
    #     prompt = build_oneshot(prompt_model, code_location, rrf_res)
    # elif type == 5:
    #     rrf_res = new_RAG_dfg(files_loc, db_path, res_path, code_location, db)
    #     prompt = build_oneshot(prompt_model, code_location, rrf_res)
    elif type == 2:
        rrf_res_text, retrieved_ids = adaptive_RAG(
            files_loc, db_path, res_path, code_location, db, experiment_model
        )
        prompt = build_oneshot(prompt_model, code_location, rrf_res_text)
    else:
        prompt_location = "prompts/zero_prompt.txt"
        with open(prompt_location, 'r', encoding='utf-8') as file:
            prompt_model = file.read()
        prompt = build_zeroshot(prompt_model, code_location)
    # causes, fix = final_RAG(files_loc, db_path, res_path, code_location)
    # prompt = build_zeroshot(prompt_model, code_location)
    # prompt = build_newoneshot(prompt_model, code_location, causes, fix)

    if retrieved_ids:
        try:
            ground_truth_id = get_ground_truth_id(code_location, db)
            print(f"Ground Truth ID: {ground_truth_id}, Retrieved: {retrieved_ids}")

                # 2. 计算指标
            metrics = calculate_metrics(retrieved_ids, ground_truth_id)

                # 3. 保存指标
            with open(result_metrics_location, 'w') as f:
                f.write(json.dumps(metrics, indent=4))

        except Exception as e:
            print(f"Failed to calculate retrieval metrics: {e}")

    clear_gpu_cache()
    with open(prompt_RAG_location, 'w') as file:
        file.write(prompt)

    # print("prompt", prompt)

    # 读取提示词
    # with open(prompt_location, 'r', encoding='utf-8') as file:
    #     prompt = file.read()

    tokens = getTokenNumber.get_openai_token_len(prompt, model="text-davinci-001")
    max_tokens = 128000

    if tokens > max_tokens:
        print("超出token限制跳过," + code_location)
        return
        # 计算允许的最大长度，并截断多余的部分
        # truncated_prompt = prompt[:getTokenNumber.get_openai_token_len(prompt[:max_tokens], model="text-davinci-001")]
        # prompt = truncated_prompt  # 更新为截断后的prompt

    repeat_time = 5
    repeat_nowttime = repeat_time
    while repeat_nowttime > 0:
        repeat_nowttime -= 1

        try:
            # 发送请求
            print(" 第 " + str(repeat_time - repeat_nowttime) + " 次请求。" + code_location)
            result_txt = SendPrompt.send_prompt_openai_gpt(prompt, experiment_model)
        except Exception as e:
            print(" 请求发送异常", e)
            continue

        try:
            res_json_data = ReadJson.extract_json_regular(result_txt)
        except Exception as e:
            print("Json读取异常:", e)
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

            topN_first = 0  # 统计第一个错误的位置
            topN_multi = []  # 统计每个错误的位置
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
            print("数据存储成功 " + code_location)
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


def run_one_tutorcode(
        version_str,
        prompt_location,
        experiment_type,
        experiment_model,
        root_path,
        type,
        db
):
    try:
        print(f"[START] {version_str}")

        code_location = os.path.join(
            root_path, version_str, "buggyCode/buggy_code_numbered.txt"
        )
        faultline_location = os.path.join(
            root_path, version_str, "buggyCode/fault_lines.txt"
        )
        faultline_indexes = get_faultline(faultline_location)
        res_path = os.path.join(root_path, version_str, experiment_model, str(experiment_type))

        os.makedirs(res_path, exist_ok=True)

        files_loc = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/DebugBench_train.txt"
        db_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data"

        ok = faultlocalization(
            prompt_location,
            code_location,
            res_path,
            db_path,
            files_loc,
            experiment_model,
            faultline_indexes,
            type,
            db
        )

        print(f"[DONE] {version_str}, success={ok}")
        return version_str, ok

    except Exception as e:
        print(f"[ERROR] {version_str}: {e}")
        return version_str, False
    finally:
        clear_gpu_cache()


def clear_gpu_cache():
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except:
        pass


def test_Code(prompt_location, experiment_type, experiment_model, rangeIndex, type, db):
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_Test/"
    success_versions = []
    filter_data_path = "evaluate/DebugBench_Filter_Data.pkl"
    os.makedirs(os.path.dirname(filter_data_path), exist_ok=True)

    if os.path.exists(filter_data_path):
        with open(filter_data_path, "rb") as f:
            TutorCode_Filter_Data = pickle.load(f)
    else:
        TutorCode_Filter_Data = []

    if not TutorCode_Filter_Data:
        # 列出 root_path 下所有子文件夹名，并按数字排序
        TutorCode_Filter_Data = sorted(
            [d for d in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, d))],
            key=lambda x: int(x) if x.isdigit() else x
        )

    max_workers = 10  # ✅ 并发数，建议 4~8，Claude 很容易限流

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for version_str in TutorCode_Filter_Data[:rangeIndex]:
            futures.append(
                executor.submit(
                    run_one_tutorcode,
                    version_str,
                    prompt_location,
                    experiment_type,
                    experiment_model,
                    root_path,
                    type,
                    db
                )
            )

        for future in as_completed(futures):
            version_str, ok = future.result()
            if ok:
                success_versions.append(version_str)
            if not ok:
                print(f"[FAILED] {version_str}")
    # with open("evaluate/TutorCode_Filter_Data.pkl", "wb") as f:
    #     pickle.dump(success_versions, f)


def run_all(prompt_location):
    # 批量跑实验
    experiment_model = "nvidadeepseek-ai/deepseek-v3.2"
    for i in [1]:
        test_Code(prompt_location, 0, experiment_model, 9999, 0, 2)
        test_Code(prompt_location, 1, experiment_model, 9999, 1, 2)
        test_Code(prompt_location, 2, experiment_model, 9999, 2, 2)


    # for i in [2]:
    #     test_Code(prompt_location, i, experiment_model, 1239)


if __name__ == "__main__":
    prompt_location = "prompts/oneshot_prompt.txt"
    # prompt_location = "prompts/zero_prompt.txt"
    run_all(prompt_location)