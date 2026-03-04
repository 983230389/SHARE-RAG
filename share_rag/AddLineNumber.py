import os


def add_line_numbers_to_code(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    numbered_lines = [f"{idx + 1} {line}" for idx, line in enumerate(lines)]
    return ''.join(numbered_lines)


def process_directory(base_dir):
    """
    Process each ID folder in the DebugBench_test directory to add line numbers to buggy codes.
    """
    extensions = ['.cpp', '.java', '.py']  # File extensions to handle

    for id_folder in os.listdir(base_dir):
        id_folder_path = os.path.join(base_dir, id_folder)
        if os.path.isdir(id_folder_path):
            buggy_folder_path = os.path.join(id_folder_path, "buggyCode")
            if os.path.exists(buggy_folder_path):
                # Get all code files from buggyCode folder
                buggy_files = [f for f in os.listdir(buggy_folder_path) if any(f.endswith(ext) for ext in extensions)]

                # Process each buggy code file
                for buggy_file in buggy_files:
                    buggy_file_path = os.path.join(buggy_folder_path, buggy_file)
                    # Add line numbers to the code
                    numbered_code = add_line_numbers_to_code(buggy_file_path)

                    # Save the numbered code to a new .txt file in the buggyCode folder
                    output_file_path = os.path.join(buggy_folder_path,
                                                    f"{os.path.splitext(buggy_file)[0]}_numbered.txt")
                    with open(output_file_path, 'w', encoding='utf-8') as output_file:
                        output_file.write(numbered_code)


if __name__ == "__main__":
    base_directory = '/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/DebugBench_Test'
    process_directory(base_directory)
