# tools/joern_utils.py
import subprocess
import tempfile
import os

def run_joern(code: str, language: str):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, f"test.{language}")
        with open(src, "w") as f:
            f.write(code)

        subprocess.run(["joern-parse", tmp], check=True)
        subprocess.run(["joern-export", "--repr", "cfg", "--out", f"{tmp}/cfg"])
        subprocess.run(["joern-export", "--repr", "ddg", "--out", f"{tmp}/dfg"])

        return f"{tmp}/cfg", f"{tmp}/dfg"
