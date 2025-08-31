from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QStackedWidget,
    QDesktopWidget,
    QSizePolicy,
    QSpacerItem,
)
from qframelesswindow import FramelessWindow, StandardTitleBar
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import (
    QGuiApplication,
    QIcon,
    QPixmap,
    QDesktopServices,
)
import requests
from qfluentwidgets import (
    NavigationInterface,
    NavigationItemPosition,
    FlowLayout,
    SmoothScrollArea,
    InfoBar,
    SwitchButton,
    InfoBarPosition,
    AvatarWidget,
    HorizontalSeparator,
    SplashScreen,
    ProgressRing,
)
from qfluentwidgets import FluentIcon as FIF
import sys
import heapq  # 算rks组成
import os
from typing import Any, List, Tuple, Dict
import pandas as pd
from datetime import datetime
from math import sqrt


# 设置高 DPI 渲染策略，保证在高分辨率屏幕上界面清晰
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
# 启用高 DPI 缩放并使用高分辨率 pixmap
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
#! 先创建 QApplication 实例再写窗口 否则初始化缓存图片的时候会失败
app = QApplication(sys.argv)

from dependences.classes import *
from dependences.get_play_data import *
from dependences.song_list_view_delegate import (
    SongListViewWidget,
    ROLE_COMBINE,
    ROLE_DIFF,
    SongItem,
)


class MainWindow(FramelessWindow):

    def __init__(self):
        super().__init__()

        # ---------- 初始化各种变量 ----------
        self.tt = datetime.now()
        self.avatar = ""  # 存放用户头像文件名
        self.user_name = ""  # 存放用户ID
        self.token = ""  # 存放用户 session_token
        self.save_dict = {}  # 云存档解析后的字典数据
        self.total_rks = 0  # rks未/30之前得到的值 用于计算某个歌曲是否能推分
        self.widgets: dict[str, dict] = {}
        """self.widgets[页面名称][页面控件名称]=控件"""

        self.b27: List[Tuple[float, Tuple[str, Any]]] = []
        """self.b27 = (单曲rks,(组合名称, acc,   定数, 难度, 分数, 是否fc, 处于哪一行))"""

        self.phi3: List[Tuple[float, Tuple[str, Any]]] = []
        """self.phi3 = (单曲rks,(组合名称, acc,   定数, 难度, 分数, 是否fc, 处于哪一行))"""

        self.cname_to_name: dict[str, Tuple[str, str, str, dict]] = {}
        """
        self.cname_to_name[组合名称] = (
            正常名称,
            曲师名称,
            画师名称,
            {"EZ": EZ难度谱师, "HD": HD难度谱师, "IN": IN难度谱师}
        )
        """

        self.all_song_card: dict[str, dict[str, int]] = {}
        """self.all_song_card[组合曲名][难度]=歌曲卡片控件"""

        self.illustration_cache: dict[str, QPixmap] = {}
        self.illustration_cache_process = None

        self.page_bg_cache: dict[str, QPixmap] = {}
        self.page_icon_cache: dict[str, QPixmap] = {}

        self.home_page_tips: list[str] = [
            "这里是主页 有各种小工具哦~",
            "鼠标放在卡片底端的文字上可以展开详细信息 试试吧",
        ]

        # 3. 显示启动屏幕
        self.splash_screen = QWidget()
        self.splash_screen.setFixedSize(self.width(), self.height())
        open_layout = QGridLayout(self.splash_screen)
        self.ring = ProgressRing()
        self.ring.setAlignment(Qt.AlignCenter)
        self.ring.setTextVisible(True)
        self.ring.setFixedSize(130, 130)
        self.ring.setStrokeWidth(10)
        open_layout.addWidget(self.ring, 1, 1, 1, 1)

        self.splash_screen.show()

        # self.font_family = {}
        # ---------- 窗口设置 ----------
        # 设置窗口标题
        self.setTitleBar(StandardTitleBar(self))
        self.titleBar.setTitle("PhiFilter Tool")
        self.titleBar.titleLabel.setStyleSheet(
            """
            font-size: 30px;
            font-family: "Segoe UI";
        """
        )
        self.setWindowTitle("PhiFilter Tool")  # 设置窗口标题
        self.resize(950, 800)  # 默认窗口大小
        # 将窗口居中显示
        screen = QDesktopWidget().screenGeometry()
        pos_x = (screen.width() - self.width()) // 2
        pos_y = (screen.height() - self.height()) // 2
        self.move(pos_x, pos_y)

        # ---------- 主区域 ----------
        self.widgets["basepage"] = {}
        main_layout = QHBoxLayout(self)
        self.widgets["basepage"]["main_layout"] = main_layout
        main_layout.setContentsMargins(
            0, self.height() // 20, 0, 0
        )  # 顶部留出距离 不然会遮住关闭按钮
        main_layout.setSpacing(0)

        # 导航栏
        navigation_interface = NavigationInterface(self)
        self.widgets["basepage"]["navigation_interface"] = navigation_interface
        main_layout.addWidget(navigation_interface)
        navigation_interface.setExpandWidth(200)  # 设置导航展开宽度

        content_widget = QStackedWidget(self)
        self.widgets["basepage"]["content_widget"] = content_widget
        main_layout.addWidget(content_widget, 1)

        if os.path.exists(TOKEN_PATH):
            try:
                with open(TOKEN_PATH, "r") as token_file:
                    self.token = token_file.readline().strip()
            except Exception:
                pass

        self.generate_cname_to_name_info()
        self.preinit()
        # 后续的init的逻辑在 check_preinit_finished 里面 因为需要并行加载完成

    def preinit(self):
        # 模拟两个不同的存储字典
        self.illustration_cache = {}

        # 创建 ImageLoaderApp 实例
        self.loader = ImageLoaderApp()

        # --- 添加任务 ---
        # 假设这些图片文件存在
        for combine_namei in COMBINE_NAME:
            self.loader.add_task(
                rf"{ILLUSTRATION_PREPATH}{combine_namei}.png",
                combine_namei,
                self.illustration_cache,
                400,
            )
        # print(f'待办任务{self.loader.todo_list}')
        # --- 连接信号 (可选，用于获取状态) ---
        self.loader.add_task(
            self.get_acg_image(ACG_IMAGE_URL, "主页背景"),
            "home",
            self.page_bg_cache,
            self.width(),
        )
        self.loader.add_task(
            self.get_acg_image(ACG_IMAGE_URL, "编辑页背景"),
            "edit",
            self.page_bg_cache,
            self.width(),
        )
        self.loader.add_task(
            self.get_acg_image(ACG_PPIMAGE_URL, "rks组成图背景"),
            "rks组成图背景",
            self.page_icon_cache,
            250,
        )
        self.loader.add_task(
            self.get_acg_image(ACG_IMAGE_URL, "账号页背景"),
            "account",
            self.page_bg_cache,
            250,
        )
        self.ring.setRange(0, len(self.loader.todo_list))
        self.ring.setValue(0)
        self.loader.all_tasks_finished.connect(self.on_all_finished)
        self.loader.progress.connect(self.update_open_page)

        # --- 启动处理 ---
        # print("Starting image processing...")
        self.loader.start_processing()

    def on_all_finished(self):
        # print("\n--- All Tasks Completed ---")
        # print(f"Cache A: {self.illustration_cache}")
        self.song_list_widget = SongListViewWidget()

        # ---------- 如果有 token，即刻拉取云存档并设置头像 ----------
        if self.token:
            self.get_save_data()
            try:
                self.avatar = self.save_dict["user"]["avatar"]
            except Exception:
                pass

        self.init_all_pages()
        self.init_navigation()
        if self.token:
            self.switch_to(self.home_page)
        else:
            self.switch_to(self.account_page)

        self.splash_screen.close()
        self.show()

        end_time = datetime.now()
        time_difference = end_time - self.tt

        total_seconds = time_difference.total_seconds()
        seconds = int(total_seconds % 60)
        microseconds = time_difference.microseconds

        print(f"预处理用时:{seconds:02d}s.{microseconds:06d}")

    def update_open_page(self):
        self.ring.setValue(self.loader.completed_tasks)

    # ------------------ Core data loading / mapping ------------------
    def generate_cname_to_name_info(self):
        """读取 info.tsv 并构建 self.cname_to_name 信息"""

        df = pd.read_csv(
            INFO_PATH,
            sep="\t",
            header=None,
            encoding="utf-8",
            names=[
                "combine_name",
                "song_name",
                "composer",
                "drawer",
                "EZchapter",
                "HDchapter",
                "INchapter",
                "ATchapter",
                "Legendchapter",
            ],
        )
        df = df.fillna("")
        for _, row in df.iterrows():
            combine_name = row["combine_name"]
            song_name = row["song_name"]
            composer = row["composer"]
            drawer = row["drawer"]
            EZchapter = row["EZchapter"]
            HDchapter = row["HDchapter"]
            INchapter = row["INchapter"]
            ATchapter = row["ATchapter"]
            self.cname_to_name[combine_name] = (
                song_name,
                composer,
                drawer,
                {"EZ": EZchapter, "HD": HDchapter, "IN": INchapter},
            )
            if ATchapter:
                self.cname_to_name[combine_name][3]["AT"] = ATchapter

    def get_save_data(self):
        try:
            with PhigrosCloud(self.token) as cloud:
                summary = cloud.getSummary()
                # print(f'你的summary是{summary}')
                self.user_name = cloud.getNickname()
                # print(f"你的名字是{self.user_name}")
                save_data = cloud.getSave(summary["url"], summary["checksum"])
                save_dict = unzipSave(save_data)
                save_dict = decryptSave(save_dict)
                save_dict = formatSaveDict(save_dict)
                self.save_dict = save_dict
                # print(f'存档文件是这个喵{save_dict}')
        except:
            # InfoBar.warning(
            #     title="连接失败",
            #     content="读取信息失败 请稍后重试",
            #     orient=Qt.Horizontal,
            #     isClosable=True,
            #     position=InfoBarPosition.TOP,
            #     duration=3000,
            #     parent=window,
            # )
            return

        df = pd.read_csv(
            DIFFICULTY_PATH,
            sep="\t",
            header=None,
            encoding="utf-8",
            names=["song_name", "EZ", "HD", "IN", "AT"],
        )
        df = df.fillna("")  # 用空字符串替换 NaN
        diff_map_result: Dict[str, Dict[str, str]] = {}
        for _, row in df.iterrows():
            name = row["song_name"]
            diff_map = {"EZ": row["EZ"], "HD": row["HD"], "IN": row["IN"]}
            if row["AT"]:
                diff_map["AT"] = row["AT"]
            diff_map_result[name] = diff_map

        # 使用委托式视图填充 model：效率高，避免创建大量 QWidget
        self.song_list_widget.populate_from_save(
            self.save_dict,
            diff_map_result,
            self.cname_to_name,
            GROUP_INFO,
            TAG_INFO,
            COMMENT_INFO,
            self.illustration_cache,
        )

        self.all_song_card = {}
        model = self.song_list_widget.model
        for row in range(model.rowCount()):
            idx = model.index(row)
            combine = model.data(idx, ROLE_COMBINE)
            diff = model.data(idx, ROLE_DIFF)
            if combine not in self.all_song_card.keys():
                self.all_song_card[combine] = {}
            self.all_song_card[combine][diff] = row

        # print("get_save_data 用时", time.time() - times, "s")

    # ------------------ UI pages init (kept consistent) ------------------
    def init_all_pages(self):
        self.home_page = self.init_homepage()
        self.home_page.setObjectName("home_page")

        self.account_page = self.init_account_page()
        self.account_page.setObjectName("account_page")

        self.place_b27_phi3_page = self.init_place_b27_phi3_page()
        self.place_b27_phi3_page.setObjectName("place_b27_phi3_page")

        self.search_page = self.init_search_page()
        self.search_page.setObjectName("search_page")

        self.edit_info_page = self.init_edit_info_page()
        self.edit_info_page.setObjectName("edit_info_page")

    def init_navigation(self):
        """把导航项（主页、rks组成页、搜索、编辑等）添加到 NavigationInterface"""
        navigation_interface: NavigationInterface = self.widgets["basepage"][
            "navigation_interface"
        ]

        navigation_interface.addItem(
            routeKey=self.home_page.objectName(),
            icon=FIF.HOME,  # FIF 是 qfluentwidgets 的 FluentIcon，表示图标
            text="主页",
            onClick=lambda: self.switch_to(self.home_page),
            position=(NavigationItemPosition.TOP),  # 放在顶部（枚举）
        )

        navigation_interface.addItem(
            routeKey=self.place_b27_phi3_page.objectName(),
            icon=(FIF.ALBUM),
            text="rks组成页",
            onClick=lambda: self.switch_to(self.place_b27_phi3_page),
            parentRouteKey=self.home_page.objectName(),
        )

        navigation_interface.addSeparator()  # 添加分割线

        navigation_interface.addItem(
            routeKey="to_github",
            icon=FIF.GITHUB,
            text="项目主页",
            onClick=lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/lightbluegit/PhiFilter_Tool")
            ),
            position=(NavigationItemPosition.BOTTOM),
        )

        account_icon = QIcon(ICON_PREPATH + "account_icon.png")
        navigation_interface.addItem(
            routeKey=self.account_page.objectName(),
            icon=account_icon,
            text="账号管理",
            onClick=lambda: self.switch_to(self.account_page),
            position=(NavigationItemPosition.BOTTOM),
        )

        search_icon = QIcon(ICON_PREPATH + "search_icon.png")
        navigation_interface.addItem(
            routeKey=self.search_page.objectName(),
            icon=search_icon,
            text="搜索歌曲",
            onClick=lambda: self.switch_to(self.search_page),
        )

        navigation_interface.addItem(
            routeKey=self.edit_info_page.objectName(),
            icon=FIF.EDIT,
            text="编辑歌曲相关信息",
            onClick=lambda: self.switch_to(self.edit_info_page),
        )

        # 将 content_widget 的 currentChanged 事件与 on_current_interface_changed 绑定
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        content_widget.currentChanged.connect(self.on_current_interface_changed)
        content_widget.setCurrentIndex(0)  # 默认第 0 页（home_page）

    def on_current_interface_changed(self, index: int):
        """当 content_widget 的当前页面变化时，同步导航栏选中项"""
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        widget = content_widget.widget(index)
        navigation_interface = self.widgets["basepage"]["navigation_interface"]
        navigation_interface.setCurrentItem(widget.objectName())
        if widget.objectName() == "home_page":
            self.widgets["home_page"]["tip"].set_text(
                random.choice(self.home_page_tips)
            )

    # ------------------ Pages implementations ------------------
    def init_homepage(self) -> QWidget:
        """
        替换版 init_homepage：
        - 整合为“快捷功能”页（白色基调），使用卡片式视觉与网格按钮布局
        - 若后续要添加更多快捷功能，只需在 buttons 列表中加入元组 (label, iconpath, handler, enabled)
        直接将此函数替换你类中的 init_homepage 即可。
        """

        self.widgets["home_page"] = {}

        widget = bg_widget(self.page_bg_cache["home"])
        self.widgets["home_page"]["widget"] = widget

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(5)
        self.widgets["home_page"]["layout"] = layout

        # Header
        header_style = {
            "min_height": 50,
            "max_height": 50,
            # "max_width": widget.width() - 10,
            "font_color": (182, 204, 161, 1),
            "font_size": 40,
        }
        header = label("主页", header_style)
        header.adjustSize()
        layout.addWidget(header)

        # 水平分割线
        horizontal_separator = HorizontalSeparator()
        layout.addWidget(horizontal_separator)

        grid = QGridLayout()
        grid.setContentsMargins(0, 5, 0, 0)
        layout.addLayout(grid)

        title_style = {
            "font_size": 29,
            "min_width": 250,
            "max_width": 250,
            "max_height": 40,
            "min_height": 40,
        }
        content_style = {
            "font_size": 18,
            "min_width": 250,
            "max_width": 250,
            "max_height": 80,
            "min_height": 80,
        }

        generate_rsk_conpone_card = quick_function_card(
            self.page_icon_cache["rks组成图背景"],
            "生成rks组成图",
            "生成b27, phi3组成的文件夹 左键歌曲卡片可展开详细信息，右键跳转编辑页面",
            title_style,
            content_style,
        )
        generate_rsk_conpone_card.left_func = self.generate_b27_phi3
        layout.addWidget(generate_rsk_conpone_card)

        layout.addStretch(1)  # 顶上去

        tip_layout = QVBoxLayout()
        tip_layout.setAlignment(Qt.AlignLeft)
        layout.addLayout(tip_layout)
        tip_style = {
            "font_size": 22,
            "min_width": widget.width(),
            "max_width": widget.width(),
            "max_height": 21,
            "min_height": 21,
            "font_color": (138, 138, 138, 1),
        }
        tip = label(random.choice(self.home_page_tips), tip_style)
        self.widgets["home_page"]["tip"] = tip
        tip.setAlignment(Qt.AlignLeft)
        tip_layout.addWidget(tip)

        return widget

    def get_acg_image(self, url: str, img_save_name: str) -> str | None:
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            img_path = f"{BACKGROUND_IMG_PREPATH}{img_save_name}.png"
            with open(img_path, "wb") as f:
                f.write(response.content)

            return img_path  # 返回图片路径
        except Exception as e:
            print(f"获取失败: {e}")
            return None

    def is_improveable(
        self,
        song_item: SongItem,
        delta_rks: float,
        min_b27_rks: float,
        b27_dict: dict[str, list[str]],
    ) -> float | None:
        """
        判断某个歌曲的某个难度是否可以通过推acc让玩家信息中的rks发生变化

        入参:
            song_item: 存储歌曲信息的变量
            delta_rks: rks需要增加多少才能让玩家信息中的rks发生变化
            min_b27_rks: b27地板对应的单曲rks
            b27_dict: b27_dict[组合名称]=[该歌曲在b27中的难度(str) 组成的列表]

        返回:
            如果不能推分 返回None
            否则返回需要的达到acc
        """
        acc = float(song_item.acc)
        if int(acc) == 100:
            return None  # 已经满分的歌曲推不了分

        combine_name = song_item.combine_name
        level = float(song_item.level)
        diff = song_item.diff
        singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
        if combine_name in b27_dict.keys() and diff in b27_dict[combine_name]:  # 在b27
            need_rks = delta_rks + singal_rks
            need_acc = 45 * sqrt(need_rks / level) + 55
            if need_acc <= 100:  # 可以只靠这首歌在 b27 的表现让rks产生变化
                return int(need_acc * 100 + 0.9) / 100

            # 考虑推到ap之后能不能靠这首歌在 b27和phi3 中的表现让rks产生变化
            if level - singal_rks + level - float(self.phi3[-1][0]) >= delta_rks:
                return 100  # 推AP去吧
            else:
                return None  # AP也救不了你

        else:  # 不在b27
            need_rks = delta_rks + min_b27_rks
            need_acc = 45 * sqrt(need_rks / level) + 55
            if need_acc < 70:  # 不到70不计入rks 要上榜最少要70
                return 70
            if need_acc <= 100:  # 可以只靠这首歌在 b27 的表现让rks产生变化
                return int(need_acc * 100 + 0.9) / 100

            # 考虑推到ap之后能不能靠这首歌在 b27和phi3 中的表现让rks产生变化
            if level - min_b27_rks + level - float(self.phi3[-1][0]) >= delta_rks:
                return 100  # 推AP去吧
            else:
                return None  # AP也救不了你

    def generate_improve_rks_advise(self):
        model = self.song_list_widget.model

        """self.b27 = (单曲rks,(组合名称, acc, 定数, 难度, 分数, 是否fc))"""
        b27_dict = {}  # 存储phi3关键信息 b27_dict[组合名称]=['EZ', 'IN']
        min_b27_rks = MAX_LEVEL + 1
        for songi in self.b27:
            singal_rks, other = songi
            combine_name, acc, level, diff, score, is_fc, rowi = other
            if combine_name not in b27_dict.keys():
                b27_dict[combine_name] = []
            b27_dict[combine_name].append(diff)
            min_b27_rks = min(min_b27_rks, singal_rks)
        # print(b27_dict)

        player_now_rks = round(
            self.total_rks / (len(self.b27) + len(self.phi3)), 4
        )  # 当前玩家准确rks值
        show_rks = int(player_now_rks * 100 + 0.5) / 100  # 游戏页面展示的rks值
        delta_rks = (
            show_rks + 0.005 - player_now_rks
        )  # 0.005保证游戏页面四舍五入后rks出现提升
        # print(f"需要提升的rks是:{delta_rks * 30}")
        for row in range(model.rowCount()):  # 遍历所有歌曲
            item = model.get_item(row)
            if not item:
                continue
            diffi = item.diff
            if diffi == "Legacy":
                continue
            next_acc = self.is_improveable(item, delta_rks * 30, min_b27_rks, b27_dict)
            if next_acc is None:
                continue
            item.improve_advice = next_acc
            # print(f"{item.name},{item.diff}如果{item.acc}->{next_acc}就可以加分喽~")

    def init_place_b27_phi3_page(self) -> QWidget:
        """初始化 rks 组成页面"""
        self.widgets["place_b27_phi3_page"] = {}
        widget = QWidget()
        self.widgets["place_b27_phi3_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["place_b27_phi3_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(5, 0, 0, 0)
        main_layout.setSpacing(10)

        return widget

    def init_search_page(self) -> QWidget:
        """初始化搜索页面"""
        self.widgets["search_page"] = {}
        self.widgets["search_page"]["song_cards"] = []

        widget = QWidget()
        self.widgets["search_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["search_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ------------------ 筛选条件选择区域 -------------------
        scroll_area = SmoothScrollArea()
        self.widgets["search_page"]["scroll_area"] = scroll_area
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
        scroll_area.setFixedHeight(150)

        scroll_content_widget = QWidget()
        self.widgets["search_page"]["scroll_content_widget"] = scroll_content_widget

        flow_layout = FlowLayout(scroll_content_widget)
        self.widgets["search_page"]["flow_layout"] = flow_layout
        flow_layout.setSpacing(0)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area.setWidget(scroll_content_widget)

        # 初始化第一个 filter_obj并加入逻辑链接选项
        filter_obj_list: list = []
        self.widgets["search_page"]["filter_obj_list"] = filter_obj_list
        filter_elm = filter_obj(0, filter_obj_list, flow_layout)
        filter_elm.logical_cbb = combobox(
            ["", "并且(与)", "或者(或)"],
            "",
            {
                "max_width": "90",
                "min_width": "90",
                "min_height": 35,
                "max_height": 35,
                "font_size": 20,
            },
        )
        filter_elm.main_layout.addWidget(filter_elm.logical_cbb)
        filter_obj_list.append(filter_elm)
        flow_layout.addWidget(filter_elm)
        main_layout.addWidget(scroll_area)

        # ----------------- 确认筛选按钮区域 ---------------
        filter_confirm_widget = QWidget()
        self.widgets["search_page"]["filter_confirm_widget"] = filter_confirm_widget

        filter_confirm_layout = QHBoxLayout(filter_confirm_widget)
        self.widgets["search_page"]["filter_confirm_layout"] = filter_confirm_layout
        filter_confirm_layout.setContentsMargins(0, 0, 0, 0)

        filter_btn_style = {
            "min_height": 45,
            "max_height": 45,
            "font_size": 28,
        }
        filter_from_all_song_btn = button(
            "从所有歌曲中筛一遍", filter_btn_style, FILTER_ICON_PATH
        )
        self.widgets["search_page"][
            "filter_from_all_song_btn"
        ] = filter_from_all_song_btn
        filter_from_all_song_btn.set_icon_size(30, 30)
        filter_from_all_song_btn.bind_click_func(self.filter_from_all_song)
        filter_confirm_layout.addWidget(filter_from_all_song_btn)

        filter_from_previous_song_btn = button(
            "从结果中继续筛选", filter_btn_style, FILTER_AGAIN_ICON_PATH
        )
        self.widgets["search_page"][
            "filter_from_previous_song_btn"
        ] = filter_from_previous_song_btn
        filter_from_previous_song_btn.set_icon_size(30, 30)
        filter_from_previous_song_btn.bind_click_func(self.filter_from_previous_song)
        filter_confirm_layout.addWidget(filter_from_previous_song_btn)

        main_layout.addWidget(filter_confirm_widget)

        # ------------------------------ 搜索结果展示区 ----------------------------
        result_widget = QWidget()
        self.widgets["search_page"]["result_widget"] = result_widget
        result_widget.setStyleSheet("""background-color: #DCDCDC;""")

        result_layout = QVBoxLayout(result_widget)
        self.widgets["search_page"]["result_layout"] = result_layout
        result_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(result_widget, 1)

        # ---------------- 上层 分组/排序依据 ------------
        group_widget = QWidget()
        self.widgets["search_page"]["group_widget"] = group_widget
        result_layout.addWidget(group_widget)

        group_widget_layout = QHBoxLayout(group_widget)
        self.widgets["search_page"]["group_widget_layout"] = group_widget_layout
        group_widget_layout.setContentsMargins(0, 0, 20, 0)

        page_change_btn_style = {
            "max_width": 120,
            "min_width": 120,
            "min_height": 40,
            "max_height": 40,
            "font_size": 30,
        }
        # 重置按钮
        reset_page_btn = button("重置", page_change_btn_style, RESET_PATH)
        self.widgets["search_page"]["reset_page_btn"] = reset_page_btn
        reset_page_btn.bind_click_func(self.reset_filter_result)
        group_widget_layout.addWidget(reset_page_btn)

        # 排序顺序转换按钮
        sort_result_reverse_btn = SwitchButton()
        self.widgets["search_page"]["sort_result_reverse_btn"] = sort_result_reverse_btn
        sort_result_reverse_btn.setOffText("当前:从小到大")
        sort_result_reverse_btn.setOnText("当前:从大到小")
        sort_result_reverse_btn.setChecked(True)
        sort_result_reverse_btn.setStyleSheet(get_switch_button_style())
        sort_result_reverse_btn.label.setStyleSheet(
            f"""
            font-size: 26px;
            font-family: "{FONT_FAMILY["chi"]}";
            """
        )
        sort_result_reverse_btn.checkedChanged.connect(self.place_record)
        group_widget_layout.addStretch(1)
        group_widget_layout.addWidget(sort_result_reverse_btn)  # 右侧控件

        # 排序依据选择框
        group_by_style = {
            "min_height": 24,
            "max_height": 35,
            "max_width": 80,
            "min_width": 80,
        }
        group_by_hint_style = {
            "font_size": 26,
            "min_width": 110,
            "max_width": 110,
        }
        sort_by_list = ["无", "acc", "单曲rks", "得分", "定数"]
        sort_by = combobox(
            sort_by_list, "排序依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["sort_by"] = sort_by
        sort_by.bind_react_click_func(self.place_record)
        group_widget_layout.addWidget(sort_by)  # 右侧控件

        # 分组依据选择框
        group_by_list = [
            "无",
            "曲名",
            "曲师",
            "谱师",
            "画师",
            "难度",
            "评级",
            "分组",
            "标签",
        ]
        group_by = combobox(
            group_by_list, "分组依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["group_by"] = group_by
        group_by.bind_react_click_func(self.place_record)
        group_widget_layout.addWidget(group_by)  # 右侧控件

        # ---------------- 下层 卡片展示区 ------------
        result_display_scroll = SmoothScrollArea()
        self.widgets["search_page"]["result_display_scroll"] = result_display_scroll
        result_display_scroll.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        result_display_scroll.setWidgetResizable(True)

        result_display_flow_content = QWidget()
        self.widgets["search_page"][
            "result_display_flow_content"
        ] = result_display_flow_content

        result_display_flow = FlowLayout(result_display_flow_content)
        self.widgets["search_page"]["result_display_flow"] = result_display_flow
        result_display_flow.setSpacing(0)
        result_display_flow.setContentsMargins(0, 0, 0, 0)
        result_display_scroll.setWidget(result_display_flow_content)
        result_layout.addWidget(result_display_scroll)

        return widget

    def init_edit_info_page(self) -> QWidget:
        self.widgets["edit_info_page"] = {}
        widget = bg_widget(self.page_bg_cache["edit"])
        self.widgets["edit_info_page"]["widget"] = widget
        main_layout = QHBoxLayout(widget)
        self.widgets["edit_info_page"]["main_layout"] = main_layout

        # 左侧：显示区域
        display_widget = QWidget()
        display_layout = QVBoxLayout(display_widget)
        self.widgets["edit_info_page"]["display_layout"] = display_layout
        main_layout.addWidget(display_widget)

        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        display_layout.addItem(top_spacer)
        # print('缓存似',self.illustration_cache)
        # 添加示例 card 占位
        example_song = song_info_card(
            self.illustration_cache["introduction"],
            "introduction",
            "00.0000",
            "00.000",
            "00.0",
            "EZ",
            True,
            1000000,
            0,
            "曲师名称",
            "谱师名称",
            "画师名称",
            True,
            "introduction",
        )
        display_layout.addWidget(example_song)
        self.widgets["edit_info_page"]["song_info_card"] = example_song

        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        display_layout.addItem(bottom_spacer)
        self.widgets["edit_info_page"]["spacer"] = [bottom_spacer, top_spacer]

        # 右侧：编辑控件（分组、标签、简评）
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        self.widgets["edit_info_page"]["edit_layout"] = edit_layout
        main_layout.addWidget(edit_widget)

        group_label = label("分组:")
        group_ccb = CheckableComboBox()
        group_ccb.addItems(
            used_group
        )  # used_group 由 consts 读取 GROUP_PATH 得到的集合
        edit_layout.addWidget(group_label)
        edit_layout.addWidget(group_ccb)
        self.widgets["edit_info_page"]["group_ccb"] = group_ccb

        tag_label = label("标签:")
        tag_ccb = CheckableComboBox()
        tag_ccb.addItems(used_tag)
        edit_layout.addWidget(tag_label)
        edit_layout.addWidget(tag_ccb)
        self.widgets["edit_info_page"]["tag_ccb"] = tag_ccb

        comment_label = multiline_text()
        edit_layout.addWidget(comment_label)
        self.widgets["edit_info_page"]["comment_label"] = comment_label

        confirm_btn = button("保存更改", iconpath=SAVE_ICON_PATH)
        confirm_btn.set_icon_size(30, 30)
        confirm_btn.bind_click_func(self.save_user_edit)
        edit_layout.addWidget(confirm_btn)
        self.widgets["edit_info_page"]["confirm_btn"] = confirm_btn

        return widget

    # ------------------ Actions / Filtering / Placement ------------------
    def filter_from_all_song(self):
        """
        对全部歌曲执行筛选：
        - 从 model 中读取所有项（轻量 SongItem），计算 singal_rks 并生成 all_song_info 列表
        - 读取 UI 中的 filter_obj 列表并按逻辑（并且 / 或者）进行筛选
        - 将筛选结果放入 self.filter_result，并调用 place_record 执行布局（按需构建 widgets）
        """
        if not self.token:
            # 原始代码会弹 InfoBar 提示未登录，这里为了示例直接返回
            return

        # 重新读取难度表（也可以复用之前的 diff_map_result）

        self.tt = datetime.now()
        df = pd.read_csv(
            DIFFICULTY_PATH,
            sep="\t",
            header=None,
            encoding="utf-8",
            names=["song_name", "EZ", "HD", "IN", "AT"],
        )
        df = df.fillna("")
        diff_map = {
            row["song_name"]: {
                "EZ": row["EZ"],
                "HD": row["HD"],
                "IN": row["IN"],
                "AT": row["AT"] if row["AT"] else "",
            }
            for _, row in df.iterrows()
        }

        # 遍历 model，收集每一行的轻量信息（不创建任何 song_info_card）
        all_song_info = []
        model = self.song_list_widget.model
        for row in range(model.rowCount()):
            item = model.get_item(row)
            if not item:
                continue
            diffi = item.diff
            if diffi == "Legacy":
                continue
            score = int(item.score)
            is_fc = item.is_fc
            acc = float(item.acc)
            level = float(item.level)
            singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
            # 保留 row 以便后续根据需要构建完整 widget
            all_song_info.append(
                (item.combine_name, diffi, score, acc, level, is_fc, singal_rks, row)
            )

        # 获取 UI 上的 filter_obj 列表并读取逻辑连接方式（第一个筛选项的 logical_cbb）
        filter_obj_list: list = self.widgets["search_page"]["filter_obj_list"]
        logical_link = (
            filter_obj_list[0].logical_cbb.get_content() if filter_obj_list else ""
        )
        if not logical_link and len(filter_obj_list) > 1:
            # 存在多个筛选条件但未选择连接逻辑 -> 返回
            return
        if len(filter_obj_list) == 1:
            # 单个筛选项时忽略连接逻辑
            logical_link = ""

        # 根据连接类型初始化 self.filter_result：并且（交）则从全部开始减；否则使用集合并集行为
        self.filter_result = set()
        if logical_link == "并且(与)":
            self.filter_result = set(all_song_info)

        # 对每个筛选项应用 filte_with_condition（返回列表），并合成最终结果
        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            if conditioni is None:
                return
            if logical_link == "并且(与)":
                result_list = self.filte_with_condition(self.filter_result, conditioni)
                self.filter_result = set(result_list)
            else:
                result_list = self.filte_with_condition(all_song_info, conditioni)
                for resulti in result_list:
                    self.filter_result.add(resulti)
        # 布局筛选结果：在 place_record 中按需创建具体的 song_info_card 并插入 UI
        self.place_record()

    def filte_with_condition(self, song_info, condition: tuple):
        """
        根据单个筛选条件对输入 song_info（可为 list 或 set）执行筛选逻辑并返回匹配结果列表。
        condition: (attribution, limit, limit_val)
        attribution 为属性名（如 acc、单曲rks、得分...）
        limit 为比较操作（'大于','包含' 等）
        limit_val 为比较值（字符串形式）
        """
        (attribution, limit, limit_val) = condition
        result = []
        # 对某些文本类属性，先去空格并转小写以便做不区分大小写的比较
        if attribution in ("曲名", "曲师", "谱师", "画师", "标签", "分组", "简评"):
            limit_val = limit_val.replace(" ", "").lower()
        for songi in song_info:
            (combine_name, diffi, score, acc, level, is_fc, singal_rks, row) = songi
            song_name, composer, drawer, chapter_dic = self.cname_to_name[combine_name]
            groups = (
                GROUP_INFO.get(combine_name, "").split("`")
                if GROUP_INFO.get(combine_name)
                else []
            )
            tags = (
                TAG_INFO.get(combine_name, "").split("`")
                if TAG_INFO.get(combine_name)
                else []
            )
            comments = COMMENT_INFO.get(combine_name, {}).get(diffi, "")
            # 下面针对每种 attribution 使用对应比较逻辑（与原脚本保持一致）
            if attribution == "acc":
                if limit == "大于" and acc > float(limit_val):
                    result.append(songi)
                elif limit == "大于等于" and acc >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and acc < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and acc <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and acc == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and acc != float(limit_val):
                    result.append(songi)
            elif attribution == "单曲rks":
                if limit == "大于" and singal_rks > float(limit_val):
                    result.append(songi)
                elif limit == "大于等于" and singal_rks >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and singal_rks < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and singal_rks <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and singal_rks == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and singal_rks != float(limit_val):
                    result.append(songi)
            elif attribution == "得分":
                if limit == "大于" and score > int(limit_val):
                    result.append(songi)
                elif limit == "大于等于" and score >= int(limit_val):
                    result.append(songi)
                elif limit == "小于" and score < int(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and score <= int(limit_val):
                    result.append(songi)
                elif limit == "等于" and score == int(limit_val):
                    result.append(songi)
                elif limit == "不等于" and score != int(limit_val):
                    result.append(songi)
            elif attribution == "定数":
                if limit == "大于" and level > float(limit_val):
                    result.append(songi)
                elif limit == "大于等于" and level >= float(limit_val):
                    result.append(songi)
                elif limit == "小于" and level < float(limit_val):
                    result.append(songi)
                elif limit == "小于等于" and level <= float(limit_val):
                    result.append(songi)
                elif limit == "等于" and level == float(limit_val):
                    result.append(songi)
                elif limit == "不等于" and level != float(limit_val):
                    result.append(songi)
            elif attribution == "评级":
                score_level = get_score_level(int(score), is_fc).value
                if limit == "等于" and score_level == limit_val:
                    result.append(songi)
                elif limit == "不等于" and score_level != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in score_level:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in score_level:
                    result.append(songi)
            elif attribution == "难度":
                if limit == "等于" and diffi == limit_val:
                    result.append(songi)
                elif limit == "不等于" and diffi != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in diffi:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in diffi:
                    result.append(songi)
            elif attribution == "曲名":
                sn = song_name.replace(" ", "").lower()
                if limit == "等于" and sn == limit_val:
                    result.append(songi)
                elif limit == "不等于" and sn != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in sn:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in sn:
                    result.append(songi)
            elif attribution == "曲师":
                comp = composer.replace(" ", "").lower()
                if limit == "等于" and comp == limit_val:
                    result.append(songi)
                elif limit == "不等于" and comp != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in comp:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in comp:
                    result.append(songi)
            elif attribution == "画师":
                dr = drawer.replace(" ", "").lower()
                if limit == "等于" and dr == limit_val:
                    result.append(songi)
                elif limit == "不等于" and dr != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in dr:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in dr:
                    result.append(songi)
            elif attribution == "谱师":
                chapter = chapter_dic[diffi].replace(" ", "").lower()
                if limit == "等于" and chapter == limit_val:
                    result.append(songi)
                elif limit == "不等于" and chapter != limit_val:
                    result.append(songi)
                elif limit == "包含" and limit_val in chapter:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in chapter:
                    result.append(songi)
            elif attribution == "分组":
                groups_low = [g.replace(" ", "").lower() for g in groups]
                if limit == "包含" and limit_val in groups_low:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in groups_low:
                    result.append(songi)
            elif attribution == "标签":
                tags_low = [t.replace(" ", "").lower() for t in tags]
                if limit == "包含" and limit_val in tags_low:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in tags_low:
                    result.append(songi)
            elif attribution == "简评":
                comments_low = comments.replace(" ", "").lower()
                if limit == "包含" and limit_val in comments_low:
                    result.append(songi)
                elif limit == "不包含" and limit_val not in comments_low:
                    result.append(songi)
        return result

    def filter_from_previous_song(self):
        """在已有 self.filter_result 的基础上继续做筛选（与原逻辑保持一致）"""
        if not self.token:
            return
        if not hasattr(self, "filter_result"):
            return

        self.tt = datetime.now()
        filter_obj_list = self.widgets["search_page"]["filter_obj_list"]
        logical_link = filter_obj_list[0].logical_cbb.get_content()
        filter_result_copy = self.filter_result.copy()
        if logical_link != "并且(与)":
            # 如果不是“并且”逻辑，则从空集开始累加
            self.filter_result = set()
        if not logical_link and len(filter_obj_list) > 1:
            return
        if len(filter_obj_list) == 1:
            logical_link = ""
        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            if logical_link == "并且(与)":
                self.filter_result = set(
                    self.filte_with_condition(self.filter_result, conditioni)
                )
            else:
                result_list = self.filte_with_condition(filter_result_copy, conditioni)
                for resulti in result_list:
                    self.filter_result.add(resulti)
        self.place_record()

    def place_record(self):
        """
        根据 self.filter_result 布局筛选结果。
        对于每个结果只在需要时（要显示）调用 song_list_widget.build_card_for_row(row) 来构建完整的 song_info_card。
        这样避免一次性创建大量 widget，提高性能。
        """
        if not hasattr(self, "filter_result"):
            return
        if not self.filter_result:
            return

        print("开始布局")
        # 获取分组/排序选项并处理默认值
        group_by = (
            self.widgets["search_page"]["group_by"].get_content()
            if "group_by" in self.widgets["search_page"]
            else "无"
        )
        sort_by = (
            self.widgets["search_page"]["sort_by"].get_content()
            if "sort_by" in self.widgets["search_page"]
            else "无"
        )
        is_reversed = (
            self.widgets["search_page"]["sort_result_reverse_btn"].isChecked()
            if "sort_result_reverse_btn" in self.widgets["search_page"]
            else True
        )

        # 清理上一次布局的 widgets（释放资源）
        for song_cardi in self.widgets["search_page"]["song_cards"]:
            try:
                song_cardi.deleteLater()
            except Exception:
                pass
        self.widgets["search_page"]["song_cards"] = []

        result_display_flow: FlowLayout = self.widgets["search_page"][
            "result_display_flow"
        ]
        # 在批量插入期间关闭更新以避免频繁重绘
        self.widgets["search_page"]["scroll_content_widget"].setUpdatesEnabled(False)

        visited_folder = {}  # 用于分组时缓存 folder -> list[(sort_value, card)]
        empty_sort_list = []  # 当不分组时，直接保存要显示的卡片

        # 遍历筛选结果（items 里包含 row，用来按需创建完整 widget）

        cnt = len(self.filter_result)
        for songi in self.filter_result:
            # songi: (combine_name, diffi, score, acc, level, is_fc, singal_rks, row)
            combine_name, diffi, score, acc, level, is_fc, singal_rks, row = songi
            sort_rely = None
            if sort_by == "acc":
                sort_rely = float(acc)
            elif sort_by == "单曲rks":
                sort_rely = float(singal_rks)
            elif sort_by == "得分":
                sort_rely = int(score)
            elif sort_by == "定数":
                sort_rely = float(level)

            # 惰性创建完整的 song card（仅在这个条目要展示时才构建）
            cardi = self.song_list_widget.build_card_for_row(row, is_expanded=False)
            cardi.right_func = self.link_and_show  # 不同
            if cardi is None:
                continue
            self.widgets["search_page"]["song_cards"].append(cardi)
            # 完善玩家个人编辑的部分
            # 不同
            # selected_group = GROUP_INFO.get(cardi.combine_name, "").split("`")
            # selected_tag = TAG_INFO.get(cardi.combine_name, "").split("`")
            # now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(cardi.diff, "")
            # cardi.set_edited_info(selected_group, selected_tag, now_comment)

            # 计算分组标题与分组依据值（和原代码行为一致）
            if group_by == "曲名":
                title = cardi.name
                group_rely = combine_name
            elif group_by == "曲师":
                title = cardi.composer
                group_rely = title
            elif group_by == "画师":
                title = cardi.drawer
                group_rely = title
            elif group_by == "谱师":
                title = cardi.chapter
                group_rely = title
            elif group_by == "难度":
                title = diffi
                group_rely = title
            elif group_by == "评级":
                score_level = get_score_level(int(score), is_fc)
                title = score_level.value
                group_rely = title
            elif group_by == "分组":
                title = GROUP_INFO.get(combine_name, "").split("`")
                group_rely = title
            elif group_by == "标签":
                title = TAG_INFO.get(combine_name, "").split("`")
                group_rely = title
            else:
                title = None
                group_rely = None

            # 根据是否分组把 cardi 放入对应的 folder 列表或直接追加到空列表
            if group_by != "无":
                if group_by in ("分组", "标签"):
                    # 分组或标签可能会有多个分组/标签 -> 需要把该 cardi 放到多个 folder 中
                    for index in range(len(title)):
                        key = title[index]
                        if not key:
                            continue
                        if visited_folder.get(key) is None:
                            song_folderi = folder(key, expend=True)
                            self.widgets["search_page"]["song_cards"].append(
                                song_folderi
                            )
                            result_display_flow.addWidget(song_folderi)
                            visited_folder[key] = [song_folderi, []]
                        visited_folder[key][1].append((sort_rely, cardi))
                else:
                    # 单值分组（例如按曲师分组）
                    if visited_folder.get(group_rely) is None:
                        song_folderi = folder(title, expend=True)
                        self.widgets["search_page"]["song_cards"].append(song_folderi)
                        result_display_flow.addWidget(song_folderi)
                        visited_folder[group_rely] = [song_folderi, []]
                    visited_folder[group_rely][1].append((sort_rely, cardi))
            else:
                # 无分组，直接追加
                empty_sort_list.append((sort_rely, cardi))
                result_display_flow.addWidget(cardi)

        # finalize: 如果分组则把每个 folder 里的 cards 根据 sort_rely 排序后加入 folder
        if group_by != "无":
            for folderi, cards in visited_folder.values():
                if cards and cards[0][0] is not None:
                    cards = sorted(cards, key=lambda x: x[0], reverse=is_reversed)
                for _, cardi in cards:
                    folderi.add_widget(cardi)
        else:
            if empty_sort_list and empty_sort_list[0][0] is not None:
                empty_sort_list = sorted(
                    empty_sort_list, key=lambda x: x[0], reverse=is_reversed
                )
            for _, cardi in empty_sort_list:
                result_display_flow.addWidget(cardi)

        # 恢复滚动内容更新并完成布局
        self.widgets["search_page"]["scroll_content_widget"].setUpdatesEnabled(True)
        # print(f"布局{cnt}个控件用时:", time.time() - itme)
        end_time = datetime.now()
        time_difference = end_time - self.tt

        total_seconds = time_difference.total_seconds()
        seconds = int(total_seconds % 60)
        microseconds = time_difference.microseconds

        print(f"筛选并布局{cnt}个控件用时:{seconds:02d}s.{microseconds:06d}")

    def link_and_show(self, info_card: song_info_card):
        """
        在编辑页面显示指定的 song_info_card（或其副本）。
        该方法尽可能保持原有行为：
        - 复制 card（避免破坏原来的 model/缓存）
        - 把副本放到 edit page 左侧显示区
        - 初始化编辑侧（分组/标签/简评）的值并调用 set_edited_info 同步显示
        """
        info_card_copy = info_card.copy()
        self.switch_to(self.edit_info_page)
        # 移除旧的 card（如果存在）
        old = self.widgets["edit_info_page"].get("song_info_card")
        if isinstance(old, song_info_card):
            try:
                old.deleteLater()
            except Exception:
                pass
        self.widgets["edit_info_page"]["song_info_card"] = info_card_copy
        display_layout: QVBoxLayout = self.widgets["edit_info_page"]["display_layout"]
        spacer: QSpacerItem = self.widgets["edit_info_page"]["spacer"]
        for spaceri in spacer:
            display_layout.removeItem(spaceri)

        top_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        display_layout.addItem(top_spacer)

        display_layout.addWidget(info_card_copy)

        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        display_layout.addItem(bottom_spacer)
        self.widgets["edit_info_page"]["spacer"] = [top_spacer, bottom_spacer]

        parent = display_layout.parentWidget()
        if parent:
            parent.updateGeometry()
            parent.update()

        # 同步编辑区的控件状态
        group_ccb: CheckableComboBox = self.widgets["edit_info_page"]["group_ccb"]
        selected_group = GROUP_INFO.get(info_card_copy.combine_name, "").split("`")
        group_ccb.setSelectedItems(selected_group)

        tag_ccb: CheckableComboBox = self.widgets["edit_info_page"]["tag_ccb"]
        selected_tag = TAG_INFO.get(info_card_copy.combine_name, "").split("`")
        tag_ccb.setSelectedItems(selected_tag)

        comment_label: multiline_text = self.widgets["edit_info_page"]["comment_label"]
        now_comment = COMMENT_INFO.get(info_card_copy.combine_name, {}).get(
            info_card_copy.diff, ""
        )
        comment_label.set_text(now_comment)

        # 把这些元数据写到展开区（展开区会在需要时创建）
        # info_card_copy.set_edited_info(selected_group, selected_tag, now_comment)

    def save_user_edit(self):
        """
        保存编辑页面修改到 CSV（GROUP_PATH, TAG_PATH, COMMENT_PATH）。
        同时更新内存数据结构（GROUP_INFO/TAG_INFO/COMMENT_INFO）并同步到 model 对应行的 metadata。
        """
        if not self.token:
            return
        now_card: song_info_card = self.widgets["edit_info_page"]["song_info_card"]
        if not isinstance(now_card, song_info_card):
            return
        # 从编辑控件读取新值
        song_combine_name = now_card.combine_name
        diff = now_card.diff
        new_group = "`".join(
            self.widgets["edit_info_page"]["group_ccb"].selectedItems()
        )
        new_tag = "`".join(self.widgets["edit_info_page"]["tag_ccb"].selectedItems())
        new_comment = self.widgets["edit_info_page"]["comment_label"].get_plain_text()

        # 使用 pandas 写回 GROUP_PATH（原始 CSV 存储格式）

        # GROUP 写回
        try:
            df = pd.read_csv(
                GROUP_PATH,
                sep=",",
                header=None,
                encoding="utf-8",
                names=["combine_name", "group"],
                index_col=0,
            )
            df = df.fillna("")
            GROUP_INFO[song_combine_name] = new_group
            df.at[song_combine_name, "group"] = new_group
            df.to_csv(GROUP_PATH, header=False, encoding="utf-8", index=True)
        except Exception:
            pass

        # TAG 写回
        try:
            df = pd.read_csv(
                TAG_PATH,
                sep=",",
                header=None,
                encoding="utf-8",
                names=["combine_name", "tag"],
                index_col=0,
            )
            df = df.fillna("")
            TAG_INFO[song_combine_name] = new_tag
            df.at[song_combine_name, "tag"] = new_tag
            df.to_csv(TAG_PATH, header=False, encoding="utf-8", index=True)
        except Exception:
            pass

        # COMMENT 写回（注意 CSV 列名可能不同，先尝试常规写法）
        try:
            df = pd.read_csv(
                COMMENT_PATH,
                sep=",",
                header=None,
                encoding="utf-8",
                names=[
                    "combine_name",
                    "EZ_comment",
                    "HD_comment",
                    "IN_comment",
                    "AT_comment",
                ],
                index_col=0,
            )
            df = df.fillna("")
            if COMMENT_INFO.get(song_combine_name) is None:
                COMMENT_INFO[song_combine_name] = {}
            COMMENT_INFO[song_combine_name][diff] = new_comment
            colname = f"{diff}_comment"
            if colname not in df.columns:
                # 如果列名不存在，使用 at 写入自定义列（可能会导致列不对齐，原代码也有相同处理）
                df.at[song_combine_name, f"{diff}_comment"] = new_comment
            else:
                df.at[song_combine_name, colname] = new_comment
            df.to_csv(COMMENT_PATH, header=False, encoding="utf-8", index=True)
        except Exception:
            pass

        # 更新 UI 中展示的详细卡片
        # now_card.set_edited_info(new_group.split("`"), new_tag.split("`"), new_comment)

        # 更新 model 中存储的元信息（groups/tags/comment），并发出 dataChanged 以触发重绘或其他监听器
        if song_combine_name in self.all_song_card:
            for diff_key, row in self.all_song_card[song_combine_name].items():
                if diff_key == diff:
                    item = self.song_list_widget.model.get_item(row)
                    if item:
                        item.groups = new_group.split("`")
                        item.tags = new_tag.split("`")
                        item.comment = new_comment
                        idx = self.song_list_widget.model.index(row)
                        # 发出 dataChanged 通知（使用 ROLE_COMBINE 只是为了让视图刷新；你也可以定义 ROLE_GROUPS）
                        self.song_list_widget.model.dataChanged.emit(
                            idx, idx, [ROLE_COMBINE]
                        )

    def reset_filter_result(self):
        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        # print(filter_obj_list)
        for idx in range(1, len(filter_obj_list)):  # 下标为0的留着
            filter_obj_list[idx].deleteLater()
            # print('delete')
        filter_obj_list = filter_obj_list[:1:]  # 只留第一个 还原
        basic_filter_obj = filter_obj_list[0]
        self.widgets["search_page"]["filter_obj_list"] = filter_obj_list
        basic_filter_obj.filter_obj_list = filter_obj_list  # filter_obj类需要这个数据来判断增删条件的时候是否需要隐藏删除按钮
        basic_filter_obj.add_btn.show()  # 条件筛选部分加上添加条件的按钮
        basic_filter_obj.attribution_choose_cbb.set_current_choose(0)
        basic_filter_obj.limit_choose_cbb.set_current_choose(0)
        basic_filter_obj.limit_choose_cbb.set_content(NUMERIC_COMPARATORS)
        basic_filter_obj.limit_val_cbb.clear_text()
        basic_filter_obj.limit_val_cbb.clear_completer()
        basic_filter_obj.logical_cbb.set_current_choose(0)

        self.filter_result = set()
        for song_cardi in self.widgets["search_page"][
            "song_cards"
        ]:  # 先清除掉上一次布局的所有东西
            song_cardi.deleteLater()
        self.widgets["search_page"]["song_cards"] = []

    # ------------------ rks composition / placement using model ------------------
    def generate_b27_phi3(self):
        """
        使用 model 中的轻量数据计算 b27 与 phi3：
        - 遍历 model，构建 singal_rks
        - 用两个小堆维护 top27 和 top3(AP)
        - 排序后调用 place_b27_phi3 进行布局（惰性创建 widget）
        """
        if not self.token:
            InfoBar.warning(
                title="用户未登录",
                content="请先回到账号页面进行授权喵！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            self.switch_to(self.account_page)
            return

        # 收集所有歌曲的轻量信息
        all_song_info = []
        model = self.song_list_widget.model
        for row in range(model.rowCount()):
            item = model.get_item(row)
            if not item:
                continue
            diffi = item.diff
            if diffi == "Legacy":
                continue
            score = item.score
            is_fc = item.is_fc
            acc = float(item.acc)
            level = float(item.level)
            singal_rks = round(level * pow((acc - 55) / 45, 2), 4)
            all_song_info.append(
                (singal_rks, (item.combine_name, acc, level, diffi, score, is_fc, row))
            )

        self.b27 = []
        self.phi3 = []
        heapq.heapify(self.b27)
        heapq.heapify(self.phi3)
        for singal_rks, other in all_song_info:
            combine_name, acc, level, diff, score, is_fc, row = other
            if float(acc < 70):  # acc < 70% 不计入rks
                continue
            if len(self.b27) < 27:
                heapq.heappush(self.b27, (singal_rks, other))
            else:
                heapq.heappushpop(self.b27, (singal_rks, other))
            if int(score) == int(1e6):
                # print(f"{combine_name}合法")
                if len(self.phi3) < 3:
                    heapq.heappush(self.phi3, (singal_rks, other))
                else:
                    heapq.heappushpop(self.phi3, (singal_rks, other))
        # print(f"phi3是这些:{self.phi3}")
        # 按单曲rks从大到小排序( 这不还是要排序吗
        self.b27 = sorted(self.b27, key=lambda x: x[0], reverse=True)
        self.phi3 = sorted(self.phi3, key=lambda x: x[0], reverse=True)
        # print('开始布局b27页面')
        self.generate_improve_rks_advise()
        self.place_b27_phi3()

    def place_b27_phi3(self):
        """
        布局 phi3 和 b27 结果：
        - 清空目标布局
        - 为 phi3 / b27 中的每个条目惰性创建 song_info_card 并加入对应 folder
        - 计算并显示平均 rks
        """
        # 获取目标布局（main_layout）引用
        layout: QVBoxLayout = self.widgets.get("place_b27_phi3_page", {}).get(
            "main_layout"
        )
        if layout is None:
            return

        # 清理当前 layout 中的子控件（防止重复叠加）
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                try:
                    child.widget().deleteLater()
                except Exception:
                    pass

        player_rks_label = HorizontalInfoCard("当前rks:")
        player_rks_label.setFixedHeight(50)
        layout.addWidget(player_rks_label, 0)
        # layout.insertWidget(0, player_rks_label, 0)
        self.total_rks: float = 0.0

        b27_folder = folder("b27:", True)
        b27_folder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        b27_folder.setMinimumHeight(0)
        layout.setStretch(
            layout.indexOf(b27_folder), 1 if b27_folder.is_expanded else 0
        )
        for singal_rks, other in self.b27:
            combine_name, acc, level, diff, score, is_fc, row = other
            self.total_rks += float(singal_rks)
            cardi = self.song_list_widget.build_card_for_row(row, is_expanded=False)
            if cardi:
                cardi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                cardi.setMinimumHeight(0)  # 完善玩家个人编辑的部分
                selected_group = GROUP_INFO.get(cardi.combine_name, "").split("`")
                selected_tag = TAG_INFO.get(cardi.combine_name, "").split("`")
                now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(
                    cardi.diff, ""
                )
                # cardi.set_edited_info(selected_group, selected_tag, now_comment)
                cardi.right_func = self.link_and_show
                b27_folder.add_widget(cardi)
        layout.addWidget(b27_folder, 0)

        phi3_folder = folder("phi3:", True)
        phi3_folder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        phi3_folder.setMinimumHeight(0)
        layout.setStretch(
            layout.indexOf(phi3_folder), 1 if phi3_folder.is_expanded else 0
        )
        for singal_rks, other in self.phi3:
            combine_name, acc, level, diff, score, is_fc, row = other
            self.total_rks += float(singal_rks)
            # 惰性创建：只有这小部分会被创建为 widget
            cardi = self.song_list_widget.build_card_for_row(row, is_expanded=False)
            if cardi:
                cardi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                cardi.setMinimumHeight(0)
                selected_tag = TAG_INFO.get(cardi.combine_name, "").split("`")
                now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(
                    cardi.diff, ""
                )
                # cardi.set_edited_info(selected_group, selected_tag, now_comment)
                cardi.right_func = self.link_and_show
                phi3_folder.add_widget(cardi)
        layout.addWidget(phi3_folder, 0)

        player_rks = round(self.total_rks / (len(self.b27) + len(self.phi3)), 4)
        rks_content_elm = BodyLabel(str(player_rks))
        rks_content_elm.setStyleSheet(
            """
            font-size: 24px;
            color: #333;
            background: transparent;
        """
        )
        player_rks_label.add_widget(rks_content_elm)
        # layout.addStretch(1)
        # 当某个 folder 的展开状态变化时，重新分配 layout 中所有 folder 的 stretch

        def _refresh_folder_stretches(_=None):
            try:
                # 遍历 layout 的所有项，按 widget.is_expanded 调整对应的 stretch
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    w = item.widget() if item else None
                    if isinstance(w, folder):
                        layout.setStretch(i, 1 if w.is_expanded else 0)
                # 强制刷新布局几何
                parent_widget = self.widgets.get("place_b27_phi3_page", {}).get(
                    "widget"
                )
                if parent_widget:
                    parent_widget.updateGeometry()
                    parent_widget.adjustSize()
                    parent_widget.update()
            except Exception:
                pass

        # 连接 toggled 信号（如果多次调用 place_b27_phi3，先断开以避免重复连接）
        try:
            # 确保不会重复连接：断开现有（如果有），然后连接
            try:
                phi3_folder.toggled.disconnect()
            except Exception:
                pass
            phi3_folder.toggled.connect(_refresh_folder_stretches)
            try:
                b27_folder.toggled.disconnect()
            except Exception:
                pass
            b27_folder.toggled.connect(_refresh_folder_stretches)
        except Exception:
            pass
        _refresh_folder_stretches()
        self.switch_to(self.place_b27_phi3_page)

    # ------------------ utility UI methods ------------------
    def switch_to(self, widget: QWidget):
        """在 content_widget 中切换到指定页面"""
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        if content_widget.indexOf(widget) == -1:
            content_widget.addWidget(widget)
        content_widget.setCurrentWidget(widget)

    # --------------- 账号页面 -------------------
    def init_account_page(self) -> QWidget:
        self.widgets["account_page"] = {}
        widget = bg_widget(self.page_bg_cache["account"])
        self.widgets["account_page"]["widget"] = widget

        layout = QVBoxLayout(widget)
        self.widgets["account_page"]["layout"] = layout
        widget.setLayout(layout)

        if self.avatar:
            original_pixmap = QPixmap(AVATER_IMG_PREPATH + self.avatar + ".png")
            # 使用QFluentWidgets的AvatarWidget显示
            avatar = AvatarWidget(original_pixmap, widget)
            avatar.setFixedSize(110, 110)
            avatar.show()

        if self.user_name:
            name_label = label(
                self.user_name,
                {
                    "font_size": 28,
                    "max_width": 300,
                    "min_height": 30,
                    "background_color": (255, 255, 255, 0.8),
                    "font_color": (138, 225, 252, 1),
                },
            )
            layout.addWidget(name_label)
        QRcode_img = ImageLabel(QRCODE_EMPTY_IMG_PATH)  # 空二维码
        QRcode_img.setFixedSize(410, 410)

        # 2. 保持长宽比缩放图片
        pixmap = QPixmap(QRCODE_EMPTY_IMG_PATH)
        pixmap = pixmap.scaled(
            410,
            410,
            Qt.KeepAspectRatioByExpanding,  # 保持长宽比（扩展填充）
            Qt.SmoothTransformation,  # 平滑缩放
        )

        # 3. 居中显示（避免拉伸变形）
        QRcode_img.setAlignment(Qt.AlignCenter)
        QRcode_img.setPixmap(pixmap)
        self.widgets["account_page"]["QRcode_img"] = QRcode_img
        self.widgets["account_page"]["layout"].addWidget(QRcode_img)

        login_confirm_btn = button("点击这里开始授权")
        login_confirm_btn.bind_click_func(self.check_login_status)
        self.widgets["account_page"]["login_confirm_btn"] = login_confirm_btn
        layout.addWidget(login_confirm_btn)

        log_out_btn = button("退出登录")
        log_out_btn.bind_click_func(self.log_out)
        self.widgets["account_page"]["log_out_btn"] = log_out_btn
        layout.addWidget(log_out_btn)

        if self.token:
            login_confirm_btn.hide()  # 如果已经有了token就不用再获取了
            QRcode_img.hide()
            # self.switch_to(self.home_page)
            # get_token_by_qrcode()
        else:
            log_out_btn.hide()

        return widget

    def check_login_status(self):
        self.QRCode_info = TapTapLogin.RequestLoginQRCode()
        print(f"获取二维码信息成功：{self.QRCode_info}")

        print("已生成二维码！")
        qrcod = make(self.QRCode_info["qrcode_url"])
        qrcod.save(QRCODE_IMG_PATH)
        print("添加成功")
        self.widgets["account_page"]["QRcode_img"].setPixmap(QPixmap(QRCODE_IMG_PATH))
        self.login_check_timer = QTimer()
        self.login_check_timer.setInterval(
            self.QRCode_info["interval"] * 1000
        )  # 秒转毫秒
        self.login_check_timer.timeout.connect(self.check_login)
        self.login_check_timer.start()

    def check_login(self):
        Login_info = TapTapLogin.CheckQRCodeResult(self.QRCode_info)
        if Login_info.get("data"):
            self.login_check_timer.stop()
            Profile = TapTapLogin.GetProfile(Login_info["data"])
            # 这里可以触发登录成功后的操作
            Token = TapTapLogin.GetUserData({**Profile["data"], **Login_info["data"]})
            self.token = Token["sessionToken"]
            with open(TOKEN_PATH, "w") as file:
                file.write(Token["sessionToken"])
            self.avatar = self.save_dict["user"]["avatar"]
            original_pixmap = QPixmap(AVATER_IMG_PREPATH + self.avatar + ".png")
            print(self.avatar)
            # 显示用户头像
            avatar = AvatarWidget(
                original_pixmap, self.widgets["account_page"]["widget"]
            )
            self.widgets["account_page"]["avatar"] = avatar
            avatar.setFixedSize(100, 100)
            avatar.show()

            self.widgets["account_page"]["QRcode_img"].hide()
            self.widgets["account_page"]["login_confirm_btn"].hide()
            self.widgets["account_page"]["log_out_btn"].show()
            self.switch_to(self.home_page)
        else:
            print("二维码登录未授权...")

    def log_out(self):
        with open(TOKEN_PATH, "w") as _:  # 清空tokn记录及self.token
            self.token = ""
            self.widgets["account_page"]["QRcode_img"].show()
            self.widgets["account_page"]["login_confirm_btn"].show()
            self.widgets["account_page"]["log_out_btn"].hide()
            avatar: AvatarWidget = self.widgets["account_page"]["avatar"]
            avatar.deleteLater()
            self.avatar = ""
        # 应该还要清除其他的页面


# ---------- 程序入口 ----------
if __name__ == "__main__":
    window = MainWindow()
    # window.show()
    sys.exit(app.exec_())
