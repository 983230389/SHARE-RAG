import os
import re
import shutil

def count_single_line_number_files(base_dir):
    """
    Traverse through the directories and count files named 'fault_lines.txt'
    that contain exactly one line with a single number.
    """
    count = 0
    # Use os.walk to traverse directories
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if 'fault_lines.txt' in filenames:
            file_path = os.path.join(dirpath, 'fault_lines.txt')
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Check if the file has exactly one line and it is a single number
            if len(lines) == 1 and re.match(r'^\d+\s*$', lines[0]):
                count += 1
                print(f"File with single line number found: {file_path}")

    return count


def filter_single_fault_dirs(base_dir, target_dir):
    """
    Traverse through the directories in base_dir, find directories where
    'fault_lines.txt' contains exactly one line with a single number, and
    copy those directories to target_dir.
    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    count = 0
    # Use os.walk to traverse directories
    for dirpath, dirnames, filenames in os.walk(base_dir):
        if 'fault_lines.txt' in filenames:
            file_path = os.path.join(dirpath, 'fault_lines.txt')
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            # Check if the file has exactly one line and it is a single number
            if len(lines) > 1 and re.match(r'^\d+\s*$', lines[0]):
                count += 1
                # Locate the directory to be copied
                # Assuming the structure is /TutorCode_all/{id}/buggyCode/fault_lines.txt
                # Find the correct parent directory that represents the 'id'
                id_dir = dirpath
                while os.path.basename(os.path.dirname(id_dir)) != os.path.basename(base_dir):
                    id_dir = os.path.dirname(id_dir)  # Move up until you reach the directory directly under base_dir

                target_path = os.path.join(target_dir, os.path.basename(id_dir))

                # Copy the entire {id} directory if not already copied
                if not os.path.exists(target_path):
                    shutil.copytree(id_dir, target_path)
                    print(f"Copied {id_dir} to {target_path}")

    print(f"Total directories with exactly one fault line: {count}")


if __name__ == "__main__":
    base_directory = '/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test'
    count = count_single_line_number_files(base_directory)
    print(count)
    # target_directory = '/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test_multi'
    # filter_single_fault_dirs(base_directory, target_directory)
    # print(f"Total files with exactly one line number: {single_line_count}")
