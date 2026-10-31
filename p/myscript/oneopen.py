import subprocess

def main():
    while True:
        print("\n===== 软件启动选择器 =====")
        print("1. Clash")
        print("2. Snipaste")
        print("3. Outlook")
        print("0. 退出")

        print("\n请输入编号：")
        try:
            choice = int(input())
        except ValueError:
            print("输入不是数字！")
            input("按回车继续...")
            continue

        if choice == 0:
            print("退出程序")
            return
        elif choice == 1:
            # 微信示例路径（很多电脑是这个）
            path = r"D:\Clash\clash-verge.exe"
            subprocess.Popen(path)
        elif choice == 2:
            # Typora示例路径
            path = r"D:\Snipaste\Snipaste.exe"
            subprocess.Popen(path)
        elif choice == 3:
            # Outlook示例路径
            path = r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"
            subprocess.Popen(path)
        else:
            print("编号不存在！")
            input("按回车继续...")
            continue

        print("已经发起启动！")
        input("按回车返回菜单...")

if __name__ == "__main__":
    main()
