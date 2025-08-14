from enum import Enum
from PyQt5.QtGui import QFontDatabase


# ------------------------- 这里写自定义的枚举量 -------------------------
class score_level_type(Enum):
    F = "F"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    V = "V"
    VFC = "蓝V"
    phi = "phi"


class special_type(Enum):
    AP = "AP"
    FC = "FC"
    NO_PLAY = "NO_PLAY"  # 还没玩过
    EMPTY = ""  # 无特殊状态


# 默认路径
# 整个文件的相对路径前缀
FILE_PATH = "projects/phi_tool/"

# 主文件夹下的文件可以直接写
CODE_PATH = FILE_PATH + "main_code.py"

# 固定的运行依赖文件夹
DEPENDENCES_PREPATH = FILE_PATH + "dependences/"

DIFFICULTY_PATH = DEPENDENCES_PREPATH + "difficulty.tsv"  # 各个歌曲难度文件
INFO_PATH = DEPENDENCES_PREPATH + "info.tsv"  # 组合名称与拆分名称对应关系文件

# 字体文件
FONT_PREPATH = DEPENDENCES_PREPATH + "font/"

EN_FONT1 = FONT_PREPATH + "Playfair_Display/PlayfairDisplay-VariableFont_wght.ttf"
NUM_FONT1 = FONT_PREPATH + "Share_Tech_Mono/ShareTechMono-Regular.ttf"
CHI_FONT1 = FONT_PREPATH + "ZCOOLKuaiLe/ZCOOLKuaiLe-Regular.ttf"

# 玩家信息(player_info)文件夹下文件的路径前缀
PLAYER_INFO_PREPATH = FILE_PATH + "player_info/"

TOKEN_PATH = PLAYER_INFO_PREPATH + "session_token.txt"  # 玩家session_token存储路径

# 图片素材(images)文件夹下文件的路径前缀
IMAGES_PREPATH = FILE_PATH + "images/"

# 各种小图标
ICON_PREPATH = IMAGES_PREPATH + "icons/"

INDEX_TAG_PATH = ICON_PREPATH + "index_tag.png"  # b27 phi3序号图像底部图形

SCORE_LEVEL_ICONS_PREPATH = ICON_PREPATH + "score_level_icons/"

SCORE_LEVEL_PATH: dict[score_level_type:str] = {
    score_level_type.F: SCORE_LEVEL_ICONS_PREPATH + "F.png",
    score_level_type.C: SCORE_LEVEL_ICONS_PREPATH + "C.png",
    score_level_type.B: SCORE_LEVEL_ICONS_PREPATH + "B.png",
    score_level_type.A: SCORE_LEVEL_ICONS_PREPATH + "A.png",
    score_level_type.S: SCORE_LEVEL_ICONS_PREPATH + "S.png",
    score_level_type.V: SCORE_LEVEL_ICONS_PREPATH + "V.png",
    score_level_type.VFC: SCORE_LEVEL_ICONS_PREPATH + "VFC.png",
    score_level_type.phi: SCORE_LEVEL_ICONS_PREPATH + "phi.png",
}
# 生成的二维码与空二维码
QRCODE_IMG_PREPATH = IMAGES_PREPATH + "QRcode/"

QRCODE_IMG_PATH = QRCODE_IMG_PREPATH + "QRcode.png"
QRCODE_EMPTY_IMG_PATH = QRCODE_IMG_PREPATH + "QRcode_empty.png"

# 各种背景
BACKGROUND_IMG_PREPATH = IMAGES_PREPATH + "background/"

SONG_CARD_BACKGROUND: dict[str, str] = {
    "EZ": BACKGROUND_IMG_PREPATH + "green-EZ.png",
    "HD": BACKGROUND_IMG_PREPATH + "blue-HD.png",
    "IN": BACKGROUND_IMG_PREPATH + "red-IN.png",
    "AT": BACKGROUND_IMG_PREPATH + "gold-AT.png",
}

# 插图
ILLUSTRATION_PREPATH = IMAGES_PREPATH + "illustration/"

# 特殊状态下歌曲卡片的标题颜色SPECIAL_TITLE_COLOR


SPECIAL_TITLE_COLOR = {
    special_type.AP: "rgb(254,254,67)",  # phi的黄色
    special_type.FC: "rgb(25,125,255)",  # V的蓝色
    special_type.NO_PLAY: "black",
    special_type.EMPTY: "white",
}


# 默认样式表
def get_comboBox_style(
    font_size: str = 23,
    max_width: str = 360,
    min_width: str = 360,
    min_height: str = 50,
    max_height: str = 50,
    border_radius: str = 7,
    background_color: tuple[str, str, str, str] = (255, 255, 255, 0),
):
    style = "ComboBox {\n"
    style += f"font-size: {font_size}px;\n"
    # style += f'font-family: "{font_family}";\n'
    # style += f"color: {font_color};\n"
    style += f"max-width: {max_width}px;\n"
    style += f"min-width: {min_width}px;\n"
    style += f"min-height: {min_height}px;\n"
    style += f"max-height: {max_height}px;\n"
    style += f"border: 2px solid black;\n"
    style += f"border-radius: {border_radius}px;\n"
    r, g, b, a = background_color
    style += f"background-color: rgba({r},{g},{b},{a});\n"
    style += """text-align: left;  /* 文本左对齐 */
        padding-left: 5px;  /* 可选：增加左边距 */\n"""
    style += "}"
    return style


def get_button_style(
    max_width: str = 360,
    min_width: str = 360,
    min_height: str = 50,
    max_height: str = 50,
    font_family: str = "仿宋",
    font_size: str = 34,
    border_radius: str = 7,
    background_color: tuple[str, str, str, str] = (0, 159, 170, 1),
    # color: tuple[str, str, str, str] = (0, 159, 170, 1),
):
    style = """PushButton {\n """

    r, g, b, a = background_color
    contain = f"""
    font-size: {font_size}px;
    font-family: "{font_family}";
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    border-radius: {border_radius}px;
    background-color: rgba({r},{g},{b},{a});
    color: white;
    """

    style += (
        contain
        + "\n}"
        + """/* 悬停状态 */
    PushButton:hover {
        background-color: #00CDCD;
    }
    
    /* 按下状态 */
    PushButton:pressed {
        background-color: #7FFFD4;
    }"""
    )

    return style


def get_label_style(
    font_size: str = 26,
    max_width: str = 80,
    min_width: str = 80,
    min_height: str = 50,
    max_height: str = 50,
    font_family: str = "楷体",
    font_color: str = "black",
    background_color: tuple[int, int, int, int] = (255, 255, 255, 0),
):
    style = """QLabel {\n"""
    style += f"max-width: {max_width}px;\n"
    style += f"min-width: {min_width}px;\n"
    style += f"min-height: {min_height}px;\n"
    style += f"max-height: {max_height}px;\n"
    style += f"font-size: {font_size}px;\n"
    style += f'font-family: "{font_family}";\n'
    style += f"color: {font_color};\n"
    r, g, b, a = background_color
    style += f"background-color: rgba({r},{g},{b},{a});\n"
    style += "}"
    # print(style)
    return style


def get_input_box_style(
    max_width: str = 300,
    min_width: str = 300,
    min_height: str = 60,
    max_height: str = 60,
    font_family: str = "仿宋",
    font_size: str = 28,
    border_radius: str = 7,
    background_color: tuple[str, str, str, str] = (255, 248, 220, 1),
    # color: tuple[str, str, str, str] = (0, 159, 170, 1),
):
    style = "LineEdit {\n "

    r, g, b, a = background_color
    content = f"""
    font-size: {font_size}px;
    font-family: "{font_family}";
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    border-radius: {border_radius}px;
    background-color: rgba({r},{g},{b},{a});
    """

    style += content + "\n}"
    return style


DEFAULT_EN_FONT = "Segoe UI"
DEFAULT_CN_FONT = "Microsoft YaHei"
DEFAULT_JP_FONT = "Yu Gothic UI"


FILTER_ATTRIBUTION_LIST: list[str] = [
    "acc",
    "单曲rks",
    "得分",
    "定数",
    "评级",
    "难度",
    "曲名",
    "曲师",
    "谱师",
    "画师",
]
# 数值类比较
NUMERIC_COMPARATORS: list[str] = [
    "大于",
    "大于等于",
    "小于",
    "小于等于",
    "等于",
    "不等于",
]

# 精确 模糊比较
LOGICAL_OPERATORS: list[str] = ["等于", "不等于", "包含", "不包含"]
