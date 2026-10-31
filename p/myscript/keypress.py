import subprocess
import hashlib
from datetime import datetime
import getpass
import locale
import os
import tempfile
import shutil

# ===================== 配置区 =====================
# 请确认这个路径和你电脑7z的真实安装路径完全一致
SEVEN_ZIP = r"D:\7-Zip\7z.exe"
DIR_OASIS = "oasis"
DIR_TUNDRA = "tundra"

# ⚠️ 安全提示：7z 命令行只能把密码放在命令行参数中（-p密码），
# 密码在打包/校验进行期间可能被进程列表、任务管理器或日志系统看到。
# 请保证打包和校验在同一次运行内完成（本脚本已如此设计），
# 并避免在多人共用或受监控的机器上运行。
# ==================================================

# 7z 错误输出按系统本地编码解码，避免 gbk 硬编码导致乱码
ENCODING = locale.getpreferredencoding(False) or "utf-8"


def calc_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def folder_digest(root_dir: str) -> str:
    """对目录内所有文件的 (相对路径 + 内容哈希) 再取一次哈希。
    空目录也会得到一个确定性的摘要，不会像"数文件个数"那样假阳性。"""
    file_hash_list = []
    for root, _, files in os.walk(root_dir):
        for fn in files:
            full_path = os.path.join(root, fn)
            rel_path = os.path.relpath(full_path, root_dir).replace("\\", "/")
            file_hash_list.append(f"{rel_path}|{calc_sha256(full_path)}")
    file_hash_list.sort()
    return hashlib.sha256("\n".join(file_hash_list).encode("utf-8")).hexdigest()


def confirm_password(name: str) -> str:
    """强制二次输入并比对，防止手滑输错导致压缩包永久打不开。"""
    while True:
        p1 = getpass.getpass(f"请输入 {name} 密码：")
        p2 = getpass.getpass(f"请再次输入 {name} 密码确认：")
        if p1 == p2:
            return p1
        print("❌ 两次输入不一致，请重新输入")


def run_7z(args):
    """运行 7z，输出全部捕获；只有失败时才解码打印，避免刷屏和内存顾虑。"""
    return subprocess.run([SEVEN_ZIP] + args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)


def abort(output_dir: str, msg: str, result=None) -> bool:
    """统一失败处理：提示原因、打印 7z 输出、清理半成品目录。"""
    print(f"\n❌ {msg}")
    if result is not None:
        out = (result.stdout + result.stderr).decode(ENCODING, errors="replace")
        if out.strip():
            print("----- 7z 输出 -----")
            print(out)
            print("-------------------")
    shutil.rmtree(output_dir, ignore_errors=True)
    print(f"⚠️ 已清理半成品目录：{output_dir}")
    return False


def pack_and_verify(name: str, password: str, output_dir: str, time_str: str,
                    digest_source: str) -> str:
    """打包 → 7z t 完整性测试 → 解包到临时目录比对目录摘要。
    成功返回压缩包路径，失败返回空字符串。"""
    arc_path = os.path.join(output_dir, f"{name}-{time_str}.7z")

    # 1) 打包（-mhe=on 加密文件名）
    print(f"打包 {name.upper()} → {arc_path}")
    res = run_7z(["a", f"-p{password}", "-mhe=on", arc_path, name])
    if res.returncode != 0:
        return "" if abort(output_dir, f"{name.upper()} 打包失败", res) else ""

    # 2) 7z t：不解压到磁盘，自带 CRC 校验，快速发现损坏
    print(f"测试 {name.upper()} 压缩包完整性 (7z t)")
    res = run_7z(["t", f"-p{password}", arc_path])
    if res.returncode != 0:
        abort(output_dir, f"{name.upper()} 压缩包完整性测试失败", res)
        return ""

    # 3) 解包到临时目录，比对目录摘要（确保内容与源完全一致）
    #    临时目录里是全文明文，finally 保证尽量清理
    print(f"校验 {name.upper()} 内容与源目录摘要是否一致")
    temp_dir = tempfile.mkdtemp(prefix="7z_verify_")
    try:
        res = run_7z(["x", f"-p{password}", arc_path, f"-o{temp_dir}", "-y"])
        if res.returncode != 0:
            abort(output_dir, f"{name.upper()} 解包校验失败", res)
            return ""
        inner = os.path.join(temp_dir, name)
        if not os.path.isdir(inner) or folder_digest(inner) != digest_source:
            abort(output_dir,
                  f"{name.upper()} 内容与源目录摘要不一致，备份不可靠")
            return ""
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"✅ {name.upper()} 打包并校验通过")
    return arc_path


def main():
    print("=" * 50)
    print("步骤1：检查环境")

    if not os.path.isfile(SEVEN_ZIP):
        print(f"❌ 错误：找不到 7z 程序 → {SEVEN_ZIP}")
        print("请修改脚本里的 SEVEN_ZIP 为你电脑7z的真实安装路径")
        return
    print(f"✅ 7z 程序路径正常：{SEVEN_ZIP}")

    for d in (DIR_OASIS, DIR_TUNDRA):
        if not os.path.isdir(d):
            print(f"❌ 错误：找不到 {d} 文件夹")
            return
    print("✅ 源文件夹正常")

    time_str = datetime.now().strftime("%y%m%d-%H%M%S")
    date_short = datetime.now().strftime("%y%m%d")
    date_full = datetime.now().strftime("%Y-%m-%d")
    output_dir = time_str

    arc_oasis = os.path.join(output_dir, f"oasis-{time_str}.7z")
    arc_tundra = os.path.join(output_dir, f"tundra-{time_str}.7z")
    readme_path = os.path.join(output_dir, f"README-{date_short}.txt")

    print("\n步骤2：输入密码（二次确认，防止手滑锁死压缩包）")
    pass_oasis = confirm_password("OASIS 包")
    pass_tundra = confirm_password("TUNDRA 包")
    print("✅ 密码输入完成")

    # 密码确认无误后才创建输出目录，避免中断留下空目录垃圾
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ 输出目录：{output_dir}")

    print("\n步骤3：计算源目录内容摘要")
    digest_oasis = folder_digest(DIR_OASIS)
    digest_tundra = folder_digest(DIR_TUNDRA)
    print("✅ 摘要计算完成")

    print("\n步骤4：打包并校验 OASIS")
    arc_oasis = pack_and_verify("oasis", pass_oasis, output_dir, time_str, digest_oasis)
    if not arc_oasis:
        return

    print("\n步骤5：打包并校验 TUNDRA")
    arc_tundra = pack_and_verify("tundra", pass_tundra, output_dir, time_str, digest_tundra)
    if not arc_tundra:
        return

    print("\n步骤6：计算压缩包 SHA256")
    hash_oasis = calc_sha256(arc_oasis)
    hash_tundra = calc_sha256(arc_tundra)

    readme_content = f"""# {date_full}
# 目录内容摘要（对源目录计算，验证时可用相同方法复算比对）
oasis  目录摘要：{digest_oasis}
tundra 目录摘要：{digest_tundra}

# 7z压缩包SHA256
{hash_oasis}  oasis-{time_str}.7z
{hash_tundra}  tundra-{time_str}.7z
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("\n" + "=" * 50)
    print("🎉 全部备份完成！")
    print(f"输出目录：{output_dir}")
    print(f"校验文件：{readme_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 程序异常：{e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\n按回车键退出...")
        except EOFError:
            pass  # 非交互环境（计划任务/管道）下静默退出
