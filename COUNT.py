import os
import ReadJson
import pickle
import re

def get_fault_data(faultline_location):
    with open(faultline_location, 'r', encoding='utf-8') as file:
        faultline = file.read()
    # 提取出第一个数字
    faultline_index = re.search('\d+', faultline).group(0)
    faultline_index = int(faultline_index)
    return faultline_index

def faultlocalization(experiment_index, experiment_model):

    root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/codeflaws/version/"

    with open("/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/Codeflaws_Filter_Data.pkl", "rb") as f:
        Codeflaws_Filter_Data = pickle.load(f)


    process_num = 0

    for versionInt in range(1, 1544):
        versionStr = "v" + str(versionInt)
        if versionStr not in Codeflaws_Filter_Data:
            continue

        process_num += 1

        print("正在跑Codeflaws上的 " + str(process_num) + " 个程序")
        faulte_data_path = os.path.join(root_path, versionStr, "test_data/defect_root/Fault_Record.txt")
        faultdata = get_fault_data(faulte_data_path)
        result_txt_location = os.path.join(root_path, versionStr,"test_data", experiment_model, str(experiment_index), "result.txt")
        response_topN_location = os.path.join(root_path, versionStr, "test_data", experiment_model, str(experiment_index), "topN.txt")


        with open(result_txt_location, 'r', encoding='utf-8') as file:
            response_txt = file.read()

        res_json_data = ReadJson.extract_json_regular(response_txt)

        if res_json_data is None:
            print(" json读取到空")
            continue
            # if repeat_time_this == 1:
            #     print("请求次数达到最大，跳过")
            # return False
        else:
            print(f"文件夹已创建")


            topN = 100
            faultlist = res_json_data['faultyLoc']
            for index in range(len(faultlist)):
                try:
                    if faultlist[index]['faultyLine'] == faultdata:
                        topN = index + 1
                        break
                except:
                    print("读取lineNumber失败")
            print("topN: ", topN)

            with open(response_topN_location, 'w') as file:
                    file.write(str(topN))

            print("数据存储成功 ")

def analyze_Codeflaws(experiment_index,experiment_model,rangeIndex,root_path):
    top1 = top2= top3 = top4 = top5 = top10 = topNull = 0
    istop1=istop5=istop10=0
    err_list = []

    top1_list = set()
    top5_list = set()
    top10_list = set()
    # root_path = "D:/私人资料/论文/大模型相关/大模型错误定位实证研究/data/codeflaws/version"
    Codeflaws_Filter_Data = []
    with open("/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/Codeflaws_Filter_Data.pkl", "rb") as f:
        Codeflaws_Filter_Data = pickle.load(f)

    process_num = 0

    for versionInt in range(1, 1544):
        istop1 = istop5 = istop10 = 0

        versionStr = "v" + str(versionInt);
        if versionStr not in Codeflaws_Filter_Data:
            print("跳过:"+versionStr)
            continue

        #在遍历达到一定个数后退出
        process_num +=1

        # print("processing: " + versionStr+" 第"+process_num+"个")
        if process_num>rangeIndex:
            break

        print("正在跑Codeflaws上的 " + experiment_model + " 实验： " + str(experiment_index) + " 的第 " + str(
            process_num) + " 个程序")

        print("processing: " + versionStr)
        # 数据目录
        # 输出的目录
        ans_path = os.path.join(root_path, versionStr, "test_data", experiment_model)
        ans_path = os.path.join(ans_path, str(experiment_index))
        top_N_path = os.path.join(ans_path, "topN.txt")

        topN_str = 0
        try:
            with open(top_N_path, 'r') as file:
                topN_str = file.read()
        except:
            print("读取topN失败:", top_N_path)

            # err_list.append(versionInt)

        topN_Index = int(topN_str)
        # 处理topn数据，并统计每一个程序是top几
        if topN_Index <= 1:
            top1 += 1
            # istop1=1
            top1_list.add(versionInt)
        if topN_Index <= 2:
            top2 += 1
        if topN_Index <= 3:
            top3 += 1
        if topN_Index <= 4:
            top4 += 1
        if topN_Index <= 5:
            top5 += 1
            # istop5=1
            top5_list.add(versionInt)
        if topN_Index <= 10:
            top10 += 1
            # istop10=1
            top10_list.add(versionInt)
        else:
            topNull += 1
    # ans = [top1_list, top5_list, top10_list]
    # return ans
    nums = [top1, top2,top3, top4,top5]
    return nums

if __name__=="__main__":
    faultlocalization(1, "llama-3.1-70b")

    # title = "Llama3_Codeflaws_new"
    # root_path = "/home/weijiqing/miniconda3/envs/llmfl/dataset/codeflaws/version"
    # ans_llama = analyze_Codeflaws(1, "llama-3.1-70b", 503, root_path)
    #
    # with open("./" + title + ".txt", 'w') as file:
    #     file.write("ans_llama: " + str(ans_llama) + '\n')
    # print("over")
