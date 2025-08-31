"""
轻量级的 QListView + QAbstractListModel + QStyledItemDelegate 实现，用来替代在启动时为每条歌曲
创建大量 QWidget（song_info_card）带来的高耗费。此模块职责：

- 定义 SongItem 数据类：只保存每条记录需要的轻量字段（包括图片路径与可选 QPixmap）。
- 提供 SongListModel：QAbstractListModel 子类，保存 SongItem 列表并提供接口更新图片。
- 提供异步图片加载任务 ImageLoadTask（在后台线程读取并 scaled 为 QImage），并把结果通过信号发回主线程。
  主线程收到 QImage 后将其转换为 QPixmap 并更新模型（线程安全）。
- 提供 SongDelegate：在 QListView 内“画”每条歌曲卡片（无需为每条创建 QWidget）。
- 提供 SongListViewWidget：包含 QListView、SongListModel、SongDelegate，并实现 populate_from_save()
  (把原来的 get_save_data 构建 item 的逻辑放到这里) 与 build_card_for_row()（按需构造完整 song_info_card）的帮助函数。

集成注意：
- 需要在主程序（创建 QApplication 之后）导入并使用本模块。
- 若在项目其它地方（如 classes.py 的 paintEvent）期望使用 illustration_cache/song_card_background_cache，
  build_card_for_row 会尽可能把已加载的 QPixmap 注入 dependences.consts 模块内的相应字典（延续旧代码兼容性）。
- 异步加载：后台线程生成 QImage（线程安全），在主线程槽中用 QPixmap.fromImage 转换并缓存/更新模型。
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

from PyQt5.QtCore import (
    Qt,
    QSize,
    QAbstractListModel,
    QModelIndex,
    QVariant,
    QRunnable,
    QThreadPool,
    pyqtSignal,
    QObject,
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor, QPainter
from PyQt5.QtWidgets import QListView, QStyledItemDelegate, QWidget, QVBoxLayout

from dependences.consts import *

# -------------------------
# 自定义 role 常量（用于 model.data 查询）
# Qt.UserRole 开始的 role 用法便于在 model/view 中传递自定义数据
# -------------------------
ROLE_NAME = Qt.UserRole + 1
ROLE_COMBINE = Qt.UserRole + 2
ROLE_RKS = Qt.UserRole + 3
ROLE_ACC = Qt.UserRole + 4
ROLE_LEVEL = Qt.UserRole + 5
ROLE_DIFF = Qt.UserRole + 6
ROLE_SCORE = Qt.UserRole + 7
ROLE_COMPOSER = Qt.UserRole + 8
ROLE_CHAPTER = Qt.UserRole + 9
ROLE_DRAWER = Qt.UserRole + 10
ROLE_ILLU_PATH = Qt.UserRole + 11
ROLE_BG_PATH = Qt.UserRole + 12
ROLE_ILLU_PIXMAP = Qt.UserRole + 13
ROLE_BG_PIXMAP = Qt.UserRole + 14
ROLE_GROUPS = Qt.UserRole + 15
ROLE_TAGS = Qt.UserRole + 16
ROLE_COMMENT = Qt.UserRole + 17
ROLE_ADVICE = Qt.UserRole + 18


# -------------------------
# SongItem: 轻量数据容器（使用 dataclass 简化定义）
# - combine_name: 组合名称（唯一标识曲目）
# - diff: 难度（"EZ","HD","IN","AT"...）
# - name/composer/chapter/drawer: 展示用元信息
# - rks/acc/level/score: 统计数据
# - illustration_path / bg_path: 图片文件路径（磁盘上的文件）
# - groups/tags/comment: 用户自定义元数据
# - illustration_pixmap / bg_pixmap: 可选 QPixmap（加载完成后放入，便于 delegate 绘制）
# -------------------------
@dataclass
class SongItem:
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
    illustration_path: str
    bg_path: str
    groups: List[str]
    tags: List[str]
    comment: str
    illustration_pixmap: Optional[QPixmap] = None
    bg_pixmap: Optional[QPixmap] = None


# -------------------------
# SongListModel: QAbstractListModel 的轻量实现
# - 存储 SongItem 列表
# - 提供 add_item/get_item 方法
# - 提供 set_illustration / set_bg 用于在图片加载后更新对应行并发出 dataChanged
# -------------------------
class SongListModel(QAbstractListModel):

    def __init__(self, items: List[SongItem] = None):
        super().__init__()
        self._items = items or []

    def rowCount(self, parent=QModelIndex()):
        # 返回模型行数（必需实现）
        return len(self._items)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        # 返回给定 index 和 role 的数据
        if not index.isValid():
            return QVariant()
        item = self._items[index.row()]
        # 根据自定义 role 返回对应字段
        if role == ROLE_NAME:
            return item.name
        if role == ROLE_COMBINE:
            return item.combine_name
        if role == ROLE_RKS:
            return item.rks
        if role == ROLE_ACC:
            return item.acc
        if role == ROLE_LEVEL:
            return item.level
        if role == ROLE_DIFF:
            return item.diff
        if role == ROLE_SCORE:
            return item.score
        if role == ROLE_COMPOSER:
            return item.composer
        if role == ROLE_CHAPTER:
            return item.chapter
        if role == ROLE_DRAWER:
            return item.drawer
        if role == ROLE_ILLU_PATH:
            return item.illustration_path
        if role == ROLE_BG_PATH:
            return item.bg_path
        if role == ROLE_ILLU_PIXMAP:
            return item.illustration_pixmap
        if role == ROLE_BG_PIXMAP:
            return item.bg_pixmap
        if role == ROLE_GROUPS:
            return item.groups
        if role == ROLE_TAGS:
            return item.tags
        if role == ROLE_COMMENT:
            return item.comment
        if role == ROLE_ADVICE:
            return item.improve_advice
        # Qt.SizeHintRole: 告诉视图每行的推荐尺寸（delegate 或 view 可使用）
        if role == Qt.SizeHintRole:
            return QSize(400, 198)
        # 默认的 DisplayRole 返回 name（与老代码兼容）
        if role == Qt.DisplayRole:
            return item.name
        return QVariant()

    def add_item(self, item: SongItem):
        # 向模型尾部插入一行并发通知（重要：包裹 beginInsertRows/endInsertRows）
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()

    def get_item(self, row: int) -> Optional[SongItem]:
        # 安全获取行对应的 SongItem
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def set_illustration(self, row: int, pix: QPixmap):
        # 设置某行的 illustration_pixmap（图片加载完成后在主线程调用）
        item = self.get_item(row)
        if item:
            item.illustration_pixmap = pix
            idx = self.index(row)
            # dataChanged 要带上 role，这样 delegate 可以只处理图片变化
            self.dataChanged.emit(idx, idx, [ROLE_ILLU_PIXMAP])

    def set_bg(self, row: int, pix: QPixmap):
        # 设置某行的背景 pixmap
        item = self.get_item(row)
        if item:
            item.bg_pixmap = pix
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [ROLE_BG_PIXMAP])


# -------------------------
# 异步图片加载部分（在后台线程读取并缩放为 QImage）
# 说明：
# - QImage 是线程安全的，可在工作线程中创建并 scaled。
# - QPixmap 不是线程安全，必须在主线程创建或由主线程从 QImage 创建。
# - 所以这里在后台线程产生 QImage 并通过信号发回主线程，主线程再转换为 QPixmap。
# -------------------------
class _ImageLoaderSignals(QObject):
    # 信号：key（用于标识哪张图）、QImage、is_bg（表示是否为背景图）
    finished = pyqtSignal(str, QImage, bool)  # key, qimage, is_bg


class ImageLoadTask(QRunnable):
    """Load image from disk and scaled to width as QImage in background thread."""

    def __init__(self, key: str, path: str, width: int, is_bg: bool = False):
        super().__init__()
        self.key = key
        self.path = path
        self.width = int(width)
        self.is_bg = bool(is_bg)
        self.signals = _ImageLoaderSignals()

    def run(self):
        # 注意：run 在工作线程中执行
        img = QImage(self.path)
        if img.isNull():
            # 加载失败（格式不支持等）
            return
        # 在工作线程中进行缩放，返回 QImage（线程安全）
        scaled = img.scaledToWidth(self.width, Qt.SmoothTransformation)
        # 通过信号发回主线程；finished 的连接者应在主线程执行槽
        self.signals.finished.emit(self.key, scaled, self.is_bg)


def start_image_load(key: str, path: str, width: int, is_bg: bool, finished_slot):
    """
    工具函数：构造 ImageLoadTask 并提交到全局线程池
    - finished_slot: 主线程槽函数，用于接收 QImage 并转换为 QPixmap（安全）
    """
    task = ImageLoadTask(key, path, width, is_bg)
    # 连接信号（通过 queued connection 跨线程安全传递）
    task.signals.finished.connect(finished_slot)
    QThreadPool.globalInstance().start(task)


# 全局小型 pixmap 缓存：键为 (key, is_bg)，value 为 QPixmap
# 目的是避免重复从 QImage->QPixmap 的转换并重复保存相同 pixmap
_pixmap_cache: Dict[Tuple[str, bool], QPixmap] = {}


# -------------------------
# Delegate：负责在 QListView 中绘制每一行（即每个 song card 的外观）
# 优点：不创建 QWidget，绘制开销低，和 model 结合适合大量条目
# -------------------------
class SongDelegate(QStyledItemDelegate):
    """Draw a song card inline. Keep it light and fast."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 在 delegate 中预定义字体/颜色，避免每次 paint 都创建
        self.name_font = QFont("楷体", 16, QFont.Bold)
        self.meta_font = QFont("Sans Serif", 11)
        self.small_font = QFont("Sans Serif", 10)
        self.cyan = QColor("#a7fffc")
        self.white = QColor("#ffffff")
        self.shadow = QColor(0, 0, 0, 160)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        """
        核心绘制函数：在给定的 painter 与矩形内绘制整张卡片。
        关键步骤：
        - 绘制背景（优先使用 item.bg_pixmap）
        - 绘制插图（item.illustration_pixmap）
        - 在上面叠加半透明遮罩以增强文本可读性
        - 绘制标题、评级/定数信息与底部统计（rks/acc/score）
        """
        painter.save()
        rect = option.rect
        model: SongListModel = index.model()
        item = model.get_item(index.row())

        # 背景：优先绘制已加载的背景 pixmap，否则填充一个深色矩形
        if item and item.bg_pixmap:
            painter.drawPixmap(rect, item.bg_pixmap)
        else:
            painter.fillRect(rect, QColor(30, 30, 30))

        # 插图（覆盖整个 rect，若已加载）
        if item and item.illustration_pixmap:
            painter.drawPixmap(rect, item.illustration_pixmap)

        # 覆盖一层半透明黑色以提升文字可读性
        # painter.fillRect(rect, QColor(0, 0, 0, 120))

        # 标题区域（左上）
        name_rect = rect.adjusted(12, 8, -120, -rect.height() // 2 + 10)
        painter.setFont(self.name_font)
        # 先画阴影效果：黑色偏移 1px
        painter.setPen(self.shadow)
        painter.drawText(
            name_rect.translated(1, 1), Qt.AlignLeft | Qt.TextWordWrap, str(item.name)
        )
        # 再画主文字
        painter.setPen(self.white)
        painter.drawText(name_rect, Qt.AlignLeft | Qt.TextWordWrap, str(item.name))

        # 右侧区域用于显示难度与定数（或图标）
        right_x = rect.right() - 110
        level_rect = rect.adjusted(right_x - rect.left(), 8, -10, -rect.height() + 88)
        painter.setFont(self.meta_font)
        painter.setPen(self.cyan)
        painter.drawText(level_rect, Qt.AlignCenter, f"{item.diff} {item.level}")

        # 底部信息（rks / acc / 分数）
        bottom_y = rect.bottom() - 48
        painter.setFont(self.meta_font)
        painter.setPen(self.cyan)
        painter.drawText(
            rect.left() + 12, bottom_y, 120, 24, Qt.AlignLeft, f"rks: {item.rks}"
        )
        painter.setPen(self.white)
        painter.drawText(
            rect.left() + 120, bottom_y, 120, 24, Qt.AlignLeft, f"acc: {item.acc}%"
        )
        painter.drawText(
            rect.left() + 260, bottom_y, 120, 24, Qt.AlignLeft, f"分数: {item.score}"
        )

        painter.restore()

    def sizeHint(self, option, index):
        # 与模型中 SizeHintRole 保持一致：建议每行高度 198，宽度 400
        return QSize(400, 198)


# -------------------------
# SongListViewWidget：封装 QListView、model、delegate，并提供 populate/build helpers
# -------------------------
class SongListViewWidget(QWidget):
    """
    - self.model: SongListModel 实例
    - self.view: QListView，使用 SongDelegate 绘制
    - _wait_map: 记录哪些 model 行在等待某张图片加载完成（键为 (key,is_bg)）
    - _pixmap_cache: 模块级缓存（见上）用于重用已创建的 QPixmap
    主要接口：
      - populate_from_save(save_dict, diff_map_result, cname_to_name, group_info, tag_info, comment_info)
          从存档数据填充 model 并触发图片异步加载
      - build_card_for_row(row, is_expanded=False)
          根据 model 行按需构建完整的 song_info_card（仅为单个需要详细展示的条目创建 widget）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化 model/view/delegate
        self.model = SongListModel()
        self.view = QListView()
        self.view.setModel(self.model)
        self.delegate = SongDelegate(self.view)
        self.view.setItemDelegate(self.delegate)
        # 视图细节，spacing 控制行间距，UniformItemSizes 可提升性能
        self.view.setSpacing(6)
        self.view.setUniformItemSizes(True)
        self.view.setVerticalScrollMode(QListView.ScrollPerPixel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # mapping (cache_key,is_bg) -> list of model 行索引 等待该图片加载
        # 这样多个行共享同一张图片时，只需加载一次
        self._wait_map = {}

    def _on_image_loaded(self, key: str, qimage: QImage, is_bg: bool):
        """
        主线程槽函数：接收工作线程发回的 QImage，转换为 QPixmap 并更新模型
        - key: 与 model 行关联的字符串（例如 f"{combine_name}_{diff}"）
        - qimage: 工作线程生成并缩放好的 QImage
        - is_bg: 是否为背景图（True 表示背景）
        行为：
        - 把 QPixmap 存入模块级 _pixmap_cache
        - 找到等待该图片的所有行并调用 model.set_illustration/set_bg 更新行数据
        - 清理 _wait_map 中的条目
        """
        if qimage is None:
            return
        # 将 QImage 转为 QPixmap（需在主线程执行，线程安全）
        pix = QPixmap.fromImage(qimage)
        _pixmap_cache[(key, is_bg)] = pix
        waiting_rows = self._wait_map.get((key, is_bg), [])
        for row in waiting_rows:
            if is_bg:
                self.model.set_bg(row, pix)
            else:
                self.model.set_illustration(row, pix)
        # 清理等待列表
        if (key, is_bg) in self._wait_map:
            del self._wait_map[(key, is_bg)]

    def _schedule_image_load_for_row(self, row: int, key: str, path: str, is_bg: bool):
        """
        安排某行所需图片的加载：
        - 先检查模块级 _pixmap_cache（是否已有 QPixmap）
        - 若已缓存则直接把 pixmap 写入 model（同步）
        - 否则把该行索引添加到 self._wait_map 的等待列表并提交 ImageLoadTask
        参数：
          - row: 模型行索引
          - key: 图片键（例如 f"{combine_name}_{diff}"）
          - path: 磁盘路径
          - is_bg: 是否为背景图
        """
        cache_key = (key, is_bg)
        if cache_key in _pixmap_cache:
            # 已有缓存，直接更新模型
            pix = _pixmap_cache[cache_key]
            if is_bg:
                self.model.set_bg(row, pix)
            else:
                self.model.set_illustration(row, pix)
            return
        # 记录该行在等这张图
        self._wait_map.setdefault(cache_key, []).append(row)
        # 启动后台加载（宽度硬编码为 420，若要可配置可改为常量/参数）
        start_image_load(key, path, 420, is_bg, self._on_image_loaded)

    def populate_from_save(
        self,
        save_dict: dict,
        diff_map_result: dict,
        cname_to_name: dict,
        group_info: dict,
        tag_info: dict,
        comment_info: dict,
        illustration_cache: dict[str, QPixmap],
    ):
        """
        从已解析的存档字典填充模型（等价于原来 get_save_data 中构建 song_info_card 的数据处理逻辑）
        - save_dict: decryptSave(...) 得到的结果（包含 "gameRecord" 等）
        - diff_map_result: difficulty 映射（combine_name -> { "EZ": val, "HD": val, ... }）
        - cname_to_name: combine_name -> (song_name, composer, drawer, {diff->chapter})
        - group_info/tag_info/comment_info: 项目的额外元数据字典
        过程：
         - 逐条遍历存档的 gameRecord，为每个 (combine_name, diff) 构建 SongItem 并 add_item 到 model
         - 对每个行调度插图与背景的异步加载（_schedule_image_load_for_row）
        """
        # 新建 model（以便刷新）
        self.model = SongListModel()
        self.view.setModel(self.model)
        row = 0
        # 遍历 save_dict["gameRecord"]，该结构来自你的存档反序列化逻辑
        for combine_name, all_diff_dic in save_dict["gameRecord"].items():
            for diffi, items in all_diff_dic.items():
                if diffi == "Legacy":
                    continue
                score = int(items["score"])
                acc = float(items["acc"])
                is_fc = True if items["fc"] == 1 else False
                level = float(diff_map_result[combine_name][diffi])
                singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
                acc = round(acc, 4)
                song_name, composer, drawer, chapter_dic = cname_to_name[combine_name]
                # illustration_path = ILLUSTRATION_PREPATH + combine_name + ".png"
                illustration_path = illustration_cache[combine_name]
                bg_path = SONG_CARD_BACKGROUND[diffi]
                groups = group_info.get(combine_name, "").split("`")
                tags = tag_info.get(combine_name, "").split("`")
                comment = comment_info.get(combine_name, {}).get(diffi, "")
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
                    illustration_path=illustration_path,
                    bg_path=bg_path,
                    groups=groups,
                    tags=tags,
                    comment=comment,
                )
                self.model.add_item(item)
                # 图像键：用 combine+diff 标识（若多行共享同一图可复用）
                key = f"{combine_name}_{diffi}"
                # 调度插图与背景的异步加载。加载完成后主线程槽会把 pixmap 写回 model
                # self._schedule_image_load_for_row(row, key, illustration_path, False)
                self._schedule_image_load_for_row(row, key, bg_path, True)
                row += 1

    def build_card_for_row(self, row: int, is_expanded: bool = False):
        """
        按需构建完整的 song_info_card（原来的 widget）并返回：
        - 仅在需要显示某一首歌曲的详细信息（例如编辑页面或 b27/phi3 布局）时调用。
        - 这样避免在启动时为所有歌曲都创建 QWidget。
        - 为兼容原有 paintEvent 使用的全局缓存（illustration_cache/song_card_background_cache），
          本函数会把已加载的 pixmap 注入到 dependences.consts 模块对应字典中（若存在）。
        返回：
          - song_info_card 实例 或 None（若 row 无效）
        """
        item = self.model.get_item(row)
        if not item:
            return None
        # 延迟导入 dependences.classes 中的 song_info_card 类，避免模块循环依赖
        from dependences.classes import song_info_card

        # 构造一个完整的 song_info_card（参数尽量与原构造器匹配）
        # 注意：SongItem 目前没有保存 is_fc，这里暂以 False 填充；若需要保存可扩展 SongItem
        # print(f"背景图片路径:{item.illustration_path}")
        card = song_info_card(
            item.illustration_path,
            item.name,
            item.rks,
            item.acc,
            item.level,
            item.diff,
            item.is_fc,
            item.score,
            None,  # index（可选）
            item.composer,
            item.chapter,
            item.drawer,
            is_expanded,
            item.combine_name,
            item.improve_advice,
        )

        # 为保持与旧代码兼容：某些地方（如 classes.main_info_card.paintEvent）可能从
        # dependences.consts.illustration_cache / song_card_background_cache 读取 pixmap。
        # 因此如果我们已经在 _pixmap_cache 中有对应 pixmap，就写入 consts 中的缓存字典。
        # 这样用旧方法绘制的 card.paintEvent 仍会找到 pixmap。
        from dependences import consts as _c

        # 如果 consts 上还未创建这些字典，先创建以避免 AttributeError
        if not hasattr(_c, "song_card_background_cache"):
            _c.song_card_background_cache = {}
        if not hasattr(_c, "illustration_cache"):
            _c.illustration_cache = {}

        # 在 _pixmap_cache 中以 (f"{combine}_{diff}", False/True) 作为键保存，
        # 这里尝试取出并注入 consts 的缓存字典
        pix_ill = _pixmap_cache.get((f"{item.combine_name}_{item.diff}", False))
        pix_bg = _pixmap_cache.get((f"{item.combine_name}_{item.diff}", True))
        if pix_ill:
            _c.illustration_cache[item.combine_name] = pix_ill
        if pix_bg:
            _c.song_card_background_cache[item.diff] = pix_bg

        # 返回构建好的 card；调用方负责把 card.left_func / right_func 等行为绑定上
        return card


# End of song_list_view_delegate.py
