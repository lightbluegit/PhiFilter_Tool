import os
from typing import Dict

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from dependences.consts import *

illustration_cache: Dict[str, QPixmap] = {}
song_card_background_cache: Dict[str, QPixmap] = {}


def get_illustration(combine_name: str, width: int = 420) -> QPixmap:
    """
    根据**组合名称**获取(或创建并缓存)指定歌曲的曲绘图片

    参数：
        combine_name: 组合名称
        width: 指定宽度(默认 420 跟卡片宽度一样)

    返回：
        缓存或新建的QPixmap类
    """
    global illustration_cache
    if combine_name in illustration_cache:
        return illustration_cache[combine_name]
    # 构造路径并载入
    path = os.path.join(ILLUSTRATION_PREPATH, f"{combine_name}.png")
    pix = QPixmap(path).scaledToWidth(int(width), Qt.SmoothTransformation)
    illustration_cache[combine_name] = pix
    return pix


def get_song_card_bg(diff: str, width: int = 420) -> QPixmap:
    """
    根据 难度 获取(或创建并缓存)差分背景

    参数：
        diff: 难度(EZ/HD/IN/AT)
        width: 指定宽度(默认 420 跟卡片宽度一样)

    返回：
        缓存或新建的QPixmap类
    """
    global song_card_background_cache
    key = str(diff)
    if key not in ('EZ', 'HD', 'IN', 'AT'):
        return 
    if key in song_card_background_cache.keys():
        return song_card_background_cache[key]
    
    path = SONG_CARD_BACKGROUND[key]
    pix = QPixmap(path).scaledToWidth(int(width), Qt.SmoothTransformation)
    song_card_background_cache[key] = pix
    return pix
