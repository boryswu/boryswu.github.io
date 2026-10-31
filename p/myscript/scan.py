import os

# ---------------- 改这里--扫描文件夹下所有文件全名输出到txt ----------------
folder_path = r"F:"
output_txt = r"F:\filelist.txt"
# ----------------------------------------

with open(output_txt, "w", encoding="utf-8") as f:
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            f.write(full_path + "\n")

print(f"完成！文件列表已保存到：{output_txt}")
