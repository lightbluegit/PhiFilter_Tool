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
    QGraphicsScene,
    QGraphicsPixmapItem,
    QListView,
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
    QAbstractListModel,
    QModelIndex,
)
from PyQt5.QtGui import (
    QIcon,
    QColor,
    QPainter,
    QTextOption,
    QImage,
    QPainterPath,
    QPixmap,
)
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
from dataclasses import dataclass
from dependences.consts import *
import re

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
        # self.groups = set(GROUP_INFO.values())
        # self.comments = set()
        # for i in COMMENT_INFO.values():
        #     # print(f'i={i}')
        #     for key, val in i.items():
        #         self.comments.add(val)
        #         # print('val=',val)
        self.song_name_completer = QStringListModel(SONG_NAME_LIST)
        self.composer_completer = QStringListModel(COMPOSER_LIST)
        self.charter_completer = QStringListModel(CHARTER_LIST)
        self.drawer_completer = QStringListModel(DRAWER_NAME_LIST)
        # self.group_info_completer = QStringListModel(self.groups)
        # self.comment_info_completer = QStringListModel(self.comments)

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


# 多行文本(暂时无用)
class multiline_text(TextEdit):
    def __init__(self, text: str = "", parent: QWidget = None):
        super().__init__(parent)

        self.setText(text)
        self.setWordWrapMode(QTextOption.WordWrap)
        self.setAlignment(Qt.AlignVCenter)

    def set_text(self, text: str):
        self.setText(text)

    def get_plain_text(self):
        return self.toPlainText()


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
            # difference = get_song_card_bg(, self.width())

            # 绘制到整个矩形区域
            # print(f"种类是{type(self.imgpath)}, {self.imgpath}")
            painter.drawPixmap(QRect(0, 0, self.width(), self.height()), self.imgpath)
            painter.drawPixmap(
                QRect(0, 0, self.width(), self.height()), self.diff_bg_path
            )

            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # print("左点击了!")
            self.left_func()
            self.clicked.emit()  # 需要先定义信号
        super().mousePressEvent(event)


# 左侧有底板背景作为提示 右侧可以任意填充内容的控件 hint_and_frame_widget


class hint_and_frame_widget(QFrame):
    def __init__(self, title: str):
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


# 歌曲信息卡片
class song_info_card(QWidget):
    def __init__(  # 更改入参的时候记得把.copy方法的参数也改掉喵
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

        composer_content_elm = BodyLabel(self.composer)
        composer_content_elm.setStyleSheet(self.label_style)
        composer_content_elm.setWordWrap(True)
        composer_label = hint_and_frame_widget("曲师:")
        composer_label.add_widget(composer_content_elm)
        self.flow_layout.addWidget(composer_label)

        chapter_content_elm = BodyLabel(self.chapter)
        chapter_content_elm.setStyleSheet(self.label_style)
        chapter_content_elm.setWordWrap(True)
        chapter_label = hint_and_frame_widget("谱师:")
        chapter_label.add_widget(chapter_content_elm)
        self.flow_layout.addWidget(chapter_label)
        try:
            drawer_content_elm = BodyLabel(self.drawer)
        except:
            print(f"歌曲{self.name}出错了喵 得到的是{self.drawer}")
        drawer_content_elm.setStyleSheet(self.label_style)
        drawer_content_elm.setWordWrap(True)
        drawer_label = hint_and_frame_widget("画师:")
        drawer_label.add_widget(drawer_content_elm)
        self.flow_layout.addWidget(drawer_label)

        self.group_label = hint_and_frame_widget("分组:")
        self.flow_layout.addWidget(self.group_label)

        self.comment_label = hint_and_frame_widget("简评:")
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
        )

    def set_edited_info(self, group: list[str], comment: str):
        if not self._expanded_created:
            self._ensure_expanded_created()

        # 批量添加时关闭更新以避免多次重绘
        self.scroll_content_widget.setUpdatesEnabled(False)

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

    def __init__(self, index: int, filter_obj_list, flow_layout):
        super().__init__()
        self.logical_cbb: combobox = None
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
        """根据用户切换的属性更新补全器和可选择的值"""
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

        elif self.attribution_choose_cbb.get_content() == "简评":
            self.limit_choose_cbb.set_content(["包含", "不包含"])
            self.limit_val_cbb.set_content(self.limit_val_cbb.comments)
            self.limit_val_cbb.set_completer(self.limit_val_cbb.comment_info_completer)

    def input_val_check(self, attribution, value) -> tuple[bool, str]:
        if attribution == "acc":
            print(f"val={value}")
            if not value:
                return (False, None)
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
                print("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            acc = float(value)
            if acc > 100:  # 范围限定
                print("acc不可能大于100喵")
                return (False, None)
            if acc < 0:
                print("acc不可能小于0喵")
                return (False, None)
            return (True, value)

        elif attribution in ("单曲rks", "定数"):
            if not value:
                return (False, None)
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
                print("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            singal_rks = float(value)
            if singal_rks > MAX_LEVEL:  # 范围限定
                print(
                    f"当前最高定数为{MAX_LEVEL}喵 {attribution}不可能高于{MAX_LEVEL}喵"
                )
                return (False, None)
            if singal_rks < 0:
                print(f"{attribution}不可能小于0喵")
                return (False, None)
            return (True, value)

        elif attribution == "得分":
            if not value:
                return (False, None)
            pattern = r"\d+"
            match_results = re.fullmatch(pattern, value)  # 完全匹配 '数字.数字' 的形式
            if match_results is None:
                print("无法匹配")
                return (False, None)
            match_results = match_results.group()  # 获取匹配后的值
            # print(match_results)
            score = int(value)
            if score > 1000000:  # 范围限定
                print("最高分只有100w喵 太高了啦")
                return (False, None)
            if score < 0:
                print("得分不可能小于0喵")
                return (False, None)
            return (True, value)

        elif attribution == "评级":
            if value not in ("F", "C", "B", "A", "S", "V", "蓝V", "phi"):
                print(f"评级不可能是{value}喵")
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
        check_result = self.input_val_check(attribution, limit_val)
        if check_result[0] == False:
            return None
        limit_val = check_result[1]
        return (attribution, limit, limit_val)


# 可以多选的下拉菜单(暂时用不到)
class multi_check_combobox(EditableComboBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_items = []
        self.setMaximumWidth(300)
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
            if len(text) > 35:
                display_text = text[:32] + "..."
            else:
                display_text = text
            checkbox = CheckBox(display_text)
            checkbox.setObjectName("comboCheckBox")
            checkbox.setToolTip(display_text)
            self.list_widget.setItemWidget(item, checkbox)
            item.setSizeHint(checkbox.sizeHint())  # 确保正确的高度

    def get_selected_items(self):
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

    def set_selected_items(self, items: list[str]):
        """设置选中项"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            checkbox = self.list_widget.itemWidget(item)
            checkbox.setChecked(checkbox.text() in items)

    def clear(self):
        """清除所有选项"""
        self.list_widget.clear()
        self._selected_items = []
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
            # print("左点击了!")
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
        # print('run了', self.key)
        image = QImage(self.image_path)
        if image.isNull():
            self.signal.finished.emit()
            print(f"{self.image_path}地址的图片不存在哦~")
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
        # print("finish了喵")


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
        # print('开始处理任务')

    def add_task(
        self, image_path: str, key: str, target_dict: dict[str, QPixmap], width: int
    ):
        """添加一个待处理任务"""
        self.todo_list.append((image_path, key, target_dict, width))
        # if key == '雪降り雪が降っている.AiSSw夜輪ft結月ゆかり': # 检查特定曲名是否正常运行
        #     print(f"接入任务: {image_path} -> {key}")

    def start_processing(self):
        """启动所有已添加的任务"""
        self.total_tasks = len(self.todo_list)
        # print(f"总任务量={self.total_tasks}")
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
            # print(f"{self.total_tasks}个任务完成了!")
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
    # groups: List[str]
    # comment: str
    bg_pixmap: QPixmap | None = None


# 定义模型 为 QListView 提供数据 用于管理 SongItem 列表 负责将数据提供给视图 (如 QListView)。
class SongListModel(QAbstractListModel):

    def __init__(self, items: list[SongItem] = None):
        super().__init__()
        self.items = [] if items is None else items

    def rowCount(
        self, parent=QModelIndex()
    ):  # 第二个参数虽然用不到 但是必须写 否则会报错 未知来源
        """(必需实现)返回模型的行数"""
        return len(self.items)

    def add_item(self, item: SongItem):
        # 向模型尾部插入一行
        self.beginInsertRows(QModelIndex(), len(self.items), len(self.items))
        self.items.append(item)
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
        # group_info: dict,
        # comment_info: dict,
        illustration_cache: dict[str, QPixmap],
        bg_cache: dict[str, QPixmap],
    ):
        """从存档中构建数据"""
        self.model = SongListModel()
        self.view.setModel(self.model)
        row = 0
        for combine_name, all_diff_dic in save_dict["gameRecord"].items():
            for diffi, items in all_diff_dic.items():
                if diffi == "Legacy":
                    continue
                score = int(items["score"])
                acc = float(items["acc"])
                is_fc = True if items["fc"] == 1 else False
                try:
                    level = float(diff_map_result[combine_name][diffi])
                except:
                    print(f"{combine_name}没有{diffi}难度哦 再看看文件是否更新了")
                singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
                acc = round(acc, 4)
                song_name, composer, drawer, chapter_dic = cname_to_name[combine_name]
                illustration = illustration_cache[combine_name]
                bg_path = bg_cache[diffi]
                # groups = group_info.get(combine_name, "").split("`")
                # comment = comment_info.get(combine_name, {}).get(diffi, "")
                # 构造 SongItem，并加入 model
                item = SongItem(
                    combine_name=combine_name,
                    diff=diffi,
                    name=song_name,
                    rks=singal_rks,
                    acc=acc,
                    level=level,
                    score=score,
                    improve_advice=None,
                    is_fc=is_fc,
                    composer=composer,
                    chapter=chapter_dic[diffi],
                    drawer=drawer,
                    illustration=illustration,
                    bg_path=bg_path,
                    # groups=groups,
                    # comment=comment,
                )
                self.model.add_item(item)
                row += 1

    def build_card(self, row: int, is_expanded: bool = False):
        """根据存储的数据构建卡片并返回"""
        item = self.model.get_item(row)
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
        )

        return card
