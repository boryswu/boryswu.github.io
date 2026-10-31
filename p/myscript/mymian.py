import os
import subprocess
import sys

# 脚本目录
SCRIPT_DIR = r"E:\Script"

def main():
    # 扫描目录下py文件，排除__init__.py
    file_list = []
    if os.path.isdir(SCRIPT_DIR):
        for fname in sorted(os.listdir(SCRIPT_DIR)):
            if fname.lower().endswith(".py") and fname != "__init__.py":
                file_list.append(fname)
    else:
        print(f"目录不存在：{SCRIPT_DIR}")
        input("按回车退出...")
        return

    if len(file_list) == 0:
        print("文件夹里没有找到py脚本")
        input("按回车退出...")
        return

    print("===== 脚本列表 =====")
    for idx, name in enumerate(file_list, start=1):
        print(f"{idx}. {name}")
    print("0. 退出程序")

    print("\n请输入要运行的脚本编号：")
    try:
        select = int(input())
        if select == 0:
            print("已退出")
            return
        if select < 1 or select > len(file_list):
            print("编号超出范围！")
            input("按回车退出...")
            return
    except ValueError:
        print("输入不是数字！")
        input("按回车退出...")
        return

    selected_file = file_list[select - 1]
    full_path = os.path.join(SCRIPT_DIR, selected_file)
    print(f"准备运行：{full_path}")

    # Windows新开控制台运行脚本
    if sys.platform == "win32":
        subprocess.Popen(
            [sys.executable, full_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        subprocess.Popen([sys.executable, full_path])

if __name__ == "__main__":
    main()
