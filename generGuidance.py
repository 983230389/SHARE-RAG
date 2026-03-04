import os
import json

json_path = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/Data/TutorCode.json"
test_root = "/home/weijiqing/miniconda3/envs/llmfl/LLMFL/dataset/TutorCode_Test"

with open(json_path, "r", encoding="utf-8") as f:
    tutor_data = json.load(f)

print("JSON type:", type(tutor_data))

# 如果是 dict，取消下面这行注释
# tutor_data = tutor_data["data"]

print("Total JSON items:", len(tutor_data))
print("Existing subdirs sample:", os.listdir(test_root)[:10])

written = 0
skipped = 0

for item in tutor_data:
    tutor_id = str(item.get("id"))
    guidance = item.get("tutorGuidance", "")

    if not tutor_id or not guidance.strip():
        skipped += 1
        continue

    target_dir = os.path.join(test_root, tutor_id)

    if not os.path.isdir(target_dir):
        skipped += 1
        continue

    out_path = os.path.join(target_dir, "tutorGuidance.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(guidance)

    written += 1
    print(f"[OK] {tutor_id}")

print(f"\nDone. Written: {written}, Skipped: {skipped}")
