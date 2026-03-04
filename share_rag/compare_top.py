import os

def read_number_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            number = int(file.read().strip())
            return number
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def compare_and_output_id(path1, path2, dir_id):
    num1 = read_number_from_file(path1)
    num2 = read_number_from_file(path2)

    if num1 is None or num2 is None:
        print("Error reading files for ID:", dir_id)
        return

    if num1 >= 1 and num2 >= 1:
        if num1 < num2:
            print(f"ID: {dir_id}")
    # elif num1 <= 1 and num2 <= 1:
    #     if num1 < num2:
    #         print(f"ID: {dir_id}")



def main():
    base_path = '/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test'
    directories = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

    for dir_id in directories:
        file_path1 = os.path.join(base_path, dir_id, 'gpt-4o-lyt/1/topN_first.txt')
        # file_path2 = os.path.join(base_path, dir_id, 'gpt-4o-lyt/1/topN_first.txt')
        file_path2 = os.path.join(base_path, dir_id, 'gpt-4o/1/topN_first.txt')
        if os.path.exists(file_path1) and os.path.exists(file_path2):
            compare_and_output_id(file_path1, file_path2, dir_id)
        else:
            print(f"Files missing in directory {dir_id}")

if __name__ == "__main__":
    main()
