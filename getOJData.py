import json
import shutil

# import pandas as pandas
import pymysql
import os


def solve(problem_id, data_list):
    db = None
    try:
        db = pymysql.connect(host="222.199.230.149", port=3306, user="root", password="BuctSql@405", database="jol")

        # 获取问题描述
        query = " select description, sample_input, sample_output from problem where problem_id = %s"
        cursor = db.cursor()
        cursor.execute(query, (problem_id))
        db.commit()
        problem_info = cursor.fetchone()
        cursor.close()

        if not problem_info:
            print(f"未找到问题ID为 {problem_id} 的问题信息")
            return

        description, sample_input, sample_output = problem_info

        # 获取同时有正确和错误提交的用户列表
        query = " select distinct s.user_id from solution s where s.problem_id = " + problem_id + " and s.language = 0 group by s.user_id having sum(case when s.result = 4 then 1 else 0 end) > 0 and sum(case when s.result = 6 then 1 else 0 end) > 0"
        cursor = db.cursor()
        cursor.execute(query)
        db.commit()
        users = cursor.fetchall()
        cursor.close()

        if not users:
            print(f"问题ID为 {problem_id} 没有同时提交过正确和错误代码的用户")
            return

        # data_list = []
        for user in users:
            user_id = user[0]
            # 获取该用户提交的正确代码
            query = " select sc.source from solution s join source_code sc on s.solution_id = sc.solution_id where s.user_id = '" + user_id + "' and   s.problem_id = " + problem_id + " and s.result = 4 and s.language = 0 ORDER BY s.judgetime desc limit 1"
            cursor = db.cursor()
            cursor.execute(query)
            db.commit()
            ac_code = cursor.fetchone()
            cursor.close()

            # 获取该用户提交的错误代码
            query = " select sc.source from solution s join source_code sc on s.solution_id = sc.solution_id where s.user_id = '" + user_id + "' and  s.problem_id = " + problem_id + " and s.result = 6 and s.language = 0 ORDER BY s.judgetime desc "
            cursor = db.cursor()
            cursor.execute(query)
            db.commit()
            wa_code = cursor.fetchone()
            cursor.close()

            if ac_code and wa_code:
                acCode = preprocess(ac_code[0])
                waCode = preprocess(wa_code[0])

                data = {
                    "id": user_id, "problem": problem_id, "description": description, "sample_input": sample_input, "sample_output": sample_output, "wa_code": waCode, "ac_code": acCode,
                }

                data_list.append(data)

        if not data_list:
            print(f"问题ID为 {problem_id} 没有符合条件的数据")
            return

        # txt_file_path = os.path.join(DataPath, f"{problem_id}.txt")
        # json_file_path = os.path.join(DataPath, f"{problem_id}.json")

        # 数据写入txt 文件
        # with open(txt_file_path, "w", encoding="utf-8") as txt_file:
        #     for index, data in enumerate(data_list):
        #         # 将数据转换为 JSON 字符串，不添加缩进和空格
        #         json_str = json.dumps(
        #             data,
        #             ensure_ascii=False,
        #             separators=(',', ':')
        #         )
        #         # 写入文件
        #         txt_file.write(json_str)
        #         # 如果不是最后一个对象，添加逗号和换行符
        #         if index < len(data_list) - 1:
        #             txt_file.write(',\n')
        #         else:
        #             txt_file.write('\n')
        #
        # print(f"已生成 TXT 文件：{txt_file_path}")

        # 数据写入json文件
        # with open(json_file_path, "w", encoding="utf-8") as f:
        #     json.dump(data_list, f, ensure_ascii=False, indent=4)
        # print(f"已生成 JSON 文件：{json_file_path}")


    except Exception as e:
        print("出现错误: " + str(e))
    finally:
        if db != None:
            db.close()

def preprocess(code):
    lines = code.splitlines()
    processed_lines = []
    indent_level = 0
    for line in lines:
        # 移除从 // 开始的注释部分
        comment_index = line.find("//")
        if comment_index != -1:
            line = line[:comment_index]
        # 去掉前后空格
        line = line.strip()
        # 检查缩进级别变化
        if line.endswith('{'):
            processed_lines.append('    ' * indent_level + line)
            indent_level += 1
        elif line.startswith('}'):
            indent_level -= 1
            processed_lines.append('    ' * indent_level + line)
        else:
            processed_lines.append('    ' * indent_level + line)

    # 添加行号
    numbered_lines = [f"{i + 1} {line}" for i, line in enumerate(processed_lines)]
    return '\n'.join(numbered_lines)


def main():
    ids = []
    with open("./pid.txt", "r", encoding="utf-8") as f:
        ids = [id.strip() for id in f.readlines()]

    clean()
    data_list = []

    for id in ids:
        solve(id, data_list)

    # 将所有数据写入到一个文件
    with open(output_file_path, "w", encoding="utf-8") as file:
        for index, data in enumerate(data_list):
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            file.write(json_str)
            if index < len(data_list) - 1:
                file.write(',\n')
            else:
                file.write('\n')
    print(f"已生成汇总数据文件：{output_file_path}")

# 创建保存路径
basePath = os.getcwd()
DataPath = os.path.join(basePath, "Data")
os.makedirs(DataPath, exist_ok=True)
output_file_path = os.path.join(DataPath, "BuctOJ.txt")  # 设定一个固定的输出文件

def clean():
    if os.path.exists(DataPath):
        shutil.rmtree(DataPath)
    os.makedirs(DataPath)

# ids = []
# with open("./pid.txt", "r", encoding="utf-8") as f:
#     ids = f.readlines()

# for id in ids:
#     id = id.strip().replace("\n", "")
#     main(id)

if __name__ == "__main__":
    main()
