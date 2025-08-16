from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QStackedWidget,
    QFrame,
    QLabel,
    QGridLayout,
    QToolTip,
    QCompleter,
)
from qframelesswindow import FramelessWindow, StandardTitleBar
from PyQt5.QtCore import Qt, QUrl, QTimer, QMargins, QStringListModel
from PyQt5.QtGui import (
    QGuiApplication,
    QDesktopServices,
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QFontDatabase,
)
from qfluentwidgets import (
    PushButton,
    LineEdit,
    ComboBox,
    EditableComboBox,
    FluentWindow,
    Flyout,
    InfoBarIcon,
    HorizontalSeparator,
    NavigationInterface,
    NavigationItemPosition,
    FlowLayout,
    ElevatedCardWidget,
    CaptionLabel,
    BodyLabel,
    ImageLabel,
    VerticalSeparator,
    ToolTipFilter,
    ToolTipPosition,
    SmoothScrollArea,
)
from PyQt5.QtCore import Qt
from dependences.consts import *


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
        self.cbb.setStyleSheet(get_comboBox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)
        # print(style)

    def set_content(self, new_content):
        self.cbb.clear()
        self.cbb.addItems(new_content)

    def get_content(self):
        return self.cbb.currentText()

    def bind_react_click_func(self, func):
        self.cbb.currentTextChanged.connect(func)


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
        self.cbb.setStyleSheet(get_comboBox_style(**cbb_style))
        self.editor_layout.addWidget(self.cbb)
        # print(style)
        # 初始化补全模型QAbstractItemModel
        self.song_name_completer = QStringListModel(SONG_NAME_LIST)
        self.composer_completer = QStringListModel(COMPOSER_LIST)
        self.charter_completer = QStringListModel(CHARTER_LIST)
        self.drawer_completer = QStringListModel(DRAWER_NAME_LIST)

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


class button(PushButton):

    def __init__(self, text: str, style: dict[str, str] = {}):
        super().__init__()
        self.setText(text)  # 设置按钮文本
        self.setStyleSheet(get_button_style(**style))

    def bind_click_func(self, func):  # 绑定按钮对应功能
        self.clicked.connect(func)


class label(QLabel):
    def __init__(self, text: str, style: dict[str, str] = {}):
        super().__init__()
        self.setText(text)  # 设置文本内容
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


class song_info_card(ElevatedCardWidget):

    def __init__(
        self,
        imgpath: str,
        name: str,
        singal_rks: str,
        acc: str,
        level: str,
        diff: str,
        special_record_type: special_type = special_type.EMPTY,  # 决定标题要不要上色 是否ap/fc/没玩过
        score: int = None,  # 等级
        index: int = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.imgpath = imgpath
        font_id = QFontDatabase.addApplicationFont(EN_FONT1)
        en_font_family = DEFAULT_EN_FONT
        if font_id != -1:
            en_font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        chi_font_id = QFontDatabase.addApplicationFont(EN_FONT1)
        chi_font_family = DEFAULT_CN_FONT
        if chi_font_id != -1:
            chi_font_family = QFontDatabase.applicationFontFamilies(chi_font_id)[0]
        if index:
            self.setToolTip(
                f"""<span style="font-famliy: '{en_font_family}'; color: #3fe2ff; font-size: 20px;">NO.{index}</span>"""
            )
        self.installEventFilter(
            ToolTipFilter(self, showDelay=300, position=ToolTipPosition.TOP)
        )
        self.bg_img_path = SONG_CARD_BACKGROUND[diff]
        # --布局顶部曲名和评级--
        self.top_widget = QFrame(self)

        self.top_layout = QGridLayout(self.top_widget)  # 采用网格 控制中间的空白
        self.top_layout.setContentsMargins(0, 0, 0, 0)  # 不要边界
        self.top_layout.setSpacing(3)  # 设置控件之间的间距

        # 曲名
        name_text = f"""
        <html>
            <body>
                <span style="font-family: '{en_font_family}', '{chi_font_family}', '{DEFAULT_JP_FONT}'; font-size: 31px; color: #ffffff">{name}</span>
            </body>
        </html>"""
        self.song_name_label = body_label(
            name_text,
            self.top_widget,
        )
        self.song_name_label.setWordWrap(True)  # 允许曲名自动换行
        self.top_layout.addWidget(
            self.song_name_label, 0, 1, 1, 4
        )  # (行, 列, 行跨度, 列跨度)
        self.song_name_label.setAlignment(
            Qt.AlignCenter
        )  # 居中对齐 否则与评级图片高度不一致很难看

        # 评级图片
        is_fc = False
        if (
            special_record_type == special_type.FC
            or special_record_type == special_type.AP
        ):
            is_fc = True
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
        # 单曲rks
        rks_text = f"""
        <html>
            <body>
                <span style="font-family: '{en_font_family}'; font-size: 27px; color: #a7fffc">rks: </span>
                <span style="font-size: 26px;color: #ffffff">{singal_rks}</span>
            </body>
        </html>"""
        self.rks_label = body_label(
            rks_text,
            self.bottom_widget,
        )
        self.rks_label.setWordWrap(True)
        self.bottom_layout.addWidget(
            self.rks_label, 0, 0, 1, 1
        )  # (行, 列, 行跨度, 列跨度)
        # self.rks_label.setAlignment(Qt.AlignCenter)
        self.rks_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.rks_label.setContentsMargins(15, 0, 0, 0)

        # acc
        acc_text = f"""
        <html>
            <body>
                <span style="font-family: '{en_font_family}'; font-size: 27px; color: #a7fffc">acc: </span>
                <span style="font-size: 26px;color: #ffffff">{acc}%</span>
            </body>
        </html>"""
        self.acc_label = body_label(
            acc_text,
            self.bottom_widget,
        )
        self.acc_label.setWordWrap(True)
        self.bottom_layout.addWidget(
            self.acc_label, 0, 1, 1, 2
        )  # (行, 列, 行跨度, 列跨度)
        self.acc_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.acc_label.setContentsMargins(10, 0, 0, 0)

        # 定数
        level_text = f"""
        <html>
            <body>
                <span style="font-family: '{chi_font_family}'; font-size: 24px; color: #a7fffc">定数:</span>
                <span style="font-size: 26px; font-family: '{en_font_family}';color: #ffffff">{diff} </span>
                <span style="font-size: 28px;color: #ffffff">{level}</span>
            </body>
        </html>"""
        self.level_label = body_label(
            level_text,
            self.bottom_widget,
        )
        self.level_label.setWordWrap(True)
        self.bottom_layout.addWidget(
            self.level_label, 1, 0, 1, 1
        )  # (行, 列, 行跨度, 列跨度)
        self.level_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.level_label.setContentsMargins(15, 3, 0, 0)

        # 分数
        score_text = f"""
        <html>
            <body>
                <span style="font-family: '{chi_font_family}'; font-size: 23px; color: #a7fffc">分数:</span>
                <span style="font-size: 25px;color: #ffffff">{score}</span>
            </body>
        </html>"""
        self.score_label = body_label(
            score_text,
            self.bottom_widget,
        )
        self.score_label.setWordWrap(True)
        self.bottom_layout.addWidget(
            self.score_label, 1, 1, 1, 2
        )  # (行, 列, 行跨度, 列跨度)
        self.score_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.score_label.setContentsMargins(10, 3, 0, 0)

        self.top_layout.setColumnStretch(0, 1)
        self.top_layout.setColumnStretch(1, 1)
        self.top_layout.setColumnStretch(2, 1)
        self.top_layout.setColumnStretch(3, 1)
        self.top_layout.setColumnStretch(4, 1)
        self.top_layout.setRowStretch(0, 1)
        self.top_layout.setRowStretch(1, 1)

        # 主布局（垂直排列）
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(0)  # 取消默认间距
        self.vBoxLayout.addWidget(self.top_widget)
        self.vBoxLayout.addWidget(self.bottom_widget)

        # 设置固定尺寸
        self.setFixedSize(400, 198)
        self.setCursor(Qt.PointingHandCursor)  # 鼠标悬停时显示手型指针

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print("此处应跳转到查找页面查找对应歌曲并展开对应难度")
            self.clicked.emit()  # 需要先定义信号
        super().mousePressEvent(event)

    def paintEvent(self, event):
        """绘制背景图片（如果有）"""
        super().paintEvent(event)

        if self.imgpath:
            painter = QPainter(self)
            pixmap = QPixmap(self.imgpath).scaledToWidth(
                420, Qt.SmoothTransformation  # 平滑缩放
            )
            pixmap1 = QPixmap(self.bg_img_path).scaledToWidth(
                420, Qt.SmoothTransformation
            )
            painter.drawPixmap(self.rect(), pixmap)
            painter.drawPixmap(self.rect(), pixmap1)
            painter.end()


class folder(QWidget):
    def __init__(self, title="", parent=None, expend=False):
        super().__init__(parent)
        self.is_expanded = expend
        self.widgets = []
        self.title = title
        self.setMinimumHeight(265)
        self.setMinimumWidth(420)
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 标题栏 (可点击)
        self.title_btn = button(title)
        # self.title_btn.setIcon(FluentIcon.CHEVRON_RIGHT)  # 默认向右箭头
        self.title_btn.bind_click_func(self.toggle_expand)
        self.title_btn.setObjectName("folder")
        self.title_btn.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.title_btn)

        # 内容区域 (初始隐藏)
        self.content_frame = QFrame()
        self.main_layout.addWidget(self.content_frame)
        self.content_frame.setContentsMargins(0, 0, 0, 0)
        if not self.is_expanded:
            self.content_frame.hide()
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = SmoothScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 关键设置
        self.scroll_area.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        # 必须给内部的视图也加上透明背景样式
        self.content_frame.setStyleSheet("QWidget{background: transparent}")
        self.content_layout.addWidget(self.scroll_area)
        self.content_layout.setSpacing(0)
        if not self.is_expanded:
            self.scroll_area.hide()
        # 创建内容容器
        self.scroll_content_widget = QWidget()
        self.flow_layout = FlowLayout(self.scroll_content_widget)  # 使用流式布局
        self.flow_layout.setSpacing(0)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)

        # 设置滚动区域的内容
        self.scroll_area.setWidget(self.scroll_content_widget)
        if not self.is_expanded:
            self.scroll_content_widget.hide()

    def toggle_expand(self):
        """切换展开/折叠状态"""
        self.is_expanded = not self.is_expanded
        if not self.is_expanded:
            for i in self.widgets:
                i.hide()
            self.scroll_content_widget.hide()
            self.scroll_area.hide()
            self.content_frame.hide()
        else:
            self.content_frame.show()  # 按顺序！否则 折叠-展开 操作后滚动条就会被吃掉
            self.scroll_area.show()
            self.scroll_content_widget.show()
            for i in self.widgets:
                i.show()

    def add_widget(self, widget):
        """向内容区域添加控件"""
        self.widgets.append(widget)
        self.flow_layout.addWidget(widget)
        if not self.is_expanded:
            widget.hide()


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

    def get_all_condition(self):  # 组合并返回当前的所有限制条件
        attribution = self.attribution_choose_cbb.get_content()
        limit = self.limit_choose_cbb.get_content()
        limit_val = self.limit_val_cbb.get_content()
        return (attribution, limit, limit_val)
