import os
import re

def remove_comments_and_empty_lines(code, extension):
    """Remove comments and empty lines based on file extension."""
    if extension in ['.cpp', '.java']:
        code = remove_cpp_java_comments(code)
    elif extension == '.py':
        code = remove_python_comments(code)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")

    return remove_empty_lines(code)

def remove_cpp_java_comments(code):
    """Remove C++/Java comments."""
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code

def remove_python_comments(code):
    """Remove Python comments."""
    code = re.sub(r'#.*', '', code)
    return code

def remove_empty_lines(code):
    """Remove empty lines."""
    lines = code.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def process_files(base_dir):
    """Process all files within the given base directory."""
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file in ['buggy_code.py', 'true_code.py', 'buggy_code.cpp', 'true_code.cpp', 'buggy_code.java', 'true_code.java']:
                full_path = os.path.join(root, file)
                extension = os.path.splitext(file)[1]
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                cleaned_code = remove_comments_and_empty_lines(code, extension)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_code)

if __name__ == "__main__":
    base_directory = "/home/weijiqing/miniconda3/envs/llmfl/dataset/TutorCode_test"
    process_files(base_directory)
