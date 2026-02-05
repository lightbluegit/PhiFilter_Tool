import re
import shutil
from dataclasses import dataclass

import pandas as pd
from PyQt5.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    QPropertyAnimation,
    QRect,
    QRectF,
    QRunnable,
    QSize,
    QStringListModel,
    Qt,
    QThreadPool,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QColor,
    QIcon,
    QImage,
    QPainter,
    QPainterPath,
    QPixmap,
    QTextOption,
)
from PyQt5.QtWidgets import (
    QCompleter,
    QFrame,
    QGraphicsBlurEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    CardWidget,
    CheckBox,
    ComboBox,
    EditableComboBox,
    ElevatedCardWidget,
    FlowLayout,
    HorizontalSeparator,
    ImageLabel,
    ListWidget,
    MenuAnimationType,
    PrimaryPushButton,
    RoundMenu,
    ScrollArea,
    SearchLineEdit,
    SmoothScrollArea,
    TextEdit,
)
from src.ui.styles import *
from src.utils.consts import *

# ------------------------- 这里是重写的控件 -------------------------


class combobox(QWidget):  # 重写combobox控件 选择框

    def __init__(
        self,
        content_list: list[str],  # 选项列表
        hint_label: str = "",  # 提示文本
        cbb_style: dict[str, str] = {},  # 选择框样式
        label_style: dict[str, str] = {},  # 文本样式
    ):
        super().__init__()
        self.editor_layout = QHBoxLayout(self)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(5)
        self.content_list = content_list

        # 左侧提示标签
        self.hint_label = label(hint_label, label_style)
        self.hint_label.adjustSize()
        self.editor_layout.addWidget(self.hint_label)

        # 选择主控件
        self.cbb = ComboBox()
        self.cbb.addItems(content_list)
        self.cbb.setStyleSheet(get_combobox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)

    def set_content(self, new_content_list: list[str]):
        """设置为新的内容列表

        入参：
            new_content_list: 新的内容列表
        """
        self.cbb.clear()
        self.cbb.addItems(new_content_list)

    def get_content(self) -> str:
        """获取当前选中内容

        返回值:
            str: 当前内容文本
        """
        return self.cbb.currentText()

    def bind_react_click_func(self, func):
        """绑定切换选项时执行的函数

        入参:
            func: 功能函数
        """
        self.cbb.currentTextChanged.connect(func)

    def set_current_choose(self, index: int):
        """设置当前选中内容

        入参:
            index: 设置的内容序号
        """
        self.cbb.setCurrentIndex(index)

    def set_hint_text(self, text: str):
        """设置提示文本

        入参:
            text: 提示文本
        """
        self.hint_label.setText(text)


class editable_combobox(QWidget):
    def __init__(
        self,
        content: list[str],
        hint_label: str = "",
        cbb_style: dict[str, str] = {},
        label_style: dict[str, str] = {},
        used_group=None,
    ):
        super().__init__()
        self.editor_layout = QHBoxLayout(self)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧提示标签
        self.hint_label = label(hint_label, label_style)
        self.editor_layout.addWidget(self.hint_label)

        self.cbb = EditableComboBox()
        self.cbb.addItems(content)
        self.cbb.setStyleSheet(get_combobox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)
        self.song_name_completer = QStringListModel(SONG_NAME_LIST)
        self.composer_completer = QStringListModel(COMPOSER_LIST)
        self.charter_completer = QStringListModel(CHARTER_LIST)
        self.drawer_completer = QStringListModel(DRAWER_NAME_LIST)
        self.group_info_completer = QStringListModel(used_group)
        self.nickname_completer = QStringListModel(NICKNAME_LIST)

    def set_content_list(self, content_list):
        self.cbb.clear()
        self.cbb.addItems(content_list)

    def get_content(self):
        return self.cbb.currentText()

    def clear_text(self):
        self.cbb.setText("")

    def set_text(self, text: str):
        self.cbb.setText(text)

    def bind_react_click_func(self, func):
        self.cbb.currentTextChanged.connect(func)

    def set_completer(self, model):
        # infolog(model)
        completer = QCompleter()
        completer.setFilterMode(Qt.MatchContains)  # 包含匹配
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        completer.setCompletionMode(QCompleter.PopupCompletion)  # 弹窗模式
        completer.setModel(model)
        self.cbb.setCompleter(completer)

    def clear_completer(self):
        self.cbb.setCompleter(None)

    def set_hint_text(self, text: str):
        """设置提示文本"""
        self.hint_label.setText(text)


class button(PrimaryPushButton):
    def __init__(
        self,
        text: str,
        style: dict = {
            "font_size": 30,
            "max_width": 300,
            "min_width": 300,
            "min_height": 35,
            "max_height": 35,
        },
        iconpath=None,
    ):
        super().__init__()

        self.setText(text)
        if iconpath:
            self.setIcon(QIcon(iconpath))

        base_style = f"""
            QPushButton {{
                padding: 6px 16px;
                outline: none;
                font-size: {style["font_size"]}px;
                font-family: "{FONT_FAMILY["chi"]}";
                max-width: {style['max_width']}px;
                min-width: {style['min_width']}px;
                min-height: {style['min_height']}px;
                max-height: {style['max_height']}px;
                border-radius: 7px;
            }}
        """

        # 背景色：#E6F7FF 边框色：#91D5FF 文字色：#0050B3
        color_style = """
            QPushButton {
                background-color: #E6F7FF; 
                border: 1px solid #91D5FF; 
                color: #0050B3;            
            }
            
            QPushButton:hover {
                background-color: #BAE7FF;
                border-color: #40A9FF;
                color: #003A8C;
            }
            
            QPushButton:pressed {
                background-color: #91D5FF;
                border-color: #096DD9;
                color: #002766;
                padding-top: 7px;
                padding-bottom: 5px;
            }
            
            QPushButton:disabled {
                background-color: #F5F5F5;
                border: 1px solid #D9D9D9;
                color: #B0B0B0;
            }
        """

        self.setStyleSheet(base_style + color_style)

    def bind_click_func(self, func):
        self.clicked.connect(func)

    def set_icon_size(self, w, h):
        self.setIconSize(QSize(w, h))


# 自定义样式的文本
class label(QLabel):
    def __init__(self, text: str, style: dict[str, str] = {}):
        super().__init__()
        self.setText(str(text))  # 设置文本内容
        self.setWordWrap(True)  # 启用自动换行
        self.setStyleSheet(get_label_style(**style))

    def set_text(self, text: str):
        self.setText(str(text))


# 不带样式的文本
class body_label(QLabel):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        self.setText(text)
        self.setWordWrap(True)  # 启用自动换行
        self.setAlignment(Qt.AlignVCenter)  # 默认垂直居中

    def set_text(self, text: str):
        self.setText(text)


# 多行文本
class multiline_text(TextEdit):

    def __init__(
        self,
        text: str = "",
        parent: QWidget = None,
        read_only: bool = False,
        style: dict[str, str] = {},
    ):
        super().__init__(parent)
        if read_only:
            self.setReadOnly(True)
        self.setText(text)
        self.setStyleSheet(get_multiline_text_style(**style))
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setAlignment(Qt.AlignVCenter)

    def set_text(self, text: str):
        self.setText(text)

    def get_plain_text(self):
        return self.toPlainText()


class input_line(SearchLineEdit):

    def __init__(
        self, default_text: str = "", place_holder: str = "", parent: QWidget = None
    ):
        super().__init__(parent)
        self.setClearButtonEnabled(True)
        self.setPlaceholderText(place_holder)
        self.setText(default_text)


# 不被折叠的主要信息部分
class main_info_card(ElevatedCardWidget):

    def __init__(
        self,
        imgpath: QPixmap,
        diff_bg_path: QPixmap,
        name: str,
        singal_rks: str,
        acc: str,
        level: str,
        diff: str,
        is_fc: bool,
        score: int = None,  # 等级
        index: int = None,
        combine_name: str = None,
        improve_advice: float | None = None,
    ):
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.setStyleSheet("border-radius: 10px;")
        self.left_func = None
        self.imgpath = imgpath
        self.combine_name = combine_name
        self.diff = diff
        self.diff_bg_path = diff_bg_path

        # --布局顶部曲名和评级--
        self.top_widget = QFrame(self)

        self.top_layout = QGridLayout(self.top_widget)  # 采用网格 控制中间的空白
        self.top_layout.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.top_layout.setSpacing(0)  # 设置控件之间的间距

        # 曲名
        rks_text = f"""<span style="line-height: 4px;font-family: '{FONT_FAMILY["chi"]}'; font-size: 29px;color: #ffffff">{name}</span>"""
        self.song_name_label = body_label(
            rks_text,
        )
        self.song_name_label.setMaximumWidth(230)
        self.top_layout.addWidget(
            self.song_name_label, 0, 1, 1, 4
        )  # (行, 列, 行跨度, 列跨度)
        self.song_name_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )  # 水平扩展，垂直自适应
        self.song_name_label.setAlignment(
            Qt.AlignVCenter
        )  # 居中对齐 否则与评级图片高度不一致很难看

        # 评级图片
        self.level_img = ImageLabel(
            resource_path(SCORE_LEVEL_PATH[get_score_level(score, is_fc)]),
            self.top_widget,
        )
        # infolog(SCORE_LEVEL_PATH[score_level])
        self.level_img.scaledToHeight(80)
        self.level_img.setContentsMargins(0, 0, 20, 0)
        self.top_layout.addWidget(
            self.level_img, 0, 5, 1, 1
        )  # (行, 列, 行跨度, 列跨度)
        self.level_img.setAlignment(Qt.AlignCenter)

        # 设置每一列的比例（左右留白+文字3份+图片1份）
        self.top_layout.setColumnStretch(0, 1)  # 左侧空白占1份
        self.top_layout.setColumnStretch(1, 1)  # 文字占1~3行
        self.top_layout.setColumnStretch(2, 1)
        self.top_layout.setColumnStretch(3, 1)
        self.top_layout.setColumnStretch(4, 1)  # 图片占1份 权重为2
        self.top_layout.setColumnStretch(5, 1)  # 留白 好像没用
        self.top_layout.setColumnStretch(6, 1)  # 留白 好像没用

        # --下层文本--
        self.bottom_widget = QFrame(self)

        self.bottom_layout = QGridLayout(self.bottom_widget)  # 采用网格 控制中间的空白
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.bottom_layout.setSpacing(2)  # 取消控件之间的间距

        # 推分建议
        self.improve_advice_label = label(
            "",
            {
                "font_size": 23,
                "font_color": (204, 250, 255, 1),
                "max_width": 150,
                "min_height": 26,
            },
        )

        if improve_advice is not None:
            self.improve_advice_label.setText(f"推分->{improve_advice}")
        else:
            self.improve_advice_label.setText("无法推分")
        # self.improve_advice_label.setWordWrap(True)
        self.bottom_layout.addWidget(
            self.improve_advice_label, 0, 1, 1, 2
        )  # (行, 列, 行跨度, 列跨度)
        self.improve_advice_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        self.improve_advice_label.setContentsMargins(10, 0, 0, 0)

        # 单曲rks
        rks_text = f"""
        <span style="font-family: '{FONT_FAMILY["chi"]}'; font-size: 27px; color: #a7fffc">rks:</span><span style="font-family: '{FONT_FAMILY["chi"]}'; font-size: 24px;color: #ffffff">{singal_rks}</span>"""
        self.rks_label = body_label(
            # "rks:" + str(singal_rks),
            rks_text,
            self.bottom_widget,
        )
        self.bottom_layout.addWidget(
            self.rks_label, 1, 0, 1, 1
        )  # (行, 列, 行跨度, 列跨度)
        # self.rks_label.setAlignment(Qt.AlignCenter)
        self.rks_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.rks_label.setContentsMargins(18, 0, 0, 0)

        # acc
        acc_text = f"""
        <span style="font-family: '{FONT_FAMILY["chi"]}'; font-size: 27px; color: #a7fffc">acc:</span><span style="font-family: '{FONT_FAMILY["chi"]}';font-size: 24px;color: #ffffff">{acc}%</span>"""
        self.acc_label = body_label(
            # "acc:" + str(acc),
            acc_text,
            self.bottom_widget,
        )
        self.bottom_layout.addWidget(
            self.acc_label, 1, 1, 1, 2
        )  # (行, 列, 行跨度, 列跨度)
        self.acc_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.acc_label.setContentsMargins(10, 0, 0, 0)

        # 定数
        score_text = f"""
        <span style="font-family: '{FONT_FAMILY["chi"]}'; font-size: 23px; color: #a7fffc">定数:</span><span style="font-family: '{FONT_FAMILY["chi"]}';font-size: 24px; color: #ffffff">{diff} {level}</span>"""
        self.level_label = body_label(
            # "定数:" + diff + " " + str(level),
            score_text,
            self.bottom_widget,
        )
        self.bottom_layout.addWidget(
            self.level_label, 2, 0, 1, 1
        )  # (行, 列, 行跨度, 列跨度)
        self.level_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.level_label.setContentsMargins(18, 3, 0, 0)

        # 分数
        score_text = f"""
        <span style="font-family: '{FONT_FAMILY["chi"]}'; font-size: 23px; color: #a7fffc">分数:</span><span style="font-family: '{FONT_FAMILY["chi"]}';font-size: 24px; color: #ffffff">{score}</span>"""
        self.score_label = body_label(
            score_text,
            self.bottom_widget,
        )
        self.bottom_layout.addWidget(
            self.score_label, 2, 1, 1, 2
        )  # (行, 列, 行跨度, 列跨度)
        self.score_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.score_label.setContentsMargins(10, 3, 0, 0)

        # 主布局（垂直排列）
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(0)  # 取消默认间距
        self.vBoxLayout.addWidget(self.top_widget)
        self.vBoxLayout.addWidget(self.bottom_widget)

        # 设置固定尺寸
        self.setFixedSize(400, 198)
        self.setCursor(Qt.PointingHandCursor)  # 鼠标悬停时显示手型指针

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.imgpath:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # 创建一个稍大的矩形以确保覆盖整个区域
            rect = QRectF(0, 0, self.width(), self.height())

            # 创建圆角矩形路径
            path = QPainterPath()
            radius = 10
            path.addRoundedRect(rect, radius, radius)

            # 设置裁剪区域
            painter.setClipPath(path)

            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self.imgpath)
            painter.drawPixmap(
                QRect(0, 0, self.width(), self.height()), self.diff_bg_path
            )

            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # infolog("左点击了!")
            self.left_func()
            self.clicked.emit()  # 需要先定义信号
        super().mousePressEvent(event)


# 左侧有底板背景作为提示 右侧可以任意填充内容的控件 hint_and_frame_widget
class hint_and_frame_widget(QFrame):

    def __init__(
        self,
        title: str,
        content_style: dict[str, int] = {
            "max-height": 63,
            "min-height": 63,
            "min-width": 250,
            "max-width": 250,
        },
    ):
        super().__init__()
        # ------------- 底层背景卡片 -------------
        self.setStyleSheet(
            """
            hint_and_frame_widget {
                background-color: rgba(255, 255, 255, 0.65);
                border-radius: 8px;
                margin: 4px 0;
                padding: 0;
                max-width: 380px;
            }
        """
        )
        self.setContentsMargins(0, 0, 0, 0)

        # ------------- 上层内容容器 -------------
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")  # 透明背景
        layout = QHBoxLayout(content_widget)
        layout.setContentsMargins(8, 8, 8, 8)  # 内边距
        layout.setSpacing(12)

        # 标题部分
        self.title_label = CaptionLabel(title)
        self.title_label.setStyleSheet(
            """
            min-width: 60px;
            font-size: 25px;
            color: #666;
            padding-right: 8px;
            border-radius: 8px;
            border-right: 1px solid #EEE;
            background-color: rgba(255, 255, 255, 0.85);
        """
        )
        layout.addWidget(self.title_label)

        # 内容部分
        self.scroll_area = SmoothScrollArea()
        layout.addWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            f"""QScrollArea{{
            background-color: transparent; 
            border: none;
            max-height: {content_style["max-height"]}px;
            min-height: {content_style["min-height"]}px;
            min-width: {content_style["max-width"]}px;
            max-width: {content_style["min-width"]}px;
            }}"""
        )
        # 创建内容容器
        self.scroll_content_widget = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content_widget)  # 使用流式布局
        self.flow_layout.setSpacing(5)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content_widget)
        layout.setStretch(1, 1)

        # ------------- 整体布局 -------------
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(content_widget)
        self.content_widget_list = []

    def add_widget(self, widget):
        self.content_widget_list.append(widget)
        self.flow_layout.addWidget(widget)

    def clear_content_widget(self):
        """清理内容区域加入的控件"""
        for widgeti in self.content_widget_list:
            widgeti.deleteLater()
        self.content_widget_list = []


# 歌曲信息卡片
class song_info_card(QWidget):

    def __init__(  # 更改入参的时候记得把.copy方法的参数也改掉
        self,
        imgpath: QPixmap,
        diff_bg_path: QPixmap,
        name: str,
        singal_rks: str,
        acc: str,
        level: str,
        diff: str,
        is_fc: bool,
        score: int = None,
        index: int = None,
        composer: str = "",
        chapter: str = "",
        drawer: str = "",
        is_expended: bool = False,
        combine_name: str = "",
        improve_advice: float | None = None,
        comment: str = "",
        group: list[str] = [],
        nickname_list: list[str] = [],
    ):
        super().__init__()
        # 保存数据
        self.imgpath = imgpath
        self.name = name
        self.singal_rks = singal_rks
        self.acc = acc
        self.level = level
        self.diff = diff
        self.is_fc = is_fc
        self.score = score
        self.index = index
        self.composer = composer
        self.chapter = chapter
        self.drawer = drawer
        self.combine_name = combine_name
        self.improve_advice = improve_advice
        self.diff_bg_path = diff_bg_path
        self.comment = comment
        self.group = group
        self.nickname_list = nickname_list

        self.right_func = None
        self.setContentsMargins(0, 0, 0, 0)
        self.is_expended = is_expended
        self._expanded_created = False  # 延迟标志

        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setSpacing(0)
        self.setMaximumHeight(405)
        self.setMaximumWidth(405)

        self.elevatedcard = main_info_card(
            imgpath,
            diff_bg_path,
            name,
            singal_rks,
            acc,
            level,
            diff,
            is_fc,
            score,
            index,
            combine_name,
            improve_advice,
        )
        self.mainlayout.addWidget(self.elevatedcard)
        self.elevatedcard.left_func = self.clicked_card

        self.scroll_area = SmoothScrollArea()
        self.mainlayout.addWidget(self.scroll_area)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            """QScrollArea{
            background-color: rgba(187, 255, 255, 0.6); 
            border: none; max-width: 400px;
            min-width: 400px; 
            min-height: 200px; 
            max-height: 200px;}"""
        )
        self.setStyleSheet("QWidget{background: transparent}")

        if not self.is_expended:
            self.scroll_area.hide()

        self.scroll_content_widget = None
        self.flow_layout = None

        self.label_style = """
            font-size: 24px;
            color: #333;
            background: transparent;
        """

        # 如果初始状态是展开，则延迟到事件循环创建一次，避免阻塞 __init__
        if self.is_expended:
            QTimer.singleShot(0, self._ensure_expanded_created)

    def _ensure_expanded_created(self):
        """按需构建展开区域（只会执行一次）"""
        if self._expanded_created:
            return
        self._expanded_created = True

        # 内容容器
        self.scroll_content_widget = QWidget()
        self.flow_layout = QVBoxLayout(self.scroll_content_widget)
        self.flow_layout.setSpacing(0)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.scroll_content_widget)

        # 禁用更新以批量添加控件，减少重复重绘
        self.scroll_content_widget.setUpdatesEnabled(False)
        nickname_str = ""
        for nicknamei in self.nickname_list:
            nickname_str += nicknamei + ", "
        nickname_str = nickname_str[:-2:]
        nickname_content_elm = multiline_text(nickname_str, read_only=True)
        nickname_label = hint_and_frame_widget("俗称:")
        nickname_label.add_widget(nickname_content_elm)
        self.flow_layout.addWidget(nickname_label)

        composer_content_elm = multiline_text(self.composer, read_only=True)
        composer_label = hint_and_frame_widget("曲师:")
        composer_label.add_widget(composer_content_elm)
        self.flow_layout.addWidget(composer_label)

        chapter_content_elm = multiline_text(self.chapter, read_only=True)
        chapter_label = hint_and_frame_widget("谱师:")
        chapter_label.add_widget(chapter_content_elm)
        self.flow_layout.addWidget(chapter_label)

        try:
            drawer_content_elm = multiline_text(self.drawer, read_only=True)
        except:
            infolog(f"歌曲{self.name}出错了 得到的是{self.drawer}")
        drawer_label = hint_and_frame_widget("画师:")
        drawer_label.add_widget(drawer_content_elm)
        self.flow_layout.addWidget(drawer_label)

        self.group_label = hint_and_frame_widget("分组:")
        self.group_content_label = multiline_text("、".join(self.group), read_only=True)
        self.group_label.add_widget(self.group_content_label)
        self.flow_layout.addWidget(self.group_label)

        self.comment_label = hint_and_frame_widget(
            "简评:",
            {
                "max-height": 90,
                "min-height": 90,
                "min-width": 250,
                "max-width": 250,
            },
        )
        self.comment_content_label = multiline_text(
            self.comment,
            read_only=True,
            style={
                "font_size": 19,
                "max_height": 85,
                "min_height": 85,
                "min_width": 250,
                "max_width": 250,
            },
        )
        self.comment_label.add_widget(self.comment_content_label)
        self.flow_layout.addWidget(self.comment_label)

        self.scroll_content_widget.setUpdatesEnabled(True)

    def clicked_card(self):
        self.is_expended = not self.is_expended
        if not self.is_expended:
            if self.scroll_content_widget:
                self.scroll_content_widget.hide()
            self.scroll_area.hide()
        else:
            if not self._expanded_created:
                # 延迟构建以保持响应
                QTimer.singleShot(0, self._ensure_expanded_created)
            self.scroll_area.show()
            if self.scroll_content_widget:
                self.scroll_content_widget.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton and self.right_func:
            self.right_func(self)
        super().mousePressEvent(event)

    # 深拷贝
    def copy(self):
        """深拷贝卡片组件"""
        return song_info_card(
            self.imgpath,
            self.diff_bg_path,
            self.name,
            self.singal_rks,
            self.acc,
            self.level,
            self.diff,
            self.is_fc,
            self.score,
            self.index,
            self.composer,
            self.chapter,
            self.drawer,
            True,  # 默认展开相关信息
            self.combine_name,
            self.improve_advice,
            self.comment,
            self.group,
            self.nickname_list,
        )


# 可折叠的主控件
class folder(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title="", expend=False):
        super().__init__()
        self.is_expanded = expend
        self.widgets = []
        self.title = title
        self.setMinimumWidth(420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 标题栏
        btn_style = {
            "background_color": (152, 245, 255, 1),
            "font_size": 34,
            "max_width": 360,
            "min_width": 360,
            "min_height": 50,
            "max_height": 50,
        }
        self.title_btn = button(title, btn_style)
        self.title_btn.bind_click_func(self.toggle_expand)
        self.title_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.title_btn)

        # 内容区域
        self.content_frame = QFrame()
        self.main_layout.addWidget(self.content_frame)
        self.content_frame.setContentsMargins(0, 0, 0, 0)

        if not self.is_expanded:
            self.content_frame.hide()
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        else:
            # 展开时允许竖向扩展以占满可用空间
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 保证内部 widget 可伸缩
        self.scroll_area.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        self.content_frame.setStyleSheet("QWidget{background: transparent}")
        self.content_layout.addWidget(self.scroll_area)
        self.content_layout.setSpacing(0)

        if not self.is_expanded:
            self.scroll_area.hide()

        # 创建内容容器与流式布局
        self.scroll_content_widget = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content_widget)  # 使用流式布局
        self.flow_layout.setSpacing(0)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)

        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content_widget)
        if not self.is_expanded:
            self.scroll_content_widget.hide()

    def toggle_expand(self):
        """切换展开/折叠状态并发出toggled信号"""
        self.is_expanded = not self.is_expanded
        if not self.is_expanded:
            # 折叠：隐藏内容，同时把自身竖向策略变为 Minimum（不占用额外空间）
            for i in self.widgets:
                try:
                    i.hide()
                except Exception:
                    pass
            self.scroll_content_widget.hide()
            self.scroll_area.hide()
            self.content_frame.hide()
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        else:
            self.content_frame.show()  # 必须先 show content_frame，否则 scroll_area/scroll_content_widget 可能无效
            self.scroll_area.show()
            self.scroll_content_widget.show()
            for i in self.widgets:
                try:
                    i.show()
                except Exception:
                    pass
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        try:
            self.updateGeometry()
            self.repaint()
        except Exception:
            pass

        self.toggled.emit(self.is_expanded)

    def add_widget(self, widget):
        """向内容区域添加控件"""
        self.widgets.append(widget)
        self.flow_layout.addWidget(widget)
        if not self.is_expanded:
            widget.hide()


# 搜索页面的一条筛选控件
class filter_obj(QWidget):

    def __init__(self, index: int, filter_obj_list, flow_layout, get_used_group):
        super().__init__()
        self.logical_cbb: combobox = None
        self.index = index
        self.filter_obj_list = filter_obj_list
        self.flow_layout = flow_layout
        self.get_used_group = get_used_group  # 这是个函数
        # 主布局
        self.setMaximumHeight(40)
        self.setFixedWidth(880)
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        # -----------属性选择部分-----------
        self.filter_attribution_list = FILTER_ATTRIBUTION_LIST
        cbb_style = {
            "max_width": 90,
            "min_width": 90,
            "min_height": 35,
            "max_height": 35,
            "font_size": 20,
        }
        label_style = {"min_width": 110, "max_width": 110, "font_size": 24}
        self.attribution_choose_cbb = combobox(
            self.filter_attribution_list, "筛选条件:", cbb_style, label_style
        )

        self.attribution_choose_cbb.setContentsMargins(0, 0, 0, 0)
        self.attribution_choose_cbb.bind_react_click_func(self.adapt_limit_option)
        self.main_layout.addWidget(self.attribution_choose_cbb)

        # -----------属性限制部分-----------
        self.filter_limit_list = NUMERIC_COMPARATORS + LOGICAL_OPERATORS
        self.limit_choose_cbb = combobox(self.filter_limit_list, "", cbb_style)
        self.limit_choose_cbb.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.limit_choose_cbb)

        # -----------属性限制值输入部分-----------
        limit_val_cbb_style = {
            "max_width": 150,
            "min_width": 150,
            "min_height": 35,
            "max_height": 35,
            "font_size": 23,
        }
        self.limit_val_cbb = editable_combobox(
            [], "", limit_val_cbb_style, used_group=list(get_used_group())
        )
        self.limit_val_cbb.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.limit_val_cbb)

        # -----------清除该筛选项按钮-----------
        btn_style = {
            "max_width": 17,
            "min_width": 17,
            "min_height": 20,
            "max_height": 20,
            "font_size": 40,
        }
        self.delete_btn = button("-", btn_style)
        if len(self.filter_obj_list) == 0:
            self.delete_btn.hide()
        self.delete_btn.setToolTip("清除该筛选项")
        self.delete_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.delete_btn)
        self.delete_btn.clicked.connect(self.delete_filter_obj)

        # -----------增加一个选项按钮-----------
        self.add_btn = button("+", btn_style)
        self.add_btn.setToolTip("新增筛选项")
        self.add_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.add_btn)
        self.add_btn.clicked.connect(self.add_filter_obj)

    def add_filter_obj(self):
        # infolog(self, self.filter_obj_list)
        filter_elm = filter_obj(
            len(self.filter_obj_list),
            self.filter_obj_list,
            self.flow_layout,
            self.get_used_group,
        )
        self.filter_obj_list.append(filter_elm)
        self.flow_layout.addWidget(filter_elm)
        self.filter_obj_list[0].delete_btn.show()
        self.add_btn.hide()
        if len(self.filter_obj_list) > 1:
            self.filter_obj_list[0].delete_btn.hide()  # 总不能全删完吧?

    def delete_filter_obj(self):
        self.filter_obj_list.remove(self)
        self.deleteLater()
        # infolog(self.filter_obj_list)
        self.filter_obj_list[-1].add_btn.show()
        if len(self.filter_obj_list) == 1:
            self.filter_obj_list[0].delete_btn.hide()  # 总不能全删完吧?

    def adapt_limit_option(self):
        """根据用户切换的属性更新补全器和可选择的值"""
        if self.attribution_choose_cbb.get_content() in (
            "acc",
            "单曲rks",
            "得分",
            "定数",
        ):
            self.filter_limit_list = NUMERIC_COMPARATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.clear_text()
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "评级":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(
                ["phi", "蓝V", "V", "S", "A", "B", "C", "F"]
            )
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "难度":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(["AT", "IN", "HD", "EZ"])
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "曲名":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(
                SONG_NAME_LIST
            )  # 曲名这里直接提供info.tsv里面的东西就好了 具体的区分(Another Me) 再加一个曲师就好了
            self.limit_val_cbb.set_completer(self.limit_val_cbb.song_name_completer)
            # infolog(
            #     "补全器模型:", self.limit_val_cbb.cbb.completer().model()
            # )

        elif self.attribution_choose_cbb.get_content() == "曲师":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(COMPOSER_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.composer_completer)

        elif self.attribution_choose_cbb.get_content() == "谱师":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(CHARTER_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.charter_completer)

        elif self.attribution_choose_cbb.get_content() == "画师":
            self.filter_limit_list = LOGICAL_OPERATORS
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(DRAWER_NAME_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.drawer_completer)

        elif self.attribution_choose_cbb.get_content() == "分组":
            self.filter_limit_list = ["包含", "不包含"]
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(list(self.get_used_group()))
            self.limit_val_cbb.set_completer(self.limit_val_cbb.group_info_completer)

        elif self.attribution_choose_cbb.get_content() == "简评":
            self.filter_limit_list = ["包含", "不包含"]
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "俗称":
            self.filter_limit_list = ["包含", "不包含"]
            self.limit_choose_cbb.set_content(self.filter_limit_list)
            self.limit_val_cbb.set_content_list(list(NICKNAME_LIST))
            self.limit_val_cbb.set_completer(self.limit_val_cbb.nickname_completer)

    def input_val_check(self, attribution, value) -> tuple[bool, str]:
        if attribution == "acc":
            # infolog(f"val={value}")
            if not value:
                return (True, 0)
            pattern = r"\d+\.?\d+"
            if "." not in value:  # 没有 . 就只能是 23 这样的整数
                value += "."
            if (
                value[0] == "."
            ):  # 如果输入为省略的格式(10. -> 10.0; .33 -> 0.33) 则补齐省略的0
                value = "0" + value
            if value[-1] == ".":
                value += "0"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                # infolog("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # infolog(match_results)
            acc = float(value)
            if acc > 100:  # 范围限定
                # infolog("acc不可能大于100")
                return (True, 100)
            if acc < 0:
                # infolog("acc不可能小于0")
                return (True, 0)
            return (True, value)

        elif attribution in ("单曲rks", "定数"):
            if not value:
                return (True, 0)
            pattern = r"\d+\.?\d+"
            if "." not in value:  # 没有 . 就只能是 23 这样的整数
                value += "."
            if (
                value[0] == "."
            ):  # 如果输入为省略的格式(10. -> 10.0; .33 -> 0.33) 则补齐省略的0
                value = "0" + value
            if value[-1] == ".":
                value += "0"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                # infolog("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # infolog(match_results)
            singal_rks = float(value)
            if singal_rks > MAX_LEVEL:  # 范围限定
                infolog(f"当前最高定数为{MAX_LEVEL} {attribution}不可能高于{MAX_LEVEL}")
                return (True, MAX_LEVEL)
            if singal_rks < 0:
                # infolog(f"{attribution}不可能小于0")
                return (True, 0)
            return (True, value)

        elif attribution == "得分":
            if not value:
                return (True, 0)
            pattern = r"\d+"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                infolog("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # infolog(match_results)
            score = int(value)
            if score > 1000000:  # 范围限定
                infolog("最高分只有100w 太高了啦")
                return (True, 1000000)
            if score < 0:
                infolog("得分不可能小于0")
                return (True, 0)
            return (True, value)

        elif attribution == "评级":
            if value not in ("F", "C", "B", "A", "S", "V", "蓝V", "phi"):
                infolog(f"评级不可能是{value}")
                return (False, None)
            return (True, value)

        elif attribution == "分组":
            if "`" in value:
                return (False, None)

        return (True, value)

    def get_all_condition(self) -> tuple[str, str, str]:  # 组合并返回当前的所有限制条件
        attribution = self.attribution_choose_cbb.get_content()
        limit = self.limit_choose_cbb.get_content()
        limit_val = self.limit_val_cbb.get_content()
        # infolog(attribution, limit, limit_val)
        check_result = self.input_val_check(attribution, limit_val)
        if check_result[0] == False:
            return None
        limit_val = check_result[1]
        return (attribution, limit, limit_val)


import csv
import os


def remove_group_from_csv(user_name, group_name_to_remove):
    """
    遍历 CSV 文件，删除指定的分组名，并重新序列化保存
    """
    group_path = appdata_path(f"{user_name}_{GROUP_PATH}")
    if not os.path.exists(group_path):
        print(f"文件不存在: {group_path}")
        return

    updated_rows = []
    file_changed = False

    try:
        # 读取文件
        with open(group_path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                # 确保行数据有效（至少有2列：键, 分组字符串）
                if len(row) < 2:
                    updated_rows.append(row)
                    continue

                key = row[0]
                groups_str = row[1]

                # 如果分组字符串为空，直接保留
                if not groups_str:
                    updated_rows.append(row)
                    continue

                # 反序列化：按反引号分割
                # filter(None, ...) 用于去除可能产生的空字符串
                group_list = groups_str.split("`")

                # 检查是否存在要删除的分组
                if group_name_to_remove in group_list:
                    # 移除分组
                    group_list.remove(group_name_to_remove)
                    file_changed = True

                    # 重新序列化：用反引号连接
                    new_groups_str = "`".join(group_list)
                    updated_rows.append([key, new_groups_str])
                else:
                    # 如果没有包含该分组，保持原样
                    updated_rows.append(row)

        # 只有在确实发生了更改时才写回文件，减少IO
        if file_changed:
            with open(group_path, mode="w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(updated_rows)
            print(f"已从文件中移除分组: {group_name_to_remove}")

    except Exception as e:
        print(f"处理 CSV 文件时出错: {e}")


# 可以多选的下拉菜单
class multi_check_combobox(EditableComboBox):
    selectionChanged = pyqtSignal(list)
    # 添加一个信号，如果外部需要知道哪个组被删除了，可以连接这个信号
    itemRemoved = pyqtSignal(str)

    def __init__(self, user_name, parent=None):
        super().__init__(parent)
        self.contain_list = []
        self.user_name = user_name
        self.setMaximumWidth(360)
        self.setMaximumHeight(28)

        # 创建自定义下拉菜单
        self.dropdown_menu = RoundMenu()
        self.scroll_area = ScrollArea(self.dropdown_menu)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        self.list_widget = ListWidget(self.scroll_area)
        self.list_widget.setObjectName("checkableListWidget")
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self.list_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(300)
        self.scroll_area.setMinimumHeight(200)
        self.dropdown_menu.addWidget(self.scroll_area)
        self.dropdown_menu.setMinimumWidth(300 - 5)
        self.scroll_area.setMinimumWidth(300 - 10)
        self.list_widget.setMinimumWidth(300 - 25)  # 考虑滚动条宽度
        self.dropButton.clicked.disconnect()
        self.dropButton.clicked.connect(self.show_menu)

    def show_menu(self):
        """显示自定义下拉菜单"""
        pos = self.mapToGlobal(self.rect().bottomLeft())
        if self.dropdown_menu.view.width() < self.width():
            self.dropdown_menu.view.setMinimumWidth(self.width())
            self.dropdown_menu.adjustSize()
        self.dropdown_menu.exec(pos, ani=True, aniType=MenuAnimationType.DROP_DOWN)

    def addItems(self, items):
        """添加可选项"""
        for text in items:
            # 避免重复添加
            if text in self.contain_list:
                continue

            self.contain_list.append(text)
            item = QListWidgetItem()
            self.list_widget.addItem(item)

            # --- 修改开始：创建容器 Widget ---
            container_widget = QWidget()
            layout = QHBoxLayout(container_widget)
            layout.setContentsMargins(5, 2, 5, 2)  # 调整边距
            layout.setSpacing(5)

            # 1. CheckBox
            if len(text) > 35:
                display_text = text[:32] + "..."
            else:
                display_text = text

            checkbox = CheckBox(display_text)
            checkbox.setObjectName("comboCheckBox")
            checkbox.setToolTip(text)  # 鼠标悬停显示完整文本

            # 2. 叉叉按钮
            close_btn = QPushButton("✕")
            close_btn.setFixedSize(20, 20)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # 设置样式：平时灰色透明，悬停变红
            close_btn.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #999999;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffe6e6;
                    color: #ff0000;
                }
            """
            )

            # 绑定删除事件，使用 lambda 捕获当前的 item 和 text
            # 注意：这里需要 item=item, text=text 来避免闭包变量捕获问题
            close_btn.clicked.connect(lambda _, i=item, t=text: self._remove_item(i, t))

            # 3. 组装布局
            layout.addWidget(checkbox)
            layout.addStretch()  # 弹簧，把叉叉顶到最右边
            layout.addWidget(close_btn)

            # 4. 设置给 list_widget
            self.list_widget.setItemWidget(item, container_widget)
            item.setSizeHint(container_widget.sizeHint())  # 确保 Item 高度正确
            # --- 修改结束 ---

    def _remove_item(self, item, text):
        """内部方法：点击叉叉时移除该项"""
        # 1. 获取行号并移除
        row = self.list_widget.row(item)
        if row >= 0:
            self.list_widget.takeItem(row)

        # 2. 从数据列表中移除
        if text in self.contain_list:
            self.contain_list.remove(text)

        # 3. 如果当前输入框显示的正是被删除的项，清空输入框
        if self.text() == text:
            self.setText("")

        remove_group_from_csv(self.user_name, text)
        # 4. 发送信号（可选）
        self.itemRemoved.emit(text)

    def get_selected_items(self):
        """获取当前选中的项"""
        selected = []
        if self.text():
            selected = [self.text()]

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # 注意：现在 itemWidget 是 container，需要找里面的 checkbox
            container = self.list_widget.itemWidget(item)
            # 假设 checkbox 是布局里的第一个控件
            if container:
                # 遍历 container 的子控件找到 checkbox (比较稳妥的方式)
                checkbox = container.findChild(CheckBox)
                # 或者如果你确定顺序，也可以 layout.itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    # 这里我们要获取 checkbox 的完整文本（通常存在 tooltip 或者我们需要存原始值）
                    # 简单起见，这里取 checkbox 显示的文本，但要注意被截断的情况
                    # 更好的做法是在创建时把原始 text 存为 checkbox 的属性
                    selected.append(checkbox.toolTip())

        # 去重
        return list(set(selected))

    def set_selected_items(self, items: list[str]):
        """设置选中项"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            container = self.list_widget.itemWidget(item)
            if container:
                checkbox = container.findChild(CheckBox)
                if checkbox:
                    # 比对 ToolTip (完整文本)
                    is_checked = checkbox.toolTip() in items
                    checkbox.setChecked(is_checked)

    def clear(self):
        """清除所有选项"""
        self.list_widget.clear()
        self.contain_list.clear()
        self.setText("")


# 主页的快捷功能卡片
class quick_function_card(CardWidget):
    def __init__(
        self,
        bg: QPixmap,
        preview_text: str = "",
        content_text: str = "",
        title_style: dict = {},
        content_style: dict = {},
        width: int = 250,
        height: int = 250,
    ):
        super().__init__()
        self.left_func = None
        self.bg = bg
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setSpacing(0)
        self.mainlayout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(width, height)
        self.mainlayout.addStretch(1)

        # 可移动部分
        self.moveable_part = expandable_text_widget(
            preview_text, content_text, title_style, content_style
        )
        self.mainlayout.addWidget(self.moveable_part)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.bg:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = QRectF(0, 0, self.width(), self.height())
            path = QPainterPath()
            radius = 15
            path.addRoundedRect(rect, radius, radius)
            painter.setClipPath(path)
            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self.bg)
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # infolog("左点击了!")
            self.left_func()
            self.clicked.emit()
        super().mousePressEvent(event)


# 鼠标悬停在页面上可以向上展开的控件
class expandable_text_widget(QWidget):

    def __init__(
        self,
        preview_text: str,
        content_text: str,
        title_style: dict[str, str] = {},
        content_style: dict[str, str] = {},
        width: int = 250,
        height: int = 80,
    ):
        super().__init__()
        self.w = width
        self.h = height
        self.expand = False
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(0, 0, 0, 0)
        self.mainlayout.setSpacing(10)

        # 漏出来的 标题
        self.title_label = label(preview_text, title_style)
        self.title_label.setAlignment(
            Qt.AlignHCenter | Qt.AlignTop
        )  # 如果AlignCenter 快速移入移出的时候会导致标题下降导致部分不可见
        self.mainlayout.addWidget(self.title_label)

        # 横分割线
        self.horizontal_separator = HorizontalSeparator()
        self.mainlayout.addWidget(self.horizontal_separator)
        self.horizontal_separator.hide()

        # 内容文字
        self.content_label = label(content_text, content_style)
        self.content_label.setWordWrap(True)  # 允许文字换行
        self.content_label.setAlignment(Qt.AlignTop)
        self.mainlayout.addWidget(self.content_label)
        self.content_label.hide()  # 默认隐藏

        self.resize(self.w, self.h)

        self.geometryAni = QPropertyAnimation(self, b"geometry")
        self.geometryAni.setDuration(180)
        self.len = 100

        self.original_geometry = self.geometry()
        self.geometryAni.finished.connect(self.animation_finished)

    def animation_finished(self):
        """动画结束后"""
        if self.expand:  # 结果状态是展开
            self.resize(self.w, self.h + self.len)
            self.content_label.show()
            self.horizontal_separator.show()
        else:
            self.resize(self.w, self.h)
            self.content_label.hide()
            self.horizontal_separator.hide()

    def enterEvent(self, e):
        """进入动画"""
        super().enterEvent(e)
        if self.geometryAni.state() != QPropertyAnimation.Running:
            self.original_geometry = self.geometry()
        # 计算悬停状态的目标几何
        targetRect = QRect(
            self.original_geometry.x(),
            self.original_geometry.y() - self.len,
            self.original_geometry.width(),
            self.height() + self.len,
        )

        # 没有在运行动画的话我就启动动画并展开
        if self.geometryAni.state() != QPropertyAnimation.Running:
            self.start_animation(self.original_geometry, targetRect)
            self.expand = True

    def leaveEvent(self, e):
        """鼠标离开 收回动画"""
        super().leaveEvent(e)
        self.start_animation(self.geometry(), self.original_geometry)
        self.expand = False

    def start_animation(self, start, end):
        """启动几何动画"""
        self.geometryAni.setStartValue(start)
        self.geometryAni.setEndValue(end)
        self.geometryAni.start()

    def paintEvent(self, event):
        """绘制透明白色背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(QRectF(self.rect()), QColor(255, 255, 255, 200))
        painter.end()
        super().paintEvent(event)


# 带有模糊效果背景图片的主控件
class bg_widget(QWidget):
    def __init__(self, bg: QPixmap, blur_num: float = 32.0):
        super().__init__()
        self.bg = bg
        self.blur_num = blur_num

    def paintEvent(self, event):
        """将模糊效果应用到控件的背景中 嘶 没看懂"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        scene = QGraphicsScene(self)
        pixmap_item = QGraphicsPixmapItem(self.bg)
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(self.blur_num)  # 设置模糊强度
        pixmap_item.setGraphicsEffect(blur_effect)
        scene.addItem(pixmap_item)
        original_size = self.bg.size()
        scaled_size = self.size()  # 目标大小是 widget 的大小
        if original_size.width() > 0 and original_size.height() > 0:
            scale_x = scaled_size.width() / original_size.width()
            scale_y = scaled_size.height() / original_size.height()
            scale = max(scale_x, scale_y)  # 选择较大的比例以确保填充
            pixmap_item.setScale(scale)
        scene_rect = QRectF(self.rect())
        scene.render(painter, scene_rect, scene_rect)


# 信号类
class WorkerSignals(QObject):
    finished = pyqtSignal()  # 完成单个任务


# 处理单个任务
class ImageLoaderWorker(QRunnable):
    def __init__(
        self,
        image_path: str,
        key: str,
        target_dict: dict[str, QPixmap],
        target_width: int,
    ):
        super().__init__()
        self.image_path = image_path
        self.key = key
        self.target_dict = target_dict
        self.target_width = target_width
        self.signal = WorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        """将图片转换为指定宽度的QPixmap并存储"""
        # infolog('run了', self.key)
        image = QImage(self.image_path)
        if image.isNull():
            self.signal.finished.emit()
            warnlog(f"{self.image_path}地址的图片不存在哦~")
            return

        original_width = image.width()
        original_height = image.height()
        target_height = int((self.target_width / original_width) * original_height)
        scaled_image = image.scaled(
            self.target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        pixmap = QPixmap.fromImage(scaled_image)
        self.target_dict[self.key] = pixmap  # 将转为QPixmap的图片存储到指定的字典中

        self.signal.finished.emit()
        # infolog("finish了")


# 任务管理器类
class ImageLoader(QObject):  # 继承 QObject 以支持信号
    all_tasks_finished = pyqtSignal()  # 全部任务都完成了

    def __init__(self):
        super().__init__()
        self.todo_list: list[tuple[str, str, dict[str, QPixmap], int]] = (
            []
        )  # 存储 (image_path, key, target_dict, width) 元组
        self.threadpool = QThreadPool()  # 开一个线程池 负责创建 销毁和管理线程
        self.total_tasks: int = 0  # 总任务量
        self.active_workers: list[ImageLoaderWorker] = []  # 待处理的任务

    def add_task(
        self, image_path: str, key: str, target_dict: dict[str, QPixmap], width: int
    ):
        """添加一个待处理任务"""
        self.todo_list.append((image_path, key, target_dict, width))
        # if key == '雪降り雪が降っている.AiSSw夜輪ft結月ゆかり': # 检查特定曲名是否正常运行
        #     infolog(f"接入任务: {image_path} -> {key}")

    def start_processing(self):
        """启动所有已添加的任务"""
        self.total_tasks = len(self.todo_list)
        infolog(f"开始处理任务 总任务量{self.total_tasks}")
        if self.total_tasks == 0:
            self.all_tasks_finished.emit()
            return

        # self.threadpool.setMaxThreadCount(
        #     min(8, self.threadpool.maxThreadCount())
        # )  # 可选：限制最大线程数

        # 清空上一次可能残留的引用
        self.active_workers.clear()
        for image_path, key, target_dict, width in self.todo_list:
            worker = ImageLoaderWorker(image_path, key, target_dict, width)
            worker.signal.finished.connect(  # 单个任务完成信号连接槽函数
                lambda w=worker: self.single_task_finished(w)
            )

            self.active_workers.append(worker)
            self.threadpool.start(worker)

        self.todo_list.clear()  # todo_list用完了

    def single_task_finished(self, worker):
        """处理单个任务完成"""
        self.active_workers.remove(worker)  # 移除已完成的处理器
        if self.active_workers == []:
            infolog(f"{self.total_tasks}个任务完成了!")
            self.all_tasks_finished.emit()  # 发射总完成信号


# -----------虽然用了模型与视图/委托交互的模式 但是实际上似乎只用了存储数据的部分...--------
@dataclass
class SongItem:  # 存储单个歌曲的信息
    combine_name: str
    diff: str
    name: str
    rks: float
    acc: float
    level: float
    score: int
    improve_advice: float | None
    is_fc: bool
    composer: str
    chapter: str
    drawer: str
    illustration: QPixmap
    bg_path: str
    groups: list[str]
    nickname_list: list[str]
    comment: str
    bg_pixmap: QPixmap | None = None


# 定义模型 为 QListView 提供数据 用于管理 SongItem 列表 负责将数据提供给视图 (如 QListView)。
class SongListModel(QAbstractListModel):

    def __init__(self, items: list[SongItem] = None):
        super().__init__()
        self.items = [] if items is None else items
        self.item_dict = {}  # {组合名称.难度 : SongItem}
        if items is not None:
            for itemi in items:
                self.item_dict[f"{itemi.combine_name}.{itemi.diff}"] = itemi

    def rowCount(
        self, parent=QModelIndex()
    ):  # 第二个参数虽然用不到 但是必须写 否则会报错 未知来源
        """(必需实现)返回模型的行数"""
        return len(self.items)

    def add_item(self, item: SongItem):
        # 向模型尾部插入一行
        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(item)
        self.item_dict[f"{item.combine_name}.{item.diff}"] = item
        self.endInsertRows()

    def get_item(self, row: int) -> SongItem | None:
        # 获取行对应的 SongItem
        if 0 <= row < len(self.items):
            return self.items[row]
        return None


class SongListViewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = SongListModel()  # 模型：管理和提供数据
        self.view = QListView()  # 向用户展示数据，并处理用户的交互（如点击、选择等）
        self.view.setModel(self.model)

    # 从存档中构建数据
    def init_model_from_save_data(
        self,
        save_dict: dict,
        diff_map_result: dict,
        cname_to_name: dict,
        illustration_cache: dict[str, QPixmap],
        bg_cache: dict[str, QPixmap],
        user_name: str,
    ):
        """从存档中构建数据"""
        infolog("开始从存档中构建数据")
        self.model = SongListModel()
        self.view.setModel(self.model)
        self.GROUP_INFO = {}
        self.COMMENT_INFO = {}
        # ----- 获取分组信息 -----
        group_path = appdata_path(f"{user_name}_{GROUP_PATH}")
        if not os.path.exists(group_path) or os.path.getsize(group_path) == 0:
            shutil.copy2(resource_path(DEFAULT_GROUP), group_path)

        df = pd.read_csv(
            group_path,
            sep=",",
            header=None,
            encoding="utf-8",
            names=["c_name", "group"],
        )
        df = df.fillna("")
        df.set_index(df.columns[0], inplace=True)
        used_group = set()
        for idx, rowi in df.iterrows():
            group_raw = str(rowi["group"])  # 组合名称 : 分组
            if group_raw:
                group_raw = group_raw.split("`")
                for i in group_raw:
                    used_group.add(i)
            self.GROUP_INFO[idx] = group_raw
            # infolog('GROUP_INFO是',GROUP_INFO)

            #     group_raw = str(rowi["group"]).strip()
            #     for groupi in group_raw.split("`"):
            #         if groupi:
            #             used_group.add(groupi)
            # used_group = list(used_group)

        # ----- 获取简评信息 -----
        comment_path = appdata_path(f"{user_name}_{COMMENT_PATH}")
        if not os.path.exists(comment_path) or os.path.getsize(comment_path) == 0:
            shutil.copy2(resource_path(DEFAULT_COMMENT), comment_path)

        df = pd.read_csv(
            comment_path,
            sep=",",
            header=None,
            encoding="utf-8",
            names=[
                "c_name",
                "EZ_comment",
                "HD_comment",
                "IN_comment",
                "AT_comment",
            ],
        )
        df = df.fillna("")
        df.set_index(df.columns[0], inplace=True)
        for idx, rowi in df.iterrows():
            self.COMMENT_INFO[idx] = {
                "EZ": str(rowi["EZ_comment"]),
                "HD": str(rowi["HD_comment"]),
                "IN": str(rowi["IN_comment"]),
                "AT": str(rowi["AT_comment"]),
            }

        row = 0
        for combine_name, all_diff_dic in diff_map_result.items():
            for diffi, leveli in all_diff_dic.items():
                gamerecord = save_dict["gameRecord"]
                # 一定会有的信息

                song_name, composer, drawer, chapter_dic = cname_to_name[combine_name]
                illustration = illustration_cache[combine_name]
                bg_path = bg_cache[diffi]
                nickname = NICKNAME_DICT.get(combine_name, [])  # 有可能暂时没有没别名
                if (
                    combine_name not in gamerecord
                    or diffi not in gamerecord[combine_name]
                ):  # 对于未游玩过的歌曲的处理
                    score = 0
                    acc = 0.0
                    is_fc = False
                    singal_rks = 0
                    groups = []
                    comment = ""
                else:
                    items = gamerecord[combine_name][diffi]
                    score = int(items["score"])
                    acc = float(items["acc"])
                    acc = round(acc, 4)
                    is_fc = True if items["fc"] == 1 else False
                    singal_rks = round(leveli * pow((acc - 55) / 45, 2), 4)
                    groups = self.GROUP_INFO.get(combine_name, {})
                    comment = self.COMMENT_INFO.get(combine_name, {}).get(diffi, "")

                # 构造 SongItem，并加入 model
                # infolog(f"模型正在写入{combine_name}")
                item = SongItem(
                    combine_name=combine_name,
                    diff=diffi,
                    name=song_name,
                    rks=singal_rks,
                    acc=acc,
                    level=leveli,
                    score=score,
                    improve_advice=None,
                    is_fc=is_fc,
                    composer=composer,
                    chapter=chapter_dic[diffi],
                    drawer=drawer,
                    illustration=illustration,
                    bg_path=bg_path,
                    groups=groups,
                    comment=comment,
                    nickname_list=nickname,
                )
                self.model.add_item(item)
                row += 1
        infolog("从存档中构建数据完成")

    def build_card(
        self, data: int | SongItem, is_expanded: bool = False
    ) -> song_info_card:
        """根据存储的数据构建卡片并返回"""
        if isinstance(data, int):
            item = self.model.get_item(data)
        elif isinstance(data, SongItem):
            item = data
        else:
            return None
        if not item:
            return None

        card = song_info_card(
            item.illustration,
            item.bg_path,
            item.name,
            item.rks,
            item.acc,
            item.level,
            item.diff,
            item.is_fc,
            item.score,
            None,
            item.composer,
            item.chapter,
            item.drawer,
            is_expanded,
            item.combine_name,
            item.improve_advice,
            item.comment,
            item.groups,
            item.nickname_list,
        )

        return card


# 分数计算结果展示控件 四个文字槽位 横向
class score_display_widget(QWidget):
    def __init__(
        self,
        perfect_num: str = "",
        great_num: str = "",
        bad_and_miss_num: str = "",
        max_count_num: str = "",
    ):
        super().__init__()
        self.setFixedWidth(600)
        layout = QHBoxLayout(self)
        label_list = [None, None, None, None]

        perfect_label = label(perfect_num)
        label_list[0] = perfect_label
        layout.addWidget(perfect_label)

        great_label = label(great_num)
        label_list[1] = great_label
        layout.addWidget(great_label)

        bad_and_miss_label = label(bad_and_miss_num)
        label_list[2] = bad_and_miss_label
        layout.addWidget(bad_and_miss_label)

        max_count_label = label(max_count_num)
        label_list[3] = max_count_label
        layout.addWidget(max_count_label)


class CapsuleTag(QFrame):
    # 自定义信号：当标签被移除时发出（可选，方便父控件知道标签没了）
    removed = pyqtSignal(str)

    def __init__(self, text, font_size=12, parent=None):
        super().__init__(parent)
        self.text_content = text

        # 1. 设置对象名，方便在 QSS 中特指这个控件
        self.setObjectName("CapsuleFrame")

        # 2. 设置布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            15, 5, 10, 5
        )  # 左 上 右 下 (调整边距以获得完美的胶囊感)
        layout.setSpacing(10)  # 文本和叉叉之间的距离

        # 3. 创建文本标签
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标签背景透明，防止遮挡胶囊背景
        self.label.setStyleSheet("background: transparent; border: none; color: #333;")

        # 4. 创建关闭按钮 ("X")
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)  # 按钮大小
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # 点击叉叉触发关闭逻辑
        self.close_btn.clicked.connect(self.close_tag)

        # 5. 添加到布局
        layout.addWidget(self.label)
        layout.addWidget(self.close_btn)

        # 6. 设置样式 (胶囊外观 + 白色 RGB 背景)
        self._set_style()

        # 自动调整大小以适应内容
        self.adjustSize()

    def _set_style(self):
        # 使用 QSS 设置样式
        # border-radius 的值通常是高度的一半，这里设为 15px 作为一个通用值
        # 如果字体很大，可能需要增加 padding 或 radius
        style = """
            QFrame#CapsuleFrame {
                background-color: rgb(255, 255, 255); /* 要求的白色背景 RGB */
                border: 1px solid #dcdcdc;            /* 加一点灰色边框，否则白色背景下看不清 */
                border-radius: 18px;                  /* 胶囊圆角 */
            }
            
            QPushButton {
                background-color: transparent;
                border: none;
                color: #999999;
                font-weight: bold;
                border-radius: 10px;
            }
            
            QPushButton:hover {
                background-color: #ffcccc; /* 悬停时的红色背景 */
                color: #ff0000;
            }
        """
        self.setStyleSheet(style)

    def close_tag(self):
        """处理标签移除"""
        self.removed.emit(self.text_content)  # 发送信号
        self.close()  # 从视觉上关闭窗口
        self.deleteLater()  # 安排资源释放
