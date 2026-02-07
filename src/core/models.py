from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class user_data:
    # 基础信息
    user_name: str = ""
    token: str = ""  # 用户 session_token
    avatar: str = ""  # 用户头像文件名
    background_name: str = ""  # 背景图名称
    user_introduction: str = ""

    # 核心数据
    rks: float = 0.0
    total_rks: float = 0.0  # rks未/30之前得到的值 用于计算某个歌曲是否能推分
    money: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)  # KB MB GB TB PB
    challengemode_rank: str = ""

    # 统计数据 (建议封装成小对象，这里先照搬你的结构)# 各个难度的统计数据[cleared, FC, AP]
    EZ_stats: List[int] = field(default_factory=lambda: [-1, -1, -1])
    HD_stats: List[int] = field(default_factory=lambda: [-1, -1, -1])
    IN_stats: List[int] = field(default_factory=lambda: [-1, -1, -1])
    AT_stats: List[int] = field(default_factory=lambda: [-1, -1, -1])

    # 复杂结构
    # b27 = [(单曲rks, 处于item的哪一行), ...]
    b27: List[Tuple[float, Tuple[str, Any]]] = field(default_factory=list)
    phi3: List[Tuple[float, Tuple[str, Any]]] = field(default_factory=list)
    save_dict: dict = field(default_factory=dict)  # 云存档解析后的字典数据

    # 之前存储的数据是否为最新的数据
    is_updated: bool = False
