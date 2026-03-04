# 计算 scores.txt 中数字的平均值
try:
    with open('/home/weijiqing/miniconda3/envs/llmfl/LLMFL/evaluate/BLEURT_SCORE_AVG/score_TOP1_llama3.txt', 'r') as file:
        lines = file.readlines()

    # 转换并过滤无效数据
    scores = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                scores.append(float(line))
            except ValueError:
                print(f"警告：跳过无效行 '{line}'")

    if not scores:
        print("错误：文件中无有效数字")
    else:
        total = sum(scores)
        count = len(scores)
        average = total / count
        # maximum = max(scores)
        # print(f"有效数字个数: {count}")
        # print(f"总和: {total:.4f}")
        print(f"平均值: {average:.4f}")
        # print(f"最大值: {maximum:.4f}")

except FileNotFoundError:
    print("错误：文件 'scores.txt' 未找到")
except Exception as e:
    print(f"未知错误: {e}")