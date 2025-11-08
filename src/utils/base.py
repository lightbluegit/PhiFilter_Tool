from pathlib import Path
import os
import sys
from enum import Enum
import logging
from logging.handlers import RotatingFileHandler

debug: bool = False
debug: bool = True


def appdata_path(relative_path="", create_file=True):
    """
    获取可写的用户数据目录路径

    Args:
        relative_path: 相对路径，空字符串返回文件夹路径
        create_file: 是否创建文件（当relative_path不为空时）
    """
    if debug:
        base_path = Path.cwd()
    else:
        if sys.platform == "win32":
            base = Path(os.environ["APPDATA"])

            base_path = base / "PhiFilterTool"

    # 确保基础目录存在
    base_path.mkdir(parents=True, exist_ok=True)

    if not relative_path:
        # 返回文件夹路径
        return str(base_path)

    # 处理文件路径
    file_path = base_path / relative_path

    if create_file:
        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.touch()  # 创建空文件
            print(f"创建文件: {file_path}")

    return str(file_path)


def resource_path(relative_path):
    """
    获取打包后资源的正确路径
    用法: resource_path("images/avatar/1.png")
    """
    if debug:
        base_path = os.path.abspath(".")
    else:
        # PyInstaller 会创建临时文件夹，并把路径存入 sys._MEIPASS
        base_path = sys._MEIPASS
    return os.path.join(base_path, relative_path)


LOG_PATH = "PhiFilterTool_log.log"  # 日志文件


# 记录器
logger = logging.getLogger("PhiFilterTool_log")
logger.setLevel(logging.INFO)

# 创建处理器
infofilehandler = RotatingFileHandler(
    filename="PhiFilterTool_infolog.log",
    maxBytes=15 * 1024 * 1024,  # 10 MB
    backupCount=3,  # 保留3个备份文件
)
filehandler = logging.FileHandler(filename="PhiFilterTool_log.log")
filehandler.setLevel(logging.WARNING)

# 创建格式
formatter = logging.Formatter(
    "%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s|%(message)s"
)

# 绑定格式
infofilehandler.setFormatter(formatter)
filehandler.setFormatter(formatter)
# 记录器添加处理器
logger.addHandler(infofilehandler)
logger.addHandler(filehandler)

debuglog = logger.debug
infolog = logger.info
warnlog = logger.warning
errlog = logger.error
crtclog = logger.critical


class score_level_type(Enum):
    F = "F"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    V = "V"
    VFC = "蓝V"
    phi = "phi"


# 获取评级
def get_score_level(score: int, is_fc: bool = False) -> score_level_type:
    if score == 1000000:
        return score_level_type.phi
    elif is_fc:
        return score_level_type.VFC
    elif score >= 960000:
        return score_level_type.V
    elif score >= 920000:
        return score_level_type.S
    elif score >= 880000:
        return score_level_type.A
    elif score >= 820000:
        return score_level_type.B
    elif score >= 600000:
        return score_level_type.C
    else:
        return score_level_type.F
