from PyQt5.QtGui import QFontDatabase
from src.utils.consts import CHI_FONT1_PATH

# ---------------默认样式表获取---------------

FONT_FAMILY = {}
font_id = QFontDatabase.addApplicationFont(CHI_FONT1_PATH)
if font_id < 0:
    FONT_FAMILY["chi"] = "仿宋"
    print("中文字体加载失败！ 已切换为仿宋")
else:
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
    FONT_FAMILY["chi"] = font_family


def get_combobox_style(
    font_size: str = 23,
    font_family: str = FONT_FAMILY["chi"],
    max_width: str = 360,
    min_width: str = 360,
    min_height: str = 50,
    max_height: str = 50,
    border_radius: str = 7,
    background_color: tuple[str, str, str, str] = (255, 255, 255, 0),
):
    style = "ComboBox {\n"
    r, g, b, a = background_color
    style += f"""
    font-size: {font_size}px;
    font-family: "{font_family}";
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    border: 2px solid black;
    border-radius: {border_radius}px;
    background-color: rgba({r},{g},{b},{a});
    text-align: left;
    padding-left: 5px;
    """
    style += "}"
    return style


def get_label_style(
    font_size: str = 26,
    max_width: str = 0,
    min_width: str = 0,
    min_height: str = 0,
    max_height: str = 0,
    font_family: str = FONT_FAMILY["chi"],
    font_color: tuple[int, int, int, int] = (0, 0, 0, 1),
    background_color: tuple[int, int, int, int] = (255, 255, 255, 0),
    other: str = None,
):
    style = """QLabel {\n"""
    r, g, b, a = background_color
    fr, fg, fb, fa = font_color
    style += f"""
    font-size: {font_size}px;
    font-family: '{font_family}';
    color: rgba({fr},{fg},{fb},{fa});
    background-color: rgba({r},{g},{b},{a});
    """

    if max_width > 0:
        style += f"max-width: {max_width}px;\n"
    if min_width > 0:
        style += f"min-width: {min_width}px;\n"
    if min_height > 0:
        style += f"min-height: {min_height}px;\n"
    if max_height > 0:
        style += f"max-height: {max_height}px;\n"

    style += (other if other is not None else "") + "}"
    return style


def get_input_box_style(
    max_width: str = 300,
    min_width: str = 300,
    min_height: str = 60,
    max_height: str = 60,
    font_family: str = FONT_FAMILY["chi"],
    font_size: str = 28,
    border_radius: str = 7,
    background_color: tuple[str, str, str, str] = (255, 248, 220, 1),
):
    style = "LineEdit {\n "
    r, g, b, a = background_color
    style += f"""
    font-size: {font_size}px;
    font-family: "{font_family}";
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    border-radius: {border_radius}px;
    background-color: rgba({r},{g},{b},{a});
    """
    style += "}"
    return style


def get_switch_button_style(
    font_family: str = FONT_FAMILY["chi"],
    max_width: str = 210,
    min_width: str = 210,
    min_height: str = 30,
    max_height: str = 30,
):
    style = "SwitchButton {\n"
    style += f"""
    font-family: "{font_family}";
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    """
    style += "}"
    return style


def get_multiline_text_style(
    max_width: str = 250,
    min_width: str = 250,
    min_height: str = 63,
    max_height: str = 63,
    font_size: str = 19,
    background_transparent: str = 1,
):
    style = "QTextEdit {\n"
    if(background_transparent):
        style += "background-color: transparent;"
    style += f"""
    border: none;
    font-size: {font_size}px;
    max-width: {max_width}px;
    min-width: {min_width}px;
    min-height: {min_height}px;
    max-height: {max_height}px;
    """
    style += "}"
    return style
