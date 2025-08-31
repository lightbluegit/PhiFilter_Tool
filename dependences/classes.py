from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QGridLayout,
    QCompleter,
    QListWidgetItem,
    QSizePolicy,
    QGraphicsBlurEffect,
)
from PyQt5.QtCore import (
    Qt,
    QStringListModel,
    pyqtSignal,
    QSize,
    QTimer,
    QRectF,
    QRect,
    QPropertyAnimation,
    QObject,
    QRunnable,
    QThreadPool,
)
from PyQt5.QtGui import QIcon, QColor, QPainter, QTextOption, QImage, QPainterPath
from qfluentwidgets import (
    PrimaryPushButton,
    LineEdit,
    ComboBox,
    EditableComboBox,
    FlowLayout,
    ElevatedCardWidget,
    CaptionLabel,
    BodyLabel,
    ImageLabel,
    ToolTipFilter,
    HorizontalSeparator,
    SmoothScrollArea,
    RoundMenu,
    MenuAnimationType,
    TextEdit,
    CheckBox,
    ListWidget,
    ScrollArea,
    CardWidget,
)
from dependences.image_cache import *
from dependences.consts import *
import re
import random

# ------------------------- 这里是重写的控件 -------------------------


class combobox(QWidget):  # 重写combobox控件

    def __init__(
        self,
        content: list[str],
        hint_label: str = "",
        cbb_style: dict[str, str] = {},
        label_style: dict[str, str] = {},
    ):
        super().__init__()
        self.editor_layout = QHBoxLayout(self)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧提示标签
        if hint_label:

            self.hint_label = label(hint_label, label_style)
            self.editor_layout.addWidget(self.hint_label)

        self.cbb = ComboBox()
        self.cbb.addItems(content)
        self.cbb.setStyleSheet(get_combobox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)
        # print(style)

    def set_content(self, new_content):
        self.cbb.clear()
        self.cbb.addItems(new_content)

    def get_content(self) -> str:
        return self.cbb.currentText()

    def bind_react_click_func(self, func):
        self.cbb.currentTextChanged.connect(func)

    def set_current_choose(self, index: int):
        self.cbb.setCurrentIndex(index)


class editable_combobox(QWidget):
    def __init__(
        self,
        content: list[str],
        hint_label: str = "",
        cbb_style: dict[str, str] = {},
        label_style: dict[str, str] = {},
    ):
        super().__init__()
        self.editor_layout = QHBoxLayout(self)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧提示标签
        if hint_label:
            self.hint_label = label(hint_label, label_style)
            self.editor_layout.addWidget(self.hint_label)

        self.cbb = EditableComboBox()
        self.cbb.addItems(content)
        self.cbb.setStyleSheet(get_combobox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)
        # print(style)
        # 初始化补全模型QAbstractItemModel
        self.groups = set(GROUP_INFO.values())
        self.tags = set(TAG_INFO.values())
        self.comments = set()
        for i in COMMENT_INFO.values():
            # print(f'i={i}')
            for key, val in i.items():
                self.comments.add(val)
                # print('val=',val)
        self.song_name_completer = QStringListModel(SONG_NAME_LIST)
        self.composer_completer = QStringListModel(COMPOSER_LIST)
        self.charter_completer = QStringListModel(CHARTER_LIST)
        self.drawer_completer = QStringListModel(DRAWER_NAME_LIST)
        self.group_info_completer = QStringListModel(self.groups)
        self.tag_info_completer = QStringListModel(self.tags)
        self.comment_info_completer = QStringListModel(self.comments)

    def set_content(self, new_content):
        self.cbb.clear()
        self.cbb.addItems(new_content)

    def get_content(self):
        return self.cbb.currentText()

    def clear_text(self):
        self.cbb.setText("")

    def bind_react_click_func(self, func):
        self.cbb.currentTextChanged.connect(func)

    def set_completer(self, model):
        # print(model)
        completer = QCompleter()
        completer.setFilterMode(Qt.MatchContains)  # 包含匹配
        completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        completer.setCompletionMode(QCompleter.PopupCompletion)  # 弹窗模式
        completer.setModel(model)
        self.cbb.setCompleter(completer)

    def clear_completer(self):
        self.cbb.setCompleter(None)


class button(PrimaryPushButton):

    def __init__(self, text: str, style: dict[str, str] = {}, iconpath=None):
        super().__init__()
        self.setText(text)  # 设置按钮文本
        self.setStyleSheet(get_button_style(**style))
        if iconpath:
            self.setIcon(QIcon(iconpath))

    def bind_click_func(self, func):  # 绑定按钮对应功能
        self.clicked.connect(func)

    def set_icon_size(self, w, h):
        self.setIconSize(QSize(w, h))


class label(QLabel):
    def __init__(self, text: str, style: dict[str, str] = {}):
        super().__init__()
        self.setText(text)  # 设置文本内容
        self.setWordWrap(True)  # 启用自动换行
        self.setStyleSheet(get_label_style(**style))

    def set_text(self, text: str):
        self.setText(text)


class body_label(QLabel):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        # 1. 基础设置（保持与QFluentBodyLabel一致）
        self.setText(text)
        self.setWordWrap(True)  # 启用自动换行
        self.setAlignment(Qt.AlignVCenter)  # 默认垂直居中
        # print(style)

    def set_text(self, text: str):
        self.setText(text)


class multiline_text(TextEdit):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        # 1. 基础设置（保持与QFluentBodyLabel一致）
        self.setText(text)
        self.setWordWrapMode(QTextOption.WordWrap)  # 启用自动换行
        self.setAlignment(Qt.AlignVCenter)  # 默认垂直居中
        # print(style)

    def set_text(self, text: str):
        self.setText(text)

    def set_md_text(self, text):
        self.setMarkdown(text)

    def set_html_text(self, text):
        self.setHtml(text)

    def get_plain_text(self):
        return self.toPlainText()

    def get_md_text(self):
        return self.toMarkdown()

    def get_html_text(self):
        return self.toHtml()


class input_box(LineEdit):

    def __init__(
        self, place_holder: str, have_clear_btn: bool = True, style: dict[str, str] = {}
    ):
        super().__init__()
        self.setPlaceholderText(place_holder)
        self.setClearButtonEnabled(have_clear_btn)
        self.setStyleSheet(get_input_box_style(**style))


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


class main_info_card(ElevatedCardWidget):

    def __init__(
        self,
        imgpath: QPixmap,
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
        self.bg_img_path = SONG_CARD_BACKGROUND[diff]

        # --布局顶部曲名和评级--
        self.top_widget = QFrame(self)

        self.top_layout = QGridLayout(self.top_widget)  # 采用网格 控制中间的空白
        self.top_layout.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.top_layout.setSpacing(0)  # 设置控件之间的间距

        # 曲名
        self.song_name_label = label(
            name,
            {
                "font_size": 29,
                "max_width": 230,
                "min_width": 230,
                "min_height": 30,
                "max_height": 100,
                "font_color": (255, 255, 255, 1),
            },
        )
        self.song_name_label.setWordWrap(True)  # 允许曲名自动换行
        self.top_layout.addWidget(
            self.song_name_label, 0, 1, 1, 4
        )  # (行, 列, 行跨度, 列跨度)
        self.song_name_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )  # 水平扩展，垂直自适应
        self.song_name_label.setAlignment(
            Qt.AlignCenter
        )  # 居中对齐 否则与评级图片高度不一致很难看

        # 评级图片
        self.level_img = ImageLabel(
            SCORE_LEVEL_PATH[get_score_level(score, is_fc)], self.top_widget
        )
        # print(SCORE_LEVEL_PATH[score_level])
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
        if improve_advice is not None:

            self.improve_advice_label = label(
                f"推分->{improve_advice}",
                {
                    "font_size": 23,
                    "font_color": (188, 188, 188, 1),
                    "max_width": 150,
                    "min_height": 26,
                },
            )
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
        # self.rks_label.setStyleSheet(
        # f"""
        # font-size: 27px;
        # color: #DCDCDC;
        # """
        # )
        # self.rks_label.setWordWrap(True)
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
        # self.acc_label.setStyleSheet(
        #     f"""
        # font-size: 26px;
        # color: #ffffff;
        # """
        # )
        # self.acc_label.setWordWrap(True)
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
        # self.level_label.setStyleSheet(
        #     f"""
        # font-size: 26px;
        # color: #ffffff;
        # """
        # )
        # self.level_label.setWordWrap(True)
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
        # self.score_label.setStyleSheet(
        #     f"""
        # font-size: 25px;
        # color: #ffffff;
        # """
        # )
        # self.score_label.setWordWrap(True)
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

            # 绘制背景图片
            # illustration = get_illustration(self.combine_name, self.width())
            difference = get_song_card_bg(self.diff, self.width())

            # 绘制到整个矩形区域
            # print(f"种类是{type(self.imgpath)}, {self.imgpath}")
            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self.imgpath)
            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), difference)

            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # print("左点击了!")
            self.left_func()
            self.clicked.emit()  # 需要先定义信号
        super().mousePressEvent(event)


#! 这个要删掉
class tag(PrimaryPushButton):
    def __init__(self, text="", bg_color=None, border_width=2):
        super().__init__()

        self.setFixedHeight(28)  # 固定高度
        self.setCursor(Qt.PointingHandCursor)
        bg_color_list = [
            (70, 130, 200, 60),
            (200, 100, 100, 60),
            (127, 255, 212, 60),
            (240, 255, 240, 60),
            (255, 250, 205, 60),
        ]
        if bg_color is None:
            idx = random.randint(0, len(bg_color_list) - 1)
            r, g, b, a = bg_color_list[idx]
        self.bg_color = (r, g, b, a)

        self.setToolTip(text)
        self.setText(text)
        self.installEventFilter(ToolTipFilter(self, 200))
        # 禁用默认按钮样式
        self.setStyleSheet(f"border: none; background-color: rgba({r},{g},{b},{a});")


class HorizontalInfoCard(QFrame):
    def __init__(self, title: str):
        super().__init__()

        # ------------- 底层背景卡片 -------------
        self.setStyleSheet(
            """
            HorizontalInfoCard {
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
            """QScrollArea{
            background-color: transparent; 
            border: none;
            max-height: 55px;
            min-height: 55px;
            min-width: 250px;
            max-width: 250px;
            }"""
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


class song_info_card(QWidget):
    def __init__(
        self,
        imgpath: QPixmap,
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

        composer_content_elm = BodyLabel(self.composer)
        composer_content_elm.setStyleSheet(self.label_style)
        composer_content_elm.setWordWrap(True)
        composer_label = HorizontalInfoCard("曲师:")
        composer_label.add_widget(composer_content_elm)
        self.flow_layout.addWidget(composer_label)

        chapter_content_elm = BodyLabel(self.chapter)
        chapter_content_elm.setStyleSheet(self.label_style)
        chapter_content_elm.setWordWrap(True)
        chapter_label = HorizontalInfoCard("谱师:")
        chapter_label.add_widget(chapter_content_elm)
        self.flow_layout.addWidget(chapter_label)

        drawer_content_elm = BodyLabel(self.drawer)
        drawer_content_elm.setStyleSheet(self.label_style)
        drawer_content_elm.setWordWrap(True)
        drawer_label = HorizontalInfoCard("画师:")
        drawer_label.add_widget(drawer_content_elm)
        self.flow_layout.addWidget(drawer_label)

        self.group_label = HorizontalInfoCard("分组:")
        self.flow_layout.addWidget(self.group_label)

        self.tag_label = HorizontalInfoCard("标签:")
        self.flow_layout.addWidget(self.tag_label)

        self.comment_label = HorizontalInfoCard("简评:")
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

    def copy(self):
        return song_info_card(
            self.imgpath,
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
        )

    def set_edited_info(self, group: list[str], tags: list[str], comment: str):
        if not self._expanded_created:
            self._ensure_expanded_created()

        # 批量添加时关闭更新以避免多次重绘
        self.scroll_content_widget.setUpdatesEnabled(False)

        # tags
        self.tag_label.clear_content_widget()
        for tagi in tags:
            if not tagi:
                continue
            # print(tagi)
            tag_elm = tag("#" + tagi)
            self.tag_label.add_widget(tag_elm)

        self.group_label.clear_content_widget()
        for groupi in group:
            if not groupi:
                continue
            group_elm = BodyLabel(groupi)
            # group_elm.setStyleSheet(self.label_style)
            # group_elm.setWordWrap(True)
            self.group_label.add_widget(group_elm)

        # comment
        self.comment_label.clear_content_widget()
        if comment:
            comment_elm = BodyLabel(comment)
            comment_elm.setStyleSheet(self.label_style)
            comment_elm.setWordWrap(True)
            self.comment_label.add_widget(comment_elm)

        self.scroll_content_widget.setUpdatesEnabled(True)


class folder(QWidget):
    """
    改版 folder：
    - 去掉固定的大最小高度（折叠时不占用大量空间）
    - 在展开/折叠时调整自身的 QSizePolicy（展开时竖向 Expanding，折叠时竖向 Minimum）
    - 发出 toggled(bool) 信号，方便父布局根据展开状态调整 layout 的 stretch 分配
    """

    toggled = pyqtSignal(bool)

    def __init__(self, title="", expend=False):
        super().__init__()
        self.is_expanded = expend
        self.widgets = []
        self.title = title

        # 不再设置全局固定最小高度，保留宽度最小约束（可按需调整）
        self.setMinimumWidth(420)

        # 默认 QSizePolicy：水平方向可扩展，垂直方向使用 Minimum（折叠时不占用多余空间）
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 标题栏 (可点击)
        btn_style = {
            "background_color": (152, 245, 255, 1),
        }
        self.title_btn = button(title, btn_style)
        self.title_btn.bind_click_func(self.toggle_expand)
        self.title_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.title_btn)

        # 内容区域 (用 QFrame 包裹)
        self.content_frame = QFrame()
        self.main_layout.addWidget(self.content_frame)
        self.content_frame.setContentsMargins(0, 0, 0, 0)

        # 初始根据 expend 隐藏/显示内容，并设置 sizePolicy
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
        """切换展开/折叠状态，并调整 QSizePolicy，发出 toggled 信号以便父布局调整 stretch"""
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
            # 展开：显示内容，允许竖向扩展以填充父布局给的可用空间
            self.content_frame.show()  # 必须先 show content_frame，否则 scroll_area/scroll_content_widget 可能无效
            self.scroll_area.show()
            self.scroll_content_widget.show()
            for i in self.widgets:
                try:
                    i.show()
                except Exception:
                    pass
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 通知布局管理器更新几何
        try:
            self.updateGeometry()
            self.repaint()
        except Exception:
            pass

        # 发出信号，父布局（例如 place_b27_phi3）要监听并根据所有 folder 的状态重新分配 stretch
        try:
            self.toggled.emit(self.is_expanded)
        except Exception:
            pass

    def add_widget(self, widget):
        """向内容区域添加控件"""
        self.widgets.append(widget)
        self.flow_layout.addWidget(widget)
        # 避免强制 title_btn 宽度跟随内容宽度（会产生副作用），所以移除固定宽度的设置
        # self.title_btn.setMinimumWidth(self.scroll_content_widget.width())
        # self.title_btn.setMaximumWidth(self.scroll_content_widget.width())
        if not self.is_expanded:
            try:
                widget.hide()
            except Exception:
                pass


class filter_obj(QWidget):

    def __init__(self, index: int, filter_obj_list, flow_layout):
        super().__init__()
        self.index = index
        self.filter_obj_list = filter_obj_list
        self.flow_layout = flow_layout
        # 主布局
        self.setMaximumHeight(40)
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
        self.filter_limit_list = NUMERIC_COMPARATORS
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
        self.limit_val_cbb = editable_combobox([], "", limit_val_cbb_style)
        self.limit_val_cbb.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.limit_val_cbb)

        # -----------清除该筛选项按钮-----------
        btn_style = {
            "max_width": "50",
            "min_width": "50",
            "min_height": 35,
            "max_height": 35,
        }
        self.delete_btn = button("-", btn_style)
        if len(self.filter_obj_list) == 0:
            self.delete_btn.hide()
        self.delete_btn.setToolTip("清除该筛选项")
        self.delete_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.delete_btn)
        self.delete_btn.clicked.connect(self.delete_filter_obj)

        # -----------增加一个选项按钮-----------
        btn_style = {
            "max_width": "50",
            "min_width": "50",
            "min_height": 35,
            "max_height": 35,
        }
        self.add_btn = button("+", btn_style)
        self.add_btn.setToolTip("新增筛选项")
        self.add_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.add_btn)
        self.add_btn.clicked.connect(self.add_filter_obj)

    def add_filter_obj(self):
        # print(self, self.filter_obj_list)
        filter_elm = filter_obj(
            len(self.filter_obj_list), self.filter_obj_list, self.flow_layout
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
        # print(self.filter_obj_list)
        self.filter_obj_list[-1].add_btn.show()
        if len(self.filter_obj_list) == 1:
            self.filter_obj_list[0].delete_btn.hide()  # 总不能全删完吧?

    def adapt_limit_option(self):
        if self.attribution_choose_cbb.get_content() in (
            "acc",
            "单曲rks",
            "得分",
            "定数",
        ):
            self.limit_choose_cbb.set_content(NUMERIC_COMPARATORS)
            self.limit_val_cbb.clear_text()
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "评级":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(["phi", "蓝V", "V", "S", "A", "B", "C", "F"])
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "难度":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(["AT", "IN", "HD", "EZ"])
            self.limit_val_cbb.clear_completer()

        elif self.attribution_choose_cbb.get_content() == "曲名":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(
                SONG_NAME_LIST
            )  # 曲名这里直接提供info.tsv里面的东西就好了 具体的区分(Another Me) 再加一个曲师就好了
            self.limit_val_cbb.set_completer(self.limit_val_cbb.song_name_completer)
            # print(
            #     "补全器模型:", self.limit_val_cbb.cbb.completer().model()
            # )

        elif self.attribution_choose_cbb.get_content() == "曲师":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(COMPOSER_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.composer_completer)

        elif self.attribution_choose_cbb.get_content() == "谱师":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(CHARTER_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.charter_completer)

        elif self.attribution_choose_cbb.get_content() == "画师":
            self.limit_choose_cbb.set_content(LOGICAL_OPERATORS)
            self.limit_val_cbb.set_content(DRAWER_NAME_LIST)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.drawer_completer)

        elif self.attribution_choose_cbb.get_content() == "分组":
            self.limit_choose_cbb.set_content(["包含", "不包含"])
            self.limit_val_cbb.set_content(self.limit_val_cbb.groups)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.group_info_completer)

        elif self.attribution_choose_cbb.get_content() == "标签":
            self.limit_choose_cbb.set_content(["包含", "不包含"])
            self.limit_val_cbb.set_content(self.limit_val_cbb.tags)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.tag_info_completer)

        elif self.attribution_choose_cbb.get_content() == "简评":
            self.limit_choose_cbb.set_content(["包含", "不包含"])
            self.limit_val_cbb.set_content(self.limit_val_cbb.comments)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.comment_info_completer)

    def input_val_check(self, attribution, limit, value) -> bool:
        if attribution == "acc":
            if not value:
                return False
            pattern = r"\d+\.?\d+"
            if (
                value[0] == "."
            ):  # 如果输入为省略的格式(10. -> 10.0; .33 -> 0.33) 则补齐省略的0
                value = "0" + value
            if value[-1] == ".":
                value += "0"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                print("无法匹配")
                return False
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            acc = float(value)
            if acc > 100:  # 范围限定
                print("acc不可能大于100喵")
                return False
            if acc < 0:
                print("acc不可能小于0喵")
                return False
            return True

        elif attribution in ("单曲rks", "定数"):
            if not value:
                return False
            pattern = r"\d+\.?\d+"
            if (
                value[0] == "."
            ):  # 如果输入为省略的格式(10. -> 10.0; .33 -> 0.33) 则补齐省略的0
                value = "0" + value
            if value[-1] == ".":
                value += "0"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                print("无法匹配")
                return False
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            singal_rks = float(value)
            if singal_rks > MAX_LEVEL:  # 范围限定
                print(
                    f"当前最高定数为{MAX_LEVEL}喵 {attribution}不可能高于{MAX_LEVEL}喵"
                )
                return False
            if singal_rks < 0:
                print(f"{attribution}不可能小于0喵")
                return False
            return True

        elif attribution == "得分":
            if not value:
                return False
            pattern = r"\d+"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                print("无法匹配")
                return False
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            score = int(value)
            if score > 1000000:  # 范围限定
                print("最高分只有100w喵 太高了啦")
                return False
            if score < 0:
                print("得分不可能小于0喵")
                return False
            return True

        elif attribution == "评级":
            if value not in ("F", "C", "B", "A", "S", "V", "蓝V", "phi"):
                print(f"评级不可能是{value}喵")
                return False
            return True

        elif attribution in ("分组", "标签"):
            if "`" in value:
                return False

        return True

    def get_all_condition(self) -> tuple[str, str, str]:  # 组合并返回当前的所有限制条件
        attribution = self.attribution_choose_cbb.get_content()
        limit = self.limit_choose_cbb.get_content()
        limit_val = self.limit_val_cbb.get_content()
        if self.input_val_check(attribution, limit, limit_val) == False:
            return None
        return (attribution, limit, limit_val)


class CheckableComboBox(EditableComboBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_items = []
        self.setMaximumWidth(300)
        # 创建自定义下拉菜单
        self.dropdown_menu = RoundMenu()
        self.scroll_area = ScrollArea(self.dropdown_menu)
        self.scroll_area.setWidgetResizable(True)  # 关键设置
        self.scroll_area.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        # 必须给内部的视图也加上透明背景样式
        self.list_widget = ListWidget(self.scroll_area)

        # 配置下拉菜单
        self.list_widget.setObjectName("checkableListWidget")
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setWidget(self.list_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(300)
        self.scroll_area.setMinimumHeight(200)
        self.dropdown_menu.addWidget(self.scroll_area)

        # 连接信号
        # self.list_widget.itemClicked.connect(self._on_item_clicked)

        # 替换默认下拉行为
        self.dropdown_menu.setMinimumWidth(300 - 5)
        self.scroll_area.setMinimumWidth(300 - 10)
        self.list_widget.setMinimumWidth(300 - 25)  # 考虑滚动条宽度
        self.dropButton.clicked.disconnect()
        self.dropButton.clicked.connect(self._show_custom_menu)

    def _show_custom_menu(self):
        """显示自定义下拉菜单"""
        # 计算位置
        pos = self.mapToGlobal(self.rect().bottomLeft())

        # 更新菜单尺寸
        if self.dropdown_menu.view.width() < self.width():
            self.dropdown_menu.view.setMinimumWidth(self.width())
            self.dropdown_menu.adjustSize()
        # 显示菜单
        self.dropdown_menu.exec(pos, ani=True, aniType=MenuAnimationType.DROP_DOWN)

    def addItems(self, items):
        """添加可选项"""
        for text in items:
            item = QListWidgetItem()
            self.list_widget.addItem(item)

            # 创建带文本的复选框

            # 文本过长时显示省略号
            if len(text) > 35:
                display_text = text[:32] + "..."
            else:
                display_text = text
            checkbox = CheckBox(display_text)
            checkbox.setObjectName("comboCheckBox")
            # 设置工具提示显示完整文本
            checkbox.setToolTip(display_text)

            # 设置项控件
            self.list_widget.setItemWidget(item, checkbox)
            item.setSizeHint(checkbox.sizeHint())  # 确保正确的高度

    def selectedItems(self):
        """获取当前选中的项"""
        selected = []
        if self.text():
            selected = [self.text()]
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            if checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def setSelectedItems(self, items: list[str]):
        """设置选中项"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            checkbox.setChecked(checkbox.text() in items)

        # self._update_selection()

    def clear(self):
        """清除所有选项"""
        self.list_widget.clear()
        self._selected_items = []
        self.setText("")


class quick_function_card(CardWidget):
    def __init__(
        self,
        bg: QPixmap,
        preview_text="",
        content_text="",
        title_style={},
        content_style={},
    ):
        super().__init__()
        self.left_func = None
        self.bg = bg
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setSpacing(0)
        self.mainlayout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(250, 250)

        self.mainlayout.addStretch(1)

        self.moveable_part = ExpandableTextWidget(
            preview_text, content_text, title_style, content_style
        )
        self.mainlayout.addWidget(self.moveable_part)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.bg:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            # 绘制背景图片
            rect = QRectF(0, 0, self.width(), self.height())
            path = QPainterPath()
            radius = 15
            path.addRoundedRect(rect, radius, radius)

            # 设置裁剪区域
            painter.setClipPath(path)
            # 绘制到整个矩形区域
            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self.bg)
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # print("左点击了!")
            self.left_func()
            self.clicked.emit()  # 需要先定义信号
        super().mousePressEvent(event)


class ExpandableTextWidget(QWidget):
    def __init__(self, preview_text, content_text, title_style, content_style):
        super().__init__()

        # 初始化布局
        self.expand = False
        self.mainlayout = QVBoxLayout(self)
        self.mainlayout.setContentsMargins(0, 0, 0, 0)
        self.mainlayout.setSpacing(10)

        # 创建标签
        self.title_label = label(preview_text, title_style)
        self.title_label.setWordWrap(True)  # 允许文字换行
        self.title_label.setAlignment(Qt.AlignCenter)  # 居中显示
        self.mainlayout.addWidget(self.title_label)

        self.horizontal_separator = HorizontalSeparator()
        self.mainlayout.addWidget(self.horizontal_separator)
        self.horizontal_separator.hide()

        self.content_label = label(content_text, content_style)
        # print(f"content_style={content_style}")
        self.content_label.setWordWrap(True)  # 允许文字换行
        self.content_label.setAlignment(Qt.AlignTop)  # 居中显示
        self.mainlayout.addWidget(self.content_label)
        self.content_label.hide()

        # 设置初始大小
        self.resize(250, 70)

        # 创建几何动画
        self.geometryAni = QPropertyAnimation(self, b"geometry")
        self.geometryAni.setDuration(300)
        self.len = 100
        # self.geometryAni.setEasingCurve(QEasingCurve.OutBack)

        # 保存初始几何状态
        self._originalGeo = self.geometry()
        self.geometryAni.finished.connect(self._on_animation_finished)

    def _on_animation_finished(self):
        # print("动画完成！")
        if self.expand:
            self.resize(250, 70 + self.len)
            self.content_label.show()
            self.horizontal_separator.show()
        else:
            self.resize(250, 70)
            self.content_label.hide()
            self.horizontal_separator.hide()
        # 在这里执行动画完成后的操作

    def enterEvent(self, e):
        super().enterEvent(e)
        if self.geometryAni.state() != QPropertyAnimation.Running:
            self._originalGeo = self.geometry()
        # 计算悬停状态的目标几何
        targetRect = QRect(
            self._originalGeo.x(),
            self._originalGeo.y() - self.len,
            self._originalGeo.width(),
            self.height() + self.len,
        )

        # 没有在运行动画的话我就启动动画
        if self.geometryAni.state() != QPropertyAnimation.Running:
            self._startGeometryAni(self._originalGeo, targetRect)
            self.expand = True

    def leaveEvent(self, e):
        super().leaveEvent(e)
        # 返回初始几何
        self._startGeometryAni(self.geometry(), self._originalGeo)
        self.expand = False

        # self.resize(250, 100)
        # self.content_label.hide()
        # self.horizontal_separator.hide()

    # def mousePressEvent(self, e):
    #     super().mousePressEvent(e)
    #     # 返回初始几何
    #     self._startGeometryAni(self.geometry(), self._originalGeo)
    #     self.content_label.hide()
    #     self.horizontal_separator.hide()

    def _startGeometryAni(self, start, end):
        """启动几何动画"""
        self.geometryAni.setStartValue(start)
        self.geometryAni.setEndValue(end)
        self.geometryAni.start()

    def paintEvent(self, event):
        # 创建圆角矩形路径

        # 创建QPainter并设置裁剪区域
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 填充背景（透明白色）
        painter.fillRect(QRectF(self.rect()), QColor(255, 255, 255, 200))
        painter.end()

        # 调用父类方法绘制其他内容
        super().paintEvent(event)


from PyQt5.QtWidgets import (
    QWidget,
    QGraphicsBlurEffect,
    QGraphicsScene,
    QGraphicsPixmapItem,
)
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt


class bg_widget(QWidget):
    def __init__(self, bg: QPixmap, blur_num: float = 18.0):
        super().__init__()
        # self.setWindowTitle("Blurred Background with QGraphicsBlurEffect")
        # self.resize(800, 600)
        # 请确保有一个名为 'bg.jpg' 的图片文件在脚本同目录下
        # 或者提供完整路径
        self.bg = bg

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 加载图片
        # 创建一个临时的 QGraphicsScene
        scene = QGraphicsScene(self)

        # 创建一个 QGraphicsPixmapItem 来持有图片
        pixmap_item = QGraphicsPixmapItem(self.bg)

        # 创建 QGraphicsBlurEffect 并设置模糊半径
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(16.0)  # 调整此值以改变模糊强度

        # 将模糊效果应用到 pixmap item
        pixmap_item.setGraphicsEffect(blur_effect)

        # 将 item 添加到场景
        scene.addItem(pixmap_item)

        # 缩放图片以适应窗口大小 (保持宽高比填充)
        # 我们需要先将 pixmap_item 放入场景才能正确获取其 bounds
        # 因此，我们先添加 item，然后根据原始 pixmap 大小设置 scale
        original_size = self.bg.size()
        scaled_size = self.size()  # 目标大小是 widget 的大小
        if original_size.width() > 0 and original_size.height() > 0:
            # 计算缩放比例以填充
            scale_x = scaled_size.width() / original_size.width()
            scale_y = scaled_size.height() / original_size.height()
            scale = max(scale_x, scale_y)  # 选择较大的比例以确保填充
            pixmap_item.setScale(scale)

        # 确定场景的渲染区域 (即 widget 的大小)
        scene_rect = QRectF(self.rect())

        # 使用 QPainter 将 QGraphicsScene 渲染到 widget 上
        # render(target painter, target area, source area, render options)
        scene.render(painter, scene_rect, scene_rect)

        # 清理 (可选，因为 scene 是临时的，会在方法结束时被销毁)


# --- 信号类 ---
class WorkerSignals(QObject):
    finished = pyqtSignal()  # Worker 完成信号 (单个任务)
    progress = pyqtSignal(int, int)  # 发送 (当前完成任务数, 总任务数)
    log_message = pyqtSignal(str)
    # 修改 pixmap_loaded 信号，包含 key 和 target_dict
    pixmap_loaded = pyqtSignal(str, object, object)  # (key, QPixmap, target_dict)


# --- 工作单元 (QRunnable) - 处理单个任务 ---
class ImageLoaderWorker(QRunnable):
    def __init__(self, image_path, key, target_dict, target_width):
        super().__init__()
        self.image_path = image_path
        self.key = key
        self.target_dict = target_dict  # 虽然传递了，但实际存储由 ImageLoaderApp 控制
        self.target_width = target_width
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    def run(self):
        # print('run了', self.key)
        try:
            image = QImage(self.image_path)
            if image.isNull():
                self.signals.finished.emit()
                print(f"图片不存在哦~")
                return

            original_width = image.width()
            original_height = image.height()
            if original_width <= 0 or original_height <= 0:
                self.signals.finished.emit()
                return

            target_height = int((self.target_width / original_width) * original_height)
            scaled_image = image.scaled(
                self.target_width,
                target_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            pixmap = QPixmap.fromImage(scaled_image)

            # 发射信号，携带 key, pixmap 和 target_dict
            self.signals.pixmap_loaded.emit(self.key, pixmap, self.target_dict)
            # print('信号发射!')

        except Exception as e:
            self.signals.log_message.emit(
                f"[Error] Processing '{self.image_path}': {e}"
            )
        finally:
            # 无论成功与否，都发出 finished 信号
            # print('finishi了喵')
            self.signals.finished.emit()


# --- 任务管理器 ---
class ImageLoaderApp(QObject):  # 继承 QObject 以支持信号
    # 定义一个总的完成信号
    all_tasks_finished = pyqtSignal()

    def __init__(self):
        super().__init__()  # 调用父类 QObject 的初始化
        self.todo_list = []  # 存储 (image_path, key, target_dict) 元组
        self.threadpool = QThreadPool()
        self.total_tasks = 0
        self.completed_tasks = 0
        self.active_workers = set()  # 使用集合存储，避免重复
        # print(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")

    def add_task(self, image_path, key, target_dict, width):
        """添加一个待处理任务"""
        self.todo_list.append((image_path, key, target_dict, width))
        # print(f"Task added: {image_path} -> {key}")

    def start_processing(self):
        """启动所有已添加的任务"""
        self.total_tasks = len(self.todo_list)
        # print(f"self.total_tasks={self.total_tasks}")
        self.completed_tasks = 0

        if self.total_tasks == 0:
            self.all_tasks_finished.emit()
            return

        self.threadpool.setMaxThreadCount(
            min(8, self.threadpool.maxThreadCount())
        )  # 可选：限制最大线程数

        # 清空上一次可能残留的引用
        self.active_workers.clear()
        for image_path, key, target_dict, width in self.todo_list:
            worker = ImageLoaderWorker(image_path, key, target_dict, width)
            finished_slot = lambda w=worker: self._on_single_task_finished(
                w
            )  # w=worker 是捕获当前 worker
            worker.signals.finished.connect(finished_slot)
            worker.signals.pixmap_loaded.connect(self._store_pixmap)  # 连接存储信号
            worker.signals.log_message.connect(self._log_message)  # 连接日志信号 (可选)

            self.active_workers.add(worker)
            self.threadpool.start(worker)

        # 清空 todo_list，为下一次使用做准备
        self.todo_list.clear()

    def _on_single_task_finished(self, worker):
        """内部槽函数：处理单个任务完成"""
        self.completed_tasks += 1
        self.active_workers.discard(worker)  # discard 不会抛出异常如果 worker 不存在
        # print(f"Task finished. Progress: {self.completed_tasks}/{self.total_tasks}")
        # 发射进度信号
        self.progress.emit(self.completed_tasks, self.total_tasks)

        if self.completed_tasks >= self.total_tasks:
            # print("All tasks finished!")
            self.all_tasks_finished.emit()  # 发射总完成信号

    def _store_pixmap(self, key, pixmap, target_dict):
        """内部槽函数：将 pixmap 存储到指定的字典中"""
        # print(f"Storing pixmap for key '{key}' into target dict.")
        self.active_workers.clear()
        target_dict[key] = pixmap
        # print(target_dict)

    def _log_message(self, message):
        """内部槽函数：处理日志消息 (可选)"""
        print(message)

    # 如果需要从 ImageLoaderApp 外部连接进度信号，可以在这里定义
    progress = pyqtSignal(int, int)  # (completed, total)
