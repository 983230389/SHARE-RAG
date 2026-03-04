import os
import pickle

def analyze_sbfl_mbfll(formula, method, root_path):
    # root_path = "D:/私人资料/论文/大模型相关/大模型错误定位实证研究/data/codeflaws/results"
    data_path = os.path.join(root_path,formula+method+".txt");
    if not os.path.exists(data_path):
        raise PathNotExistError(f"The path '{data_path}' does not exist. Program terminated.")
    data = []
    with open(data_path, 'r') as file:
        for line in file:
            row = [int(x) for x in line.split()]
            data.append(row)
    top1 = top2 = top3 = top4 = top5 = top10 = topNull = 0
    for version in range(0, 197):
        row_data = data[version]
        topN_Index=100
        for n in range(0,10):
            if row_data[n]>0:
                topN_Index=n+1
                break;
        if topN_Index <= 1:
            top1 += 1
            # istop1=1
            # top1_list.add(versionInt)
        if topN_Index <= 2:
            top2 += 1
        if topN_Index <= 3:
            top3 += 1
        if topN_Index <= 4:
            top4 += 1
        if topN_Index <= 5:
            top5 += 1
            # istop5=1
            # top5_list.add(versionInt)
        if topN_Index <= 10:
            top10 += 1
            # istop10=1
            # top10_list.add(versionInt)
        else:
            topNull += 1

    nums = [top1, top2, top3, top4, top5, top10]
    return nums


class PathNotExistError(Exception):
    pass

if __name__ == "__main__":
    # model_name="chatGlm3"
    # gpt-4
    # experiment_model = "gpt-3.5-turbo"

    # 画codeflaws上的
    title = "SBFL"
    root_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/OJexperiment_codeflaws"
    # dstarMBFL = analyze_sbfl_mbfll("dstar", "MBFL", root_path)
    dstarSBFL = analyze_sbfl_mbfll("dstar", "SBFL", root_path)
    # ochiMBFL = analyze_sbfl_mbfll("ochi", "MBFL", root_path)
    ochiSBFL = analyze_sbfl_mbfll("ochi", "SBFL", root_path)
    # op2MBFL = analyze_sbfl_mbfll("op", "MBFL", root_path)
    op2SBFL = analyze_sbfl_mbfll("op", "SBFL", root_path)

    with open("./"+title+".txt", 'w') as file:
        file.write("name:  top1 top2 top3 top4 top5 top10" + '\n')
        # file.write("dstarMBFL: "+str(dstarMBFL)+'\n')
        file.write("dstarSBFL: " + str(dstarSBFL)+'\n')
        # file.write("ochiMBFL: " + str(ochiMBFL)+'\n')
        file.write("ochiSBFL: " + str(ochiSBFL)+'\n')
        # file.write("opMBFL: " + str(op2MBFL) + '\n')
        file.write("opSBFL: " + str(op2SBFL) + '\n')

    # 画codeflaws上的
    # title = "SBFL_MBFL_in_Condefects_5"
    # root_path = "D:/私人资料/论文/大模型相关/大模型错误定位实证研究/data/ConDefects-main/results"
    # dstarMBFL = analyze_sbfl_mbfll("dstar", "MBFL", root_path)
    # dstarSBFL = analyze_sbfl_mbfll("dstar", "SBFL", root_path)
    # ochiMBFL = analyze_sbfl_mbfll("ochi", "MBFL", root_path)
    # ochiSBFL = analyze_sbfl_mbfll("ochi", "SBFL", root_path)
    # op2MBFL = analyze_sbfl_mbfll("op", "MBFL", root_path)
    # op2SBFL = analyze_sbfl_mbfll("op", "SBFL", root_path)
    #
    # with open("./"+title+".txt", 'w') as file:
    #     file.write("name:  top1 top2 top3 top4 top5 top10" + '\n')
    #     file.write("dstarMBFL: "+str(dstarMBFL)+'\n')
    #     file.write("dstarSBFL: " + str(dstarSBFL)+'\n')
    #     file.write("ochiMBFL: " + str(ochiMBFL)+'\n')
    #     file.write("ochiSBFL: " + str(ochiSBFL)+'\n')
    #     file.write("op2MBFL: " + str(op2MBFL) + '\n')
    #     file.write("op2SBFL: " + str(op2SBFL) + '\n')




    print("over")



