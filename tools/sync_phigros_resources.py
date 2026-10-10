"""从 GitHub 仓库 7aGiven/Phigros_Resource 同步资源到本地(覆盖同名文件)。

功能:
  1. info 分支的 info.tsv / difficulty.tsv → assets/data/(覆盖)
  2. illustration 分支全部内容 → assets/images/illustrations/(覆盖同名,不删除多余文件)

用法:
  python tools/sync_phigros_resources.py            # 任意目录运行均可(路径按脚本自身定位)
  python tools/sync_phigros_resources.py --app-naming
      # 曲绘额外按 PhiFilterTool 的命名习惯存一份: "组合名称.曲师.png" → "组合名称.png"
      # (应用加载曲绘用的是 assets/images/illustrations/{组合名称}.png)
  # 或双击 tools/sync_phigros_resources.bat

说明:
  - illustration 分支通过 GitHub 的分支 ZIP 下载(单请求,无需 git,不受 API 限流),
    需要磁盘空闲空间约为该分支体积的 2 倍(压缩包 + 解压)。
  - 网络失败自动重试 3 次。
"""
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

OWNER = "7aGiven"
REPO = "Phigros_Resource"
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}"
ZIP_BASE = f"https://github.com/{OWNER}/{REPO}/archive/refs/heads"

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "assets" / "data"
ILLUSTRATION_DIR = ROOT / "assets" / "images" / "illustrations"

INFO_FILES = ("info.tsv", "difficulty.tsv")
RETRIES = 3


def _download_to(url: str, dest: Path, label: str) -> None:
    """下载单个文件到 dest,带重试。"""
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                with open(dest, "wb") as out:
                    shutil.copyfileobj(resp, out)
            print(f"[ok] {label} <- {url}")
            return
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last_err = e
            print(f"[重试 {attempt}/{RETRIES}] {label} 失败: {e}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"{label} 下载失败: {last_err}")


def sync_info_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in INFO_FILES:
        _download_to(f"{RAW_BASE}/info/{name}", DATA_DIR / name, name)


def _write_file(src, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as out:
        shutil.copyfileobj(src, out)


def sync_illustrations(app_naming: bool) -> None:
    ILLUSTRATION_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{ZIP_BASE}/illustration.zip"
    with tempfile.TemporaryDirectory(prefix="phigros_illu_") as tmp:
        zippath = Path(tmp) / "illustration.zip"
        _download_to(url, zippath, "illustration 分支 ZIP")
        print("解压中……")
        updated = new = app_named = 0
        total_bytes = 0
        with zipfile.ZipFile(zippath) as z:
            names = [i for i in z.infolist() if not i.is_dir()]
            # 去掉 zip 顶层目录前缀(如 Phigros_Resource-illustration/)
            prefix = ""
            if names and "/" in names[0].filename:
                prefix = names[0].filename.split("/", 1)[0] + "/"
            for idx, info in enumerate(names, 1):
                rel = info.filename[len(prefix):] if prefix else info.filename
                dest = ILLUSTRATION_DIR / rel
                if dest.exists():
                    updated += 1
                else:
                    new += 1
                with z.open(info) as src:
                    _write_file(src, dest)
                if app_naming and "." in rel:
                    # "组合名称.曲师.png" → 另存为 "组合名称.png"(应用实际加载的命名)
                    app_dest = ILLUSTRATION_DIR / (rel.split(".", 1)[0] + ".png")
                    with z.open(info) as src:
                        _write_file(src, app_dest)
                    app_named += 1
                total_bytes += info.file_size
                if idx % 50 == 0 or idx == len(names):
                    print(
                        f"  进度 {idx}/{len(names)}  (累计 {total_bytes / 1024 / 1024:.0f} MB)"
                    )
        print(f"曲绘完成: 新增 {new} 张,覆盖 {updated} 张"
              + (f",按应用命名另存 {app_named} 张" if app_naming else ""))


def main() -> int:
    app_naming = "--app-naming" in sys.argv[1:]
    print(f"数据目录 : {DATA_DIR}")
    print(f"曲绘目录 : {ILLUSTRATION_DIR}")
    print(f"应用命名 : {'开' if app_naming else '关'}")
    sync_info_files()
    sync_illustrations(app_naming)
    print("全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
