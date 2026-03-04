import os
import shutil

# 定义TutorCode文件夹的路径
tutor_code_path = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_Test'  # 替换成你的TutorCode文件夹路径

# 遍历TutorCode文件夹中的每个id文件夹
for id_folder in os.listdir(tutor_code_path):
    id_folder_path = os.path.join(tutor_code_path, id_folder)
    model_path = os.path.join(id_folder_path, "kimi-k2.5")
    # code = os.path.join(model_path, "buggy_code_temp.py")
    # 检查文件是否存在
    # if os.path.exists(model_path):
    #     shutil.rmtree(model_path)
    #     print(f"Deleted: {model_path}")
    # else:
    #     print(f"File not found, skipping: {model_path}")

    # 确保这是一个文件夹
    if os.path.isdir(model_path):
        gpt_folder_path = os.path.join(model_path)

        # 如果存在gpt-4o-mini文件夹，则删除
        if os.path.isdir(gpt_folder_path):

            shutil.rmtree(gpt_folder_path)
            print(f"已删除 {gpt_folder_path}")

    # model_path = os.path.join(id_folder_path, "Test")
    # # 确保这是一个文件夹
    # if os.path.isdir(model_path):
    #     shutil.rmtree(model_path)
    #     print(f"已删除 {model_path}")


