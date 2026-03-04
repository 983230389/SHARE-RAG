import os
import json
import subprocess
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def get_alltests(root_dir):
    ids = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
    ]
    for id in ids:
        try:
            logging.info(f"处理ID {id}...")
            # 获取problem_id和测试用例total
            fetch_command = ['python3', 'tutorcode_api.py', 'fetch', str(id)]
            fetch_result = subprocess.run(fetch_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if fetch_result.returncode != 0:
                logging.error(f"获取ID {id} 时出错：{fetch_result.stderr}")
                continue
            fetch_data = json.loads(fetch_result.stdout)

            problemId = fetch_data.get('problemId')
            # 获取测试用例总数
            total_cases = fetch_data.get("judgeResult", {}).get("case_cnt", 0)

            logging.info(f"ID {id} 找到 {total_cases} 个测试用例.")

            for case_id in range(1, total_cases + 1):
                testcase_command = ['python3', 'tutorcode_api.py', 'testcase', str(problemId), str(case_id)]
                testcase_result = subprocess.run(testcase_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if testcase_result.returncode != 0:
                    logging.error(f"获取 promblemId {problemId} 的测试用例时出错： {testcase_result.stderr}")
                    continue
                testcase_data = json.loads(testcase_result.stdout)
                input_data = testcase_data.get('input')
                output_data = testcase_data.get('output')

                inputs_dir = os.path.join(root_dir, id, "inputs")
                outputs_dir = os.path.join(root_dir, id, "outputs")
                os.makedirs(inputs_dir, exist_ok=True)
                os.makedirs(outputs_dir, exist_ok=True)

                in_file_path = os.path.join(inputs_dir, f"{case_id}.in")
                out_file_path = os.path.join(outputs_dir, f"{case_id}.out")

                with open(in_file_path, 'w', encoding='utf-8') as f_in:
                    f_in.write(input_data)
                with open(out_file_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(output_data)

                logging.info(f"文件已生成: {in_file_path}, {out_file_path}")
        except Exception as e:
            logging.error(f"处理ID {id} 时出现异常：{e}")

def get_problem(root_dir):
    ids = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
    ]
    for id in ids:
        try:
            logging.info(f"处理ID {id}...")
            # 获取problem_id和测试用例total
            fetch_command = ['python3', 'tutorcode_api.py', 'fetch', str(id)]
            fetch_result = subprocess.run(fetch_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if fetch_result.returncode != 0:
                logging.error(f"获取ID {id} 时出错：{fetch_result.stderr}")
                continue
            fetch_data = json.loads(fetch_result.stdout)

            problemDescription = fetch_data.get('problemDescription')

            # 问题描述文件位置
            ProblemDes_path = os.path.join(root_dir, id, "ProblemDes")
            os.makedirs(ProblemDes_path, exist_ok=True)

            # 保存incorrectCode到对应的语言文件
            problem_file = os.path.join(ProblemDes_path, f"problem.txt")
            with open(problem_file, 'w', encoding='utf-8') as file:
                file.write(problemDescription)

                logging.info(f"文件已生成: {problem_file}")
        except Exception as e:
            logging.error(f"处理ID {id} 时出现异常：{e}")


if __name__ == "__main__":
    setup_logging()
    root_dir = "/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_all"
    get_alltests(root_dir)