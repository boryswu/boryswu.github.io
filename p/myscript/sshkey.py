import subprocess
import sys
import os

def run_cmd(cmd: str, capture=False):
    """shell=True 走 cmd.exe；需要 PowerShell 的命令显式加 powershell 前缀"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return None
            return result.stdout
        subprocess.run(cmd, shell=True, check=True, timeout=120)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"命令执行失败：{e}")
        return None

def check_agent_running():
    # 用 sc query 而不是 Get-Service（cmd 不认 PowerShell 命令）
    out = run_cmd('sc query ssh-agent', capture=True)
    return bool(out and "RUNNING" in out)

def start_agent():
    print("=== 启动 ssh-agent ===")
    if check_agent_running():
        print("ssh-agent 已经在运行，跳过启动")
        return
    # 服务默认是 Disabled，先改启动类型，避免 Start-Service 报 1058
    run_cmd('powershell -Command "Set-Service ssh-agent -StartupType Manual"')
    run_cmd('powershell -Command "Start-Service ssh-agent"')

def load_key(key_path: str):
    if not os.path.exists(key_path):
        print(f"私钥不存在：{key_path}")
        return
    print(f"=== 加载私钥：{key_path} ===")
    print("（passphrase 提示会在本窗口中显示，直接输入即可，不回显）")
    run_cmd(f'ssh-add "{key_path}"')

def list_keys():
    print("=== 当前已加载密钥列表 ===")
    result = subprocess.run("ssh-add -l", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("没有加载任何密钥")

def clear_keys():
    print("=== 清空agent内密钥 ===")
    # Windows 服务的 agent 对 ssh-add -D 支持不好，改用逐个删除
    result = subprocess.run("ssh-add -l", shell=True, capture_output=True, text=True)
    keys = []
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            parts = line.split()
            # 输出格式：位数 指纹 注释(密钥路径) (类型)，取第3列即密钥路径
            if len(parts) >= 3:
                keys.append(parts[2])
    if not keys:
        print("agent 中没有密钥")
        return
    run_cmd("ssh-add -d " + " ".join(f'"{k}"' for k in keys))
    # 验证是否真的清空了
    list_keys()

def stop_agent():
    print("=== 停止 ssh-agent ===")
    run_cmd('powershell -Command "Stop-Service ssh-agent"')

def main():
    private_key = os.path.expanduser(r"~\.ssh\id_ed25519")
    # private_key = os.path.expanduser(r"~\.ssh\id_rsa")

    while True:
        print()
        print("请选择功能：")
        print("1 - 启动agent + 加载密钥（日常提交代码用）")
        print("2 - 查看已经加载的密钥")
        print("3 - 清空密钥（用完一定要清！）")
        print("4 - 清空密钥 + 停止agent")
        print("0 - 退出")
        choice = input("输入数字：").strip()

        if choice == "1":
            start_agent()
            load_key(private_key)
            list_keys()
        elif choice == "2":
            list_keys()
        elif choice == "3":
            clear_keys()
        elif choice == "4":
            clear_keys()
            stop_agent()
        elif choice == "0":
            print("再见")
            break
        else:
            print("输入错误")

        # 执行完一个功能后停一下，按回车回到菜单
        input("按回车键返回菜单...")

if __name__ == "__main__":
    main()
