import os
import shutil


def merge_folders(base_path):
    # 遍历 base_path 下的每个子目录
    for dir_name in os.listdir(base_path):
        current_dir = os.path.join(base_path, dir_name)
        print(current_dir)

        # 确保是目录而不是文件
        if os.path.isdir(current_dir):
            inputs_dir = os.path.join(current_dir, 'inputs')
            outputs_dir = os.path.join(current_dir, 'outputs')
            test_dir = os.path.join(current_dir, 'Test')

            # 如果inputs和outputs目录存在
            if os.path.exists(inputs_dir) and os.path.exists(outputs_dir):
                # 创建或确保Test目录存在
                os.makedirs(test_dir, exist_ok=True)

                # 将inputs和outputs目录中的文件移动到Test目录
                for item in os.listdir(inputs_dir):
                    src_path = os.path.join(inputs_dir, item)
                    dst_path = os.path.join(test_dir, item)
                    shutil.move(src_path, dst_path)

                for item in os.listdir(outputs_dir):
                    src_path = os.path.join(outputs_dir, item)
                    dst_path = os.path.join(test_dir, item)
                    shutil.move(src_path, dst_path)

                # 可选：删除inputs和outputs目录
                # shutil.rmtree(inputs_dir)
                # shutil.rmtree(outputs_dir)


if __name__ == '__main__':
    base_path = '/home/weijiqing/miniconda3/envs/llmfl/dataset/DebugBench_py'
    merge_folders(base_path)
