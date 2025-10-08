from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QApplication,
    QStackedWidget,
    QDesktopWidget,
    QSizePolicy,
    QStackedLayout,
)
from qframelesswindow import FramelessWindow, StandardTitleBar
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import (
    QGuiApplication,
    QIcon,
    QPixmap,
    QDesktopServices,
)
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
    Action,
    SegmentedWidget,
)
from qfluentwidgets import FluentIcon as FIF
import sys
import heapq  # 算rks组成
import os
from typing import Any, List, Tuple, Dict
import pandas as pd
from datetime import datetime
from math import sqrt
import copy
import random
import json

# pypy3 -m pip install pandas, qfluentwidgets, requests, PyQt5
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


class MainWindow(FramelessWindow):

    def __init__(self):
        super().__init__()

        # ---------------- 初始化变量 ----------------
        self.widgets: dict[str, dict] = (
            {}
        )  # 按照页面分类存储各个控件 方便 不同页面重复使用同样的变量名 及 在类的各个地方调用任意控件
        """self.widgets[页面名称][页面控件名称]=控件"""

        self.illustration_cache: dict[str, QPixmap] = (
            {}
        )  # 多线程预处理曲绘转化与裁切 后续 搜索/rks组成 布局就可以复用这些缓存 加速布局
        """self.illustration_cache[组合名称] = 曲绘缓存图"""

        self.page_bg_cache: dict[str, QPixmap] = {}  # 各个页面的二次元背景及图片缓存
        """self.page_bg_cache[组合名称] = 背景缓存图"""

        self.page_icon_cache: dict[str, QPixmap] = {}  # 主页各个组件的二次元图标缓存
        """self.page_icon_cache[组合名称] = 图标缓存图"""

        self.home_page_tips: list[str] = [  # 主页下方的各种tips的内容
            "这里是主页 有各种小工具",
            "鼠标放在卡片底端的文字上可以展开详细信息",
            "搜索页面对于曲师 曲名等内容提供自动补全",
            "筛选条件大于1个的时候记得选择连接逻辑",
            "所有歌曲卡片都可以左键展开详细信息 右键跳转编辑页面",
            "由于找不到合适的图标索性就用二次元头像做icon了(",
        ]

        self.init_variable()  # 初始化各种变量

        datetime.now()
        self.log_write("变量初始化完成")
        self.preinit()  # 并行预处理图片

        # ---------------- 主窗口设置 ----------------
        # 设置窗口标题
        self.setTitleBar(StandardTitleBar(self))
        self.titleBar.setTitle("PhiFilter Tool")
        self.titleBar.titleLabel.setStyleSheet(
            """
            font-size: 30px;
            font-family: "Segoe UI";
        """
        )
        self.setWindowTitle("PhiFilter Tool")  # 设置任务栏标题
        self.resize(950, 800)  # 主窗口大小 随便设的
        # 将窗口居中显示
        screen = QDesktopWidget().screenGeometry()
        pos_x = (screen.width() - self.width()) // 2
        pos_y = (screen.height() - self.height()) // 2
        self.move(pos_x, pos_y)

        # ---------- 主区域 ----------
        # 基础页面布局 切开内容区和导航栏区
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
        main_layout.addWidget(navigation_interface, 0)  # 导航栏不可延伸
        navigation_interface.setExpandWidth(200)  # 设置导航展开宽度

        content_widget = QStackedWidget(self)  # 内容页面管理器
        self.widgets["basepage"]["content_widget"] = content_widget
        main_layout.addWidget(content_widget, 1)  # 额外空间全给内容页面

        self.song_list_widget = SongListViewWidget()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    # 获取用户设置
    def get_setting(self):
        """获取用户设置"""
        # 检查文件是否存在
        setting_file_path = appdata_path(SETTING_PATH)
        self.log_write(f"日志地址{setting_file_path}")
        path_obj = Path(setting_file_path)
        default_setting = {
            self.user_name: {
                "main_setting": {
                    "always_update": False,
                    "default_open_page": "home_page",
                },
                "search_page_setting": {
                    "default_filter": {
                        "attribution": "acc",
                        "limit": "大于等于",
                        "value": "99.3",
                    }
                },
            },
        }
        if not path_obj.exists() or path_obj.stat().st_size == 0:
            # 如果不存在，创建默认设置并保存
            # 写入默认配置到文件
            with open(setting_file_path, "w", encoding="utf-8") as f:
                json.dump(default_setting, f, ensure_ascii=False, indent=4)
            # print(f"初始化配置文件: {setting_file_path}")

        with open(setting_file_path, "r", encoding="utf-8") as f:
            setting_file = json.load(f)
            if not setting_file:
                setting_file = default_setting
            # 读取主设置
            if self.user_name not in setting_file.keys():
                setting_file[self.user_name] = {
                    "main_setting": {
                        "always_update": False,
                        "default_open_page": "home_page",
                    },
                    "search_page_setting": {
                        "default_filter": {
                            "attribution": "acc",
                            "limit": "大于等于",
                            "value": "99.3",
                        }
                    },
                }
                with open(setting_file_path, "w", encoding="utf-8") as ff:
                    json.dump(setting_file, ff, ensure_ascii=False, indent=4)
            user_setting = setting_file[self.user_name]
            main_setting: dict = user_setting["main_setting"]
            self.always_update: bool = main_setting["always_update"]
            self.log_write(f"是否自动更新:{self.always_update}")
            # 读取默认开屏页设置
            self.default_open_page: str = main_setting["default_open_page"]

            # 读取搜索页设置
            search_page_setting: dict = user_setting["search_page_setting"]
            # print(f"读取搜索页设置{search_page_setting}")
            self.default_filter: dict[str, str] = search_page_setting["default_filter"]

    # 初始化各种与账号相关的变量
    def init_variable(self):
        """初始化各种与账号相关的变量 方便退出账号的时候重置变量 已经缓存过的就不用了"""
        self.time_record = datetime.now()  # 记录各种起始时间
        self.is_updated: bool = False  # 之前 存储的数据是否为最新的数据
        self.avatar: str = ""  # 存放用户头像文件名
        self.background_name: str = ""  # 背景名称
        self.EZ_statistical_data: list[int] = [
            -1,
            -1,
            -1,
        ]  # 各个难度的统计数据[cleared, FC, AP]
        self.HD_statistical_data: list[int] = [-1, -1, -1]
        self.IN_statistical_data: list[int] = [-1, -1, -1]
        self.AT_statistical_data: list[int] = [-1, -1, -1]
        self.rks: float = 0  # 玩家的rks
        self.money: tuple[int] = (0, 0, 0, 0, 0)  # KB MB GB TB PB
        self.challengemode_rank: str = ""  #
        self.user_introduction: str = ""  # 用户自我介绍
        self.user_name: str = ""  # 用户名
        self.token: str = ""  # 用户 session_token
        self.save_dict: dict = {}  # 云存档解析后的字典数据
        self.total_rks: float = 0  # rks未/30之前得到的值 用于计算某个歌曲是否能推分

        self.b27: List[Tuple[float, Tuple[str, Any]]] = []
        """self.b27 = (单曲rks, 处于哪一行)"""

        self.phi3: List[Tuple[float, Tuple[str, Any]]] = []  # 格式同self.b27

        self.cname_to_name: dict[str, Tuple[str, str, str, dict[str, str]]] = {}
        """
        self.cname_to_name[组合名称] = (
            正常名称,
            曲师名称,
            画师名称,
            {"EZ": EZ难度谱师, "HD": HD难度谱师, "IN": IN难度谱师}
        )
        """

        self.diff_map_result: Dict[str, Dict[str, str]] = (
            {}
        )  # diff_map_result[组合名称][难度]=定数

        self.filter_result = None  # 筛选结果

    def log_write(self, text: str):
        with open(appdata_path(LOG_PATH), "a+", encoding="utf-8") as f:
            f.write(text + "\n")

    # 多线程预处理函数
    def preinit(self):
        """多线程预处理函数"""
        self.loader = ImageLoader()  # 任务管理器

        # ------------ 添加任务 ------------
        for combine_namei in COMBINE_NAME:  # 缓存曲绘
            self.loader.add_task(
                resource_path(rf"{ILLUSTRATION_PREPATH}{combine_namei}.png"),
                combine_namei,
                self.illustration_cache,
                400,
            )

        for keyi, pathi in SONG_CARD_BACKGROUND.items():  # 背景卡片
            self.loader.add_task(resource_path(pathi), keyi, self.page_bg_cache, 250)

        self.loader.add_task(  # 空二维码
            resource_path(QRCODE_EMPTY_IMG_PATH),
            "QRcode_empty",
            self.illustration_cache,
            410,
        )
        # --------- 控件图标缓存 ---------
        #  生成rks组成卡片
        rks_conpone_card_bg_path = resource_path(
            READONLY_BACKGROUND_IMG_PREPATH + "default_rks_conpone_card_bg.png"
        )
        self.loader.add_task(
            rks_conpone_card_bg_path,
            "rks_conpone_card_bg",
            self.page_icon_cache,
            250,
        )

        # 更新卡片
        rks_conpone_card_bg_path = resource_path(
            READONLY_BACKGROUND_IMG_PREPATH + "default_update_card_bg.png"
        )
        self.loader.add_task(
            rks_conpone_card_bg_path,
            "update_card_bg",
            self.page_icon_cache,
            250,
        )

        # 计算卡片
        calculate_score_card_bg_path = resource_path(
            READONLY_BACKGROUND_IMG_PREPATH + "calculate_score_card_bg.png"
        )
        self.loader.add_task(
            calculate_score_card_bg_path,
            "calculate_score_card_bg",
            self.page_icon_cache,
            250,
        )

        # self.log_write(f'待办任务{self.loader.todo_list}')
        self.log_write(f"待办任务加载完成!")
        self.loader.all_tasks_finished.connect(self.on_all_finished)  # 所有任务完成
        self.loader.start_processing()  # 开始处理任务

    # 预处理结束后执行的操作
    def on_all_finished(self):
        """预处理结束后执行的操作"""
        # 检查文件是否存在且不为空
        if (
            not os.path.exists(appdata_path(TOKEN_PATH))
            or os.path.getsize(appdata_path(TOKEN_PATH)) == 0
        ):
            print("Token文件不存在或为空，创建新的token存储")
            self.token_file = {"last_user": ""}  # 初始化为空字典
            # 保存初始文件
            with open(appdata_path(TOKEN_PATH), "w", encoding="utf-8") as f:
                json.dump(self.token_file, f, ensure_ascii=False, indent=4)

        if os.path.exists(appdata_path(TOKEN_PATH)):  # 尝试获取已存储的token
            with open(appdata_path(TOKEN_PATH), "r", encoding="utf-8") as token_file:
                # content = token_file.read().strip()
                # if not content:
                #     print("文件为空，使用默认值")
                #     self.token_file = {"last_user":''}
                #     json.dump(self.token_file, token_file, ensure_ascii=False, indent=4)
                # else:
                self.token_file = json.load(token_file)

                last_user = self.token_file["last_user"]
                if last_user:
                    self.token = self.token_file[last_user]  # 获取上一次登录时的账号

        else:  # TOKEN_PATH 不存在
            with open(appdata_path(TOKEN_PATH), "w", encoding="utf-8") as token_file:
                self.token_file = {"last_user": ""}
                json.dump(self.token_file, token_file, ensure_ascii=False, indent=4)
        # print('ok')
        if self.token:
            self.log_write("预处理结束了 有token")
            # 常更新的话生成rks组成的时候会自动更新一次 这里再更新就重复了
            self.get_save_data()

        self.get_setting()
        self.init_all_pages()
        self.init_navigation()
        self.generate_b27_phi3()  # 先预生成 后续
        if self.token:
            self.switch_to(
                self.widgets[self.default_open_page]["widget"]
            )  # 切换到指定的起始页面
            # self.switch_to(self.account_page)
        else:
            self.switch_to(self.account_page)

        # self.open_window.deleteLater()
        self.show()
        end_time = datetime.now()
        time_difference = end_time - self.time_record

        total_seconds = time_difference.total_seconds()
        seconds = int(total_seconds % 60)
        microseconds = time_difference.microseconds

        self.log_write(f"预处理用时:{seconds:02d}s.{microseconds:06d}")

    # 从widget开始向上查找第一个是target_class类型的父控件
    def find_parent_widget(self, widget, target_class):
        """
        从 widget 开始，向上查找第一个是 target_class 类型的父控件
        """
        current = widget
        while current is not None:
            if isinstance(current, target_class):
                return current
            current = current.parent()
        return None

    # 显示菜单
    def showContextMenu(self, pos):
        # pos 是相对于当前控件的坐标（比如 centralWidget）
        # 转换为全局坐标，再转回当前控件的坐标系（确保准确）
        global_pos = self.mapToGlobal(pos)

        # 使用 childAt 找到该位置的直接子控件
        clicked_widget = self.childAt(pos)  # pos 是相对于 self 的坐标
        target_card = self.find_parent_widget(clicked_widget, song_info_card)
        # 创建菜单
        menu = RoundMenu("菜单", self)

        if target_card is None:
            menu.addAction(Action(FIF.COPY, "空白区域"))
        else:
            widget_type = type(target_card).__name__
            # object_name = target_card.objectName()
            current_page = self.widgets["basepage"]["content_widget"].currentWidget()
            if current_page:
                object_name = current_page.objectName()
                # print("当前页面的 objectName:", object_name)
            # 示例：根据不同控件类型，添加不同菜单项
            if isinstance(target_card, song_info_card) and object_name == "search_page":
                menu.addAction(
                    Action(
                        FIF.EDIT,
                        f"编辑{target_card.combine_name}相关信息",
                        triggered=lambda: self.link_and_show(target_card),
                    )
                )
                menu.addAction(
                    Action(
                        FIF.FILTER,
                        f"查找{target_card.combine_name}是否可达指定分数",
                        triggered=lambda: self.link_and_show_score_page(target_card),
                    )
                )
            else:
                menu.addAction(Action(FIF.COPY, f"控件类型: {widget_type}"))
                # menu.addAction(f"对象名: {object_name}")

        # 在右键位置弹出菜单
        menu.exec_(global_pos)

    # 生成组合名称与其对应名称 曲师等信息对照
    def generate_cname_to_name_info(self):
        """读取 info.tsv 并构建 self.cname_to_name 信息"""

        df = pd.read_csv(
            resource_path(INFO_PATH),
            sep="\t",  # 文酱的项目生成的.tsv文件 分隔符是 \t
            header=None,  # 无头模式
            encoding="utf-8",
            names=[  # 每一列的名称
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
        df = df.fillna("")  # 没有数据的部分填充空字符
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

            if ATchapter:  # 有可能没有AT
                self.cname_to_name[combine_name][3]["AT"] = ATchapter

    # 获取存档信息并填充歌曲信息
    def get_save_data(self):
        """
        获取存档信息并填充歌曲信息

        依赖: self.cname_to_name 图片缓存
        """
        print("进入存档")
        if self.token == "":
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
        try:
            # 此部分来自 千柒 的 Phi-CloudAction-python-master 项目
            with PhigrosCloud(self.token) as cloud:
                summary_data = (
                    cloud.getSummary()
                )  # summary_data的值就是get_play_data.py的 class summary 里面的那些变量做成字典
                self.log_write(f"你的summary是{summary_data}")

                self.challengemode_rank = str(summary_data["challenge"])
                self.log_write(f"你的挑战模式组成是{self.challengemode_rank}")

                # self.rks = summary_data['rks'] # 这里的rks可以被修改 自己算比较安全
                self.avatar = summary_data["avatar"]
                self.EZ_statistical_data = summary_data["EZ"]
                self.HD_statistical_data = summary_data["HD"]
                self.IN_statistical_data = summary_data["IN"]
                self.AT_statistical_data = summary_data["AT"]

                self.user_name = cloud.getNickname()
                self.log_write(f"你的名字是{self.user_name}")

                save_data = cloud.getSave(summary_data["url"], summary_data["checksum"])
                save_dict = unzipSave(save_data)
                save_dict = decryptSave(save_dict)
                save_dict = formatSaveDict(save_dict)
                self.save_dict = save_dict
                # self.log_write(f"存档文件是这个喵{save_dict}")

                self.background_name = save_dict["user"]["background"]
                self.log_write(f"你的背景名称是{self.background_name}")
                # print(f"你的金币是{save_dict["gameProgress"]}")
                self.money = save_dict["gameProgress"]["money"]
                # self.log_write('你的金币是', self.money)

                self.user_introduction = save_dict["user"]["selfIntro"]
                self.log_write(f"你的自我介绍是{self.user_introduction}")
        except:
            InfoBar.error(
                title="未知错误",
                content="云存档获取失败了喵 重新试试吧",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        # 生成难度对照表
        df = pd.read_csv(
            resource_path(DIFFICULTY_PATH),
            sep="\t",
            header=None,
            encoding="utf-8",
            names=["song_name", "EZ", "HD", "IN", "AT"],
        )
        df = df.fillna("")  # 用空字符串替换 NaN
        self.diff_map_result: Dict[str, Dict[str, str]] = {}
        for _, row in df.iterrows():
            name = row["song_name"]
            diff_map = {"EZ": row["EZ"], "HD": row["HD"], "IN": row["IN"]}
            if row["AT"]:
                diff_map["AT"] = row["AT"]
            self.diff_map_result[name] = diff_map

        # 使用委托式视图填充 model
        self.song_list_widget = SongListViewWidget()  # 覆盖掉之前的所有信息
        self.generate_cname_to_name_info()  # 重新登陆会洗掉cname_to_name原来的值
        self.log_write("进入init_model_from_save_data")
        self.song_list_widget.init_model_from_save_data(
            self.save_dict,
            self.diff_map_result,
            self.cname_to_name,
            # GROUP_INFO,
            # COMMENT_INFO,
            self.illustration_cache,
            self.page_bg_cache,
            self.user_name,
        )
        self.log_write("更新完成喵~")

        InfoBar.success(
            title="连接成功",
            content="更新完成喵~",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=window,
        )
        self.is_updated = False  # 更新过数据了 之前存储的就不是最新的数据了
        # self.log_write("get_save_data 用时", time.time() - times, "s")

    # ----------------- 页面相关处理  -----------------
    # 初始化所有页面
    def init_all_pages(self):
        """
        初始化所有页面

        依赖: 图片缓存
        """
        self.home_page = self.init_homepage()
        self.log_write("初始化home_page完成")
        self.home_page.setObjectName("home_page")

        self.account_page = self.init_account_page()
        self.log_write("初始化account_page完成")
        self.account_page.setObjectName("account_page")

        self.place_b27_phi3_page = self.init_place_b27_phi3_page()
        self.log_write("初始化place_b27_phi3_page完成")
        self.place_b27_phi3_page.setObjectName("place_b27_phi3_page")

        self.score_calculate_page = self.init_score_calculate_page()
        self.log_write("初始化score_calculate_page完成")
        self.score_calculate_page.setObjectName("score_calculate_page")

        self.search_page = self.init_search_page()
        self.log_write("初始化search_page完成")
        self.search_page.setObjectName("search_page")

        self.edit_info_page = self.init_edit_info_page()
        self.log_write("初始化edit_info_page完成")
        self.edit_info_page.setObjectName("edit_info_page")

        self.setting_page = self.init_setting_page()
        self.log_write("初始化setting_page完成")
        self.setting_page.setObjectName("setting_page")

    # 切换到指定页面
    def switch_to(self, widget: QWidget):
        """
        切换到指定页面

        入参: widget: 切换到的页面
        """
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        if content_widget.indexOf(widget) == -1:
            content_widget.addWidget(widget)
        content_widget.setCurrentWidget(widget)

    # 初始化导航栏
    def init_navigation(self):
        """把导航项（主页、rks组成页、搜索、编辑等）添加到 导航栏

        依赖: self.init_all_pages
        """
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

        calculate_icon = QIcon(resource_path(ICON_PREPATH + "calculate_icon.png"))
        navigation_interface.addItem(
            routeKey=self.score_calculate_page.objectName(),
            icon=calculate_icon,
            text="计算分数是否可达",
            onClick=lambda: self.switch_to(self.score_calculate_page),
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

        account_icon = QIcon(resource_path(ICON_PREPATH + "account_icon.png"))
        navigation_interface.addItem(
            routeKey=self.account_page.objectName(),
            icon=account_icon,
            text="账号管理",
            onClick=lambda: self.switch_to(self.account_page),
            position=(NavigationItemPosition.BOTTOM),
        )

        navigation_interface.addItem(
            routeKey=self.setting_page.objectName(),
            icon=FIF.SETTING,
            text="设置",
            onClick=lambda: self.switch_to(self.setting_page),
            position=(NavigationItemPosition.BOTTOM),
        )

        search_icon = QIcon(resource_path(ICON_PREPATH + "search_icon.png"))
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

        # 将 content_widget 的 currentChanged 事件与 link_interface_and_page_change 绑定
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        content_widget.currentChanged.connect(self.link_interface_and_page_change)
        content_widget.setCurrentIndex(0)  # 默认第 0 页（home_page）

    # 当前页面变化时 同步导航栏选中项
    def link_interface_and_page_change(self, index: int):
        """当前页面变化时 同步导航栏选中项"""
        content_widget: QStackedWidget = self.widgets["basepage"]["content_widget"]
        widget = content_widget.widget(index)

        navigation_interface: NavigationInterface = self.widgets["basepage"][
            "navigation_interface"
        ]
        navigation_interface.setCurrentItem(widget.objectName())

        if widget.objectName() == "home_page":  # 切换到主页时更新tip_label
            self.widgets["home_page"]["tip_label"].set_text(
                random.choice(self.home_page_tips)
            )

    # -------------------主页-------------------
    def init_homepage(self) -> QWidget:
        """
        初始化主页

        返回homepage以记录
        """

        self.widgets["home_page"] = {}

        # widget = bg_widget(self.page_bg_cache["home"])
        widget = QWidget()
        self.widgets["home_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["home_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(0, 24, 24, 24)
        main_layout.setSpacing(4)

        # '主页'文字标签
        title_style = {
            "min_height": 50,
            "max_height": 50,
            "font_color": (182, 204, 161, 1),
            "font_size": 48,
        }
        home_page_title_label = label("主页", title_style)
        home_page_title_label.adjustSize()
        home_page_title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(home_page_title_label)

        # 水平分割线
        horizontal_separator = HorizontalSeparator()
        main_layout.addWidget(horizontal_separator)

        # --------------- 功能卡片 ------------------
        flow_layout = FlowLayout()
        self.widgets["home_page"]["flow_layout"] = flow_layout
        flow_layout.setContentsMargins(
            0, 7, 0, 0
        )  # 上侧是跟分割线相邻的地方 设置一点距离
        main_layout.addLayout(flow_layout)  # layout直接加layout?

        card_title_style = {
            "font_size": 29,
        }
        card_content_style = {
            "font_size": 18,
        }
        generate_rsk_conpone_card = quick_function_card(
            self.page_icon_cache["rks_conpone_card_bg"],
            "生成rks组成图",
            "生成b27, phi3组成的文件夹 左键歌曲卡片可展开详细信息，右键跳转编辑页面",
            card_title_style,
            card_content_style,
        )
        self.widgets["home_page"][
            "generate_rsk_conpone_card"
        ] = generate_rsk_conpone_card
        generate_rsk_conpone_card.left_func = self.generate_b27_phi3
        flow_layout.addWidget(generate_rsk_conpone_card)

        update_savedata_card = quick_function_card(
            self.page_icon_cache["update_card_bg"],
            "更新一下数据~",
            "初始化记录数据后使用的存储数据 也可以在设置中改为常更新 但常更新会导致运行速度变慢",
            card_title_style,
            card_content_style,
        )
        self.widgets["home_page"]["update_savedata_card"] = update_savedata_card
        update_savedata_card.left_func = self.update_data
        flow_layout.addWidget(update_savedata_card)

        calculate_score_card = quick_function_card(
            self.page_icon_cache["calculate_score_card_bg"],
            "计算分数是否可达",
            "设置歌曲及难度之后右键连接到本页面 输入期望达到的分数 给出达到需要的各项数据",
            card_title_style,
            card_content_style,
        )
        self.widgets["home_page"]["calculate_score_card"] = calculate_score_card
        calculate_score_card.left_func = lambda: self.switch_to(
            self.score_calculate_page
        )
        flow_layout.addWidget(calculate_score_card)

        # --------------- 左下角提示 ---------------
        tip_layout = QHBoxLayout()
        self.widgets["home_page"]["tip_layout"] = tip_layout
        main_layout.addLayout(tip_layout)
        tip_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        tip_layout.setContentsMargins(0, 0, 0, 0)
        tip_layout.setSpacing(0)

        tip_style = {
            "font_size": 22,
            "min_width": widget.width(),
            "max_width": widget.width(),
            "max_height": 26,
            "min_height": 26,
            "font_color": (138, 138, 138, 1),
            "background_color": (255, 255, 255, 0.8),
        }
        tip_label = label(
            random.choice(self.home_page_tips), tip_style
        )  # 随机选一个作为展示的内容
        self.widgets["home_page"]["tip_label"] = tip_label
        tip_layout.addWidget(tip_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        return widget

    # -----------初始化rks组成页-----------
    def init_place_b27_phi3_page(self) -> QWidget:
        """初始化 rks 组成页面"""
        self.widgets["place_b27_phi3_page"] = {}
        widget = QWidget()
        self.widgets["place_b27_phi3_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["place_b27_phi3_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(5, 0, 0, 5)  # 左边下面可能贴边缘
        main_layout.setSpacing(5)

        return widget

    # 计算b27与phi3组成
    def generate_b27_phi3(self):
        """
        使用model中的整合数据计算b27与phi3及其提升可能 存储并布局
        """
        if (
            not self.always_update and self.is_updated
        ):  # 懒更新 且 最新的版本已经布局过了 直接跳转即可
            self.switch_to(self.place_b27_phi3_page)
            # self.log_write('最新最热rks')
            return

        if self.always_update:
            self.get_save_data()

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

        model = self.song_list_widget.model
        self.b27 = []
        self.phi3 = []
        heapq.heapify(self.b27)
        heapq.heapify(self.phi3)
        self.log_write(f"一共条目数{model.rowCount()}")
        for row in range(model.rowCount()):
            item = model.get_item(row)
            if not item:
                continue

            diffi = item.diff
            if diffi == "Legacy":  # 迷宫莉莉丝在info.tsv中有Legacy 跳过
                continue

            acc = item.acc
            if acc < 70:  # acc < 70% 不计入rks
                continue
            # self.log_write(f'当前处理歌曲{item.name}')
            if len(self.b27) < 27:
                heapq.heappush(self.b27, (item.rks, row))
            else:
                heapq.heappushpop(self.b27, (item.rks, row))

            if int(item.score) == int(1e6):
                # self.log_write(f"{combine_name}可能是合法phi3之一")
                if len(self.phi3) < 3:
                    heapq.heappush(self.phi3, (item.rks, row))
                else:
                    heapq.heappushpop(self.phi3, (item.rks, row))

        # 按单曲rks从大到小排序( 这不还是要排序吗...
        self.b27 = sorted(self.b27, key=lambda x: x[0], reverse=True)
        # self.log_write(f"b27是这些:{self.b27}")
        self.phi3 = sorted(self.phi3, key=lambda x: x[0], reverse=True)
        # self.log_write(f"phi3是这些:{self.phi3}")

        self.generate_improve_rks_advise()
        self.place_b27_phi3()

    # 计算指定难度的单曲可否推分
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
        acc = song_item.acc
        if int(acc) == 100:
            return None  # 已经满分的歌曲推不了分

        combine_name = song_item.combine_name
        level = song_item.level
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

    # 生成所有歌曲的提分建议
    def generate_improve_rks_advise(self):
        """生成所有歌曲的提分建议"""

        model = self.song_list_widget.model

        b27_dict: dict[str, list[str]] = {}  # 存储b27关键信息
        """b27_dict[组合名称]=['AT', 'IN'] 组合名称的歌在榜的难度"""
        min_b27_rks = MAX_LEVEL + 1  # b27地板对应rks

        for songi in self.b27:
            singal_rks, row = songi
            item = model.get_item(row)
            combine_name = item.combine_name
            diff = item.diff

            if combine_name not in b27_dict.keys():
                b27_dict[combine_name] = []

            b27_dict[combine_name].append(diff)
            min_b27_rks = min(min_b27_rks, singal_rks)
        # self.log_write(b27_dict)

        player_now_rks = round(
            self.total_rks / (len(self.b27) + len(self.phi3)), 4
        )  # 当前玩家准确rks值
        show_rks = int(player_now_rks * 100 + 0.5) / 100  # 游戏页面展示的rks值
        delta_rks = (
            show_rks + 0.005 - player_now_rks
        )  # 0.005保证游戏页面四舍五入后rks出现提升
        # self.log_write(f"需要提升的rks是:{delta_rks * 30}")
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
            # self.log_write(f"{item.name},{item.diff}如果{item.acc}->{next_acc}就可以加分喽~")

    # 布局b27 phi3卡片
    def place_b27_phi3(self):
        """布局b27 phi3卡片"""
        layout: QVBoxLayout = self.widgets["place_b27_phi3_page"]["main_layout"]

        while layout.count():  # 清除原先的布局
            child = layout.takeAt(0)
            if child.widget():
                try:
                    child.widget().deleteLater()
                except Exception:
                    pass

        player_rks_label = hint_and_frame_widget("当前rks:")
        self.widgets["place_b27_phi3_page"]["player_rks_label"] = player_rks_label
        player_rks_label.setFixedHeight(50)
        layout.addWidget(player_rks_label, 0)
        # layout.insertWidget(0, player_rks_label, 0)
        self.total_rks: float = 0.0

        b27_folder = folder("b27:", True)
        self.widgets["place_b27_phi3_page"]["b27_folder"] = b27_folder
        b27_folder.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Minimum
        )  # 竖直方向占据最小需求值
        b27_folder.setMinimumHeight(0)
        for singal_rks, row in self.b27:
            self.total_rks += singal_rks
            cardi = self.song_list_widget.build_card(row, is_expanded=False)
            if cardi:
                cardi.setMinimumHeight(0)
                # 完善玩家个人编辑的部分
                # selected_group = GROUP_INFO.get(cardi.combine_name, "").split("`")
                # now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(
                #     cardi.diff, ""
                # )
                # cardi.set_edited_info(selected_group,  now_comment)
                # cardi.right_func = self.link_and_show
                b27_folder.add_widget(cardi)
        layout.addWidget(b27_folder)

        phi3_folder = folder("phi3:", True)
        self.widgets["place_b27_phi3_page"]["phi3_folder"] = phi3_folder
        phi3_folder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        phi3_folder.setMinimumHeight(0)
        for singal_rks, row in self.phi3:
            self.total_rks += singal_rks
            cardi = self.song_list_widget.build_card(row, is_expanded=False)
            if cardi:
                cardi.setMinimumHeight(0)
                # now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(
                #     cardi.diff, ""
                # )
                # cardi.set_edited_info(selected_group, now_comment)
                # cardi.right_func = self.link_and_show
                phi3_folder.add_widget(cardi)
        layout.addWidget(phi3_folder)

        self.rks = round(self.total_rks / (len(self.b27) + len(self.phi3)), 4)
        rks_content_label = label(
            str(self.rks), {"font_size": 24, "background_color": (0, 0, 0, 0)}
        )
        player_rks_label.add_widget(rks_content_label)

        rks_label: label = self.widgets["account_page"][
            "rks_label"
        ]  # 同步更新账号页面的数据
        rks_label.set_text(f"rks: {int(self.rks * 100 + 0.5) / 100}")

        self.is_updated = True  # 更新完就是最新的啦
        self.switch_to(self.place_b27_phi3_page)

    # -----------更新信息卡片-----------
    def update_data(self):
        """更新数据"""
        if self.token == "":
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

        self.get_save_data()  # 更新存档数据

        # 还原搜索页面
        # self.reset_filter_result()
        self.place_record()  # 用更新过的数据重绘一遍搜索页面的数据

        # 还原编辑页面
        model = self.song_list_widget.model
        # print(model.item_dict)
        now_edit_card: song_info_card = self.widgets["edit_info_page"]["song_info_card"]
        new_songitem: SongItem = model.item_dict[
            f"{now_edit_card.combine_name}.{now_edit_card.diff}"
        ]
        new_card_in_edit: song_info_card = self.song_list_widget.build_card(
            new_songitem
        )
        self.link_and_show(new_card_in_edit)  # 自己show自己!

        now_calculate_card: song_info_card = self.widgets["score_calculate_page"][
            "song_info_card"
        ]
        new_songitem: SongItem = model.item_dict[
            f"{now_calculate_card.combine_name}.{now_calculate_card.diff}"
        ]
        new_card_in_edit: song_info_card = self.song_list_widget.build_card(
            new_songitem
        )
        self.link_and_show_score_page(new_card_in_edit)

        # 还原账号页面
        self.widgets["account_page"]["widget"].deleteLater()
        self.account_page = (
            self.init_account_page()
        )  # 刷新 肯定有token 已经刷新过一遍背景了

        self.draw_account_detail(
            self.widgets["account_page"]["widget"],
            self.widgets["account_page"]["layout"],
        )
        self.switch_to(self.home_page)  # 不写会跳转到编辑页面(link_and_show干的)

    # -----------初始化 可达分数计算 页面-----------
    def init_score_calculate_page(self) -> QWidget:
        """初始化可达分数计算页面"""
        self.widgets["score_calculate_page"] = {}
        widget = QWidget()
        self.widgets["score_calculate_page"]["widget"] = widget

        main_layout = QHBoxLayout(widget)
        self.widgets["score_calculate_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        # ------------------ 左边 分数输入及可能性展示 ------------------
        left_widget = QWidget()
        self.widgets["score_calculate_page"]["left_widget"] = left_widget
        main_layout.addWidget(left_widget)

        left_layout = QVBoxLayout(left_widget)
        self.widgets["score_calculate_page"]["left_layout"] = left_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        # 分数输入框
        score_input_elm = input_line("", "输入目标分数")
        self.widgets["score_calculate_page"]["score_input_elm"] = score_input_elm
        left_layout.addWidget(score_input_elm)

        # -------------排序依据及顺序选择框--------------
        sort_rely_widget = QWidget()
        self.widgets["score_calculate_page"]["sort_rely_widget"] = sort_rely_widget
        left_layout.addWidget(sort_rely_widget)

        sort_rely_layout = QHBoxLayout(sort_rely_widget)
        self.widgets["score_calculate_page"]["sort_rely_layout"] = sort_rely_layout

        # 排序顺序转换按钮
        sort_result_reverse_btn = SwitchButton()
        self.widgets["score_calculate_page"][
            "sort_result_reverse_btn"
        ] = sort_result_reverse_btn
        sort_result_reverse_btn.setOffText("当前:从小到大")
        sort_result_reverse_btn.setOnText("当前:从大到小")
        sort_result_reverse_btn.setChecked(True)  # 默认从大到小
        sort_result_reverse_btn.setStyleSheet(get_switch_button_style())
        sort_result_reverse_btn.label.setStyleSheet(
            f"""
            font-size: 23px;
            font-family: "{FONT_FAMILY["chi"]}";
            """
        )
        sort_result_reverse_btn.checkedChanged.connect(
            self.place_calculate_result
        )  # 每次改变都会重新布局
        sort_rely_layout.addWidget(sort_result_reverse_btn)  # 右侧控件

        # 排序依据选择框
        group_by_style = {
            "min_height": 24,
            "max_height": 35,
            "max_width": 130,
            "min_width": 130,
        }
        group_by_hint_style = {
            "font_size": 23,
            "min_width": 110,
            "max_width": 110,
        }
        sort_by_list = ["perfect数", "great数", "bad+miss数", "最大连击数"]
        sort_by = combobox(
            sort_by_list, "排序依据", group_by_style, group_by_hint_style
        )
        self.widgets["score_calculate_page"]["sort_by"] = sort_by
        sort_rely_layout.addWidget(sort_by)
        sort_by.bind_react_click_func(
            self.place_calculate_result
        )  # 每次切换的时候都重新布局

        # 表头
        label_title = score_display_widget(
            "Perfect数", "Great数", "bad+miss数", "最大连击数"
        )
        self.widgets["score_calculate_page"]["label_title"] = label_title
        left_layout.addWidget(label_title)

        # -------------- 结果布局部分 --------------
        result_display_scroll = SmoothScrollArea()
        self.widgets["score_calculate_page"][
            "result_display_scroll"
        ] = result_display_scroll
        left_layout.addWidget(result_display_scroll)
        result_display_scroll.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        result_display_scroll.setWidgetResizable(True)

        result_display_content = QWidget()
        self.widgets["score_calculate_page"][
            "result_display_content"
        ] = result_display_content
        result_display_scroll.setWidget(result_display_content)

        result_display_flow = FlowLayout(result_display_content)
        self.widgets["score_calculate_page"][
            "result_display_flow"
        ] = result_display_flow
        result_display_flow.setSpacing(0)
        result_display_flow.setContentsMargins(0, 0, 0, 0)

        start_calculate_btn = button("开始计算!")
        self.widgets["score_calculate_page"][
            "start_calculate_btn"
        ] = start_calculate_btn
        start_calculate_btn.bind_click_func(self.start_calculate)
        left_layout.addWidget(start_calculate_btn)

        # -------------- 右边 歌曲卡片部分 --------------
        right_widget = QWidget()
        self.widgets["score_calculate_page"]["right_widget"] = right_widget
        main_layout.addWidget(right_widget)

        display_layout = QVBoxLayout(right_widget)
        self.widgets["score_calculate_page"]["display_layout"] = display_layout

        example_song = song_info_card(
            imgpath=self.illustration_cache["云女孩.符白牙SiYFics"],
            diff_bg_path=self.page_bg_cache["IN"],  # 作为背景 这里的键就是跟难度相关
            name="云女孩",
            singal_rks="00.0000",
            acc="00.000",
            level="00.0",
            diff="IN",
            is_fc=True,
            score=1000000,
            index=0,
            composer="曲师名称",
            chapter="谱师名称",
            drawer="画师名称",
            is_expended=True,
            combine_name="云女孩.符白牙SiYFics",
            improve_advice=None,
            comment="豪庭好玩",
            group=["好歌!", "初见杀"],
        )
        display_layout.addWidget(example_song, 0, Qt.AlignCenter)
        self.widgets["score_calculate_page"]["song_info_card"] = example_song
        self.widgets["score_calculate_page"]["example_song"] = example_song

        self.widgets["score_calculate_page"]["score_display_widget_list"] = []
        return widget

    # 在分数可达页面显示指定的 song_info_card
    def link_and_show_score_page(self, info_card: song_info_card):
        """在分数可达页面显示指定的 song_info_card"""
        info_card_copy = info_card.copy()  # 自己写的深拷贝
        self.switch_to(self.score_calculate_page)
        # print(f'现存卡片{self.widgets["score_calculate_page"]["song_info_card"].name}')
        self.widgets["score_calculate_page"]["song_info_card"].deleteLater()
        self.widgets["score_calculate_page"]["song_info_card"] = info_card_copy
        # print(f'新卡片{self.widgets["score_calculate_page"]["song_info_card"].name}')
        display_layout: QVBoxLayout = self.widgets["score_calculate_page"][
            "display_layout"
        ]
        display_layout.addWidget(info_card_copy, 0, Qt.AlignCenter)

        # 同步编辑区的控件状态
        # group_ccb: CheckableComboBox = self.widgets["edit_info_page"]["group_ccb"]
        # selected_group = GROUP_INFO.get(info_card_copy.combine_name, "").split("`")
        # group_ccb.set_selected_items(selected_group)

        # comment_label: multiline_text = self.widgets["edit_info_page"]["comment_label"]
        # now_comment = COMMENT_INFO.get(info_card_copy.combine_name, {}).get(
        #     info_card_copy.diff, ""
        # )
        # comment_label.set_text(now_comment)

        # 把这些元数据写到展开区（展开区会在需要时创建）
        # info_card_copy.set_edited_info(selected_group, now_comment)

    # 布局可以达成目标分数的各项参数
    def place_calculate_result(self):
        """布局可以达成目标分数的各项参数"""

        # 清除前面的布局
        for score_resulti in self.widgets["score_calculate_page"][
            "score_display_widget_list"
        ]:
            try:
                score_resulti.deleteLater()
            except Exception:
                pass
        self.widgets["score_calculate_page"]["score_display_widget_list"] = []
        result_list: list[tuple[int, int, int, int]] = self.widgets[
            "score_calculate_page"
        ]["result_list"]
        result_display_flow: FlowLayout = self.widgets["score_calculate_page"][
            "result_display_flow"
        ]

        sort_result_reverse_btn: SwitchButton = self.widgets["score_calculate_page"][
            "sort_result_reverse_btn"
        ]
        sort_order = sort_result_reverse_btn.isChecked()  # checked 从大到小
        sort_by: combobox = self.widgets["score_calculate_page"]["sort_by"]
        sort_by = sort_by.get_content()
        link_map = {"perfect数": 0, "great数": 1, "bad+miss数": 2, "最大连击数": 3}
        result_list = sorted(
            result_list, key=lambda x: x[link_map[sort_by]], reverse=sort_order
        )
        for datai in result_list:
            perfect, great, bad_and_miss, max_count = datai
            score_display_widgeti = score_display_widget(
                perfect, great, bad_and_miss, max_count
            )
            self.widgets["score_calculate_page"]["score_display_widget_list"].append(
                score_display_widgeti
            )
            result_display_flow.addWidget(score_display_widgeti)
        InfoBar.success(
            title="计算完成",
            content=f"共有{len(result_list)}种可能!",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=window,
        )

    # 计算如何分配perfect great bad+miss max_count可以达到指定分数
    def start_calculate(self):
        """计算如何分配perfect great bad+miss max_count可以达到指定分数"""
        self.widgets["score_calculate_page"]["result_list"] = []  # 重置合法结果集
        aim_score = ""
        try:
            aim_score = int(
                self.widgets["score_calculate_page"]["score_input_elm"].text()
            )  # 获取用户输入值并尝试int

        except:
            InfoBar.warning(
                title="无效分数",
                content=f"分数不应该是{aim_score}喵!",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        if aim_score < 0 or aim_score > 1e6:  # 检查是否越界
            InfoBar.warning(
                title="无效分数",
                content=f"分数应该在0到100 0000内 而不是{aim_score}喵!",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        # 根据卡片获取在csv文件里用到的歌曲对应的键
        card: song_info_card = self.widgets["score_calculate_page"]["song_info_card"]
        song_key = f"{card.combine_name}.{card.diff}"
        df = pd.read_csv(
            resource_path(NOTE_COUNT_PATH),
            sep=",",
            header=None,
            encoding="utf-8",
            names=["tap", "hold", "drag", "flick", "sum"],
            index_col=0,
        )
        df = df.fillna("")
        # print(f"关键词是:{song_key}")
        row = df.loc[song_key]
        tap = int(row["tap"])
        hold = int(row["hold"])
        drag = int(row["drag"])
        flick = int(row["flick"])
        total_note = int(row["sum"])
        # total_note: int = tap + hold + drag + flick  # 总note数
        max_great: int = tap + hold  # 最多能great的数量
        result = []
        for bm in range(0, total_note + 1, 1):  # bad+miss数
            for g in range(
                0, min(max_great, total_note - bm) + 1
            ):  # great数 必定 <= perfect 数 小剪枝
                note_score: int = round(
                    (9e5 * (total_note - bm - g) + 585e3 * g) / total_note, 0
                )  # 判定分
                # mc = mac_count 最大连击数
                l: int = total_note // (bm + 1)
                r: int = total_note - bm
                need_score: int = aim_score - note_score
                while l <= r:  # 二分找max_count数
                    mid = l + ((r - l) >> 1)  # 连击数
                    mc_score = round((mid * 1e5) / total_note, 0)
                    if mc_score == need_score:
                        # print(total_note - bm - g, g, bm, mid)
                        # print(bm, g, mid)
                        result.append((total_note - bm - g, g, bm, mid))

                    if mc_score > need_score:
                        r = mid - 1
                    else:
                        l = mid + 1
        if not result:
            InfoBar.info(
                title="无解喵",
                content=f"{song_key}无法达到{aim_score}分(",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return
        self.widgets["score_calculate_page"]["result_list"] = result

        self.place_calculate_result()
        # for i in result:
        #     print(i)

    # -------------------搜索页面-------------------
    def init_search_page(self) -> QWidget:
        """初始化搜索页面"""
        self.widgets["search_page"] = {}
        self.widgets["search_page"]["card_and_folder"] = []

        widget = QWidget()
        self.widgets["search_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["search_page"]["main_layout"] = main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ------------------ 筛选条件选择区域 -------------------
        scroll_area = SmoothScrollArea()  # 滚动区域
        self.widgets["search_page"]["scroll_area"] = scroll_area
        main_layout.addWidget(scroll_area)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
        scroll_area.setFixedHeight(150)

        scroll_content_widget = QWidget()  # 滚动区域内容控件
        self.widgets["search_page"]["scroll_content_widget"] = scroll_content_widget
        scroll_area.setWidget(scroll_content_widget)

        flow_layout = FlowLayout(scroll_content_widget)  # 流式布局滚动区域内容
        self.widgets["search_page"]["flow_layout"] = flow_layout
        flow_layout.setSpacing(0)
        flow_layout.setContentsMargins(0, 0, 0, 0)

        filter_obj_list: list[filter_obj] = []
        self.widgets["search_page"]["filter_obj_list"] = filter_obj_list

        # 初始化第一个 filter_obj并加入逻辑链接选项
        filter_widget = filter_obj(0, filter_obj_list, flow_layout)
        filter_widget.attribution_choose_cbb.set_current_choose(
            filter_widget.filter_attribution_list.index(
                self.default_filter["attribution"]
            )
        )
        filter_widget.limit_choose_cbb.set_current_choose(
            filter_widget.filter_limit_list.index(self.default_filter["limit"])
        )
        filter_widget.adapt_limit_option()  # 手动adapt根据定好的东西布局补全器和列表
        filter_widget.limit_val_cbb.set_text(self.default_filter["value"])

        filter_widget.logical_cbb = combobox(
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
        filter_widget.main_layout.addWidget(
            filter_widget.logical_cbb
        )  # 第一个筛选条件的最后加上逻辑连接选项
        filter_obj_list.append(filter_widget)
        flow_layout.addWidget(filter_widget)

        # ----------------- 确认筛选按钮区域 ---------------
        filter_confirm_widget = QWidget()
        self.widgets["search_page"]["filter_confirm_widget"] = filter_confirm_widget
        main_layout.addWidget(filter_confirm_widget)

        filter_confirm_layout = QHBoxLayout(filter_confirm_widget)
        self.widgets["search_page"]["filter_confirm_layout"] = filter_confirm_layout
        filter_confirm_layout.setContentsMargins(0, 0, 0, 0)

        filter_btn_style = {
            "min_height": 45,
            "max_height": 45,
            "font_size": 28,
        }

        filter_from_all_song_btn = button(
            "从所有歌曲中筛一遍", filter_btn_style, resource_path(FILTER_ICON_PATH)
        )
        self.widgets["search_page"][
            "filter_from_all_song_btn"
        ] = filter_from_all_song_btn
        filter_confirm_layout.addWidget(filter_from_all_song_btn)
        filter_from_all_song_btn.set_icon_size(30, 30)
        filter_from_all_song_btn.bind_click_func(self.filter_from_all_song)

        filter_from_previous_song_btn = button(
            "从结果中继续筛选", filter_btn_style, resource_path(FILTER_AGAIN_ICON_PATH)
        )
        self.widgets["search_page"][
            "filter_from_previous_song_btn"
        ] = filter_from_previous_song_btn
        filter_confirm_layout.addWidget(filter_from_previous_song_btn)
        filter_from_previous_song_btn.set_icon_size(30, 30)
        filter_from_previous_song_btn.bind_click_func(self.filter_from_previous_song)

        # ------------------------------ 搜索结果展示区 ----------------------------
        result_widget = QWidget()
        self.widgets["search_page"]["result_widget"] = result_widget
        result_widget.setStyleSheet("""background-color: #DCDCDC;""")

        result_layout = QVBoxLayout(result_widget)
        self.widgets["search_page"]["result_layout"] = result_layout
        result_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(result_widget, 1)  # 所有的额外空间都给搜索结果栏

        # ---------------- 上层 分组/排序依据 ------------
        group_widget = QWidget()
        self.widgets["search_page"]["group_widget"] = group_widget
        result_layout.addWidget(group_widget, 0)  # 组合区域不给额外空间

        group_layout = QHBoxLayout(group_widget)
        self.widgets["search_page"]["group_layout"] = group_layout
        group_layout.setContentsMargins(0, 0, 5, 0)
        group_layout.setSpacing(6)

        # 重置按钮
        reset_page_btn_style = {
            "max_width": 120,
            "min_width": 120,
            "min_height": 40,
            "max_height": 40,
            "font_size": 30,
        }
        reset_page_btn = button("重置", reset_page_btn_style, resource_path(RESET_PATH))
        self.widgets["search_page"]["reset_page_btn"] = reset_page_btn
        reset_page_btn.bind_click_func(self.reset_filter_result)
        group_layout.addWidget(reset_page_btn)

        # 个数限制输入
        display_num_input = input_line(place_holder="个数限制")
        display_num_input.setFixedWidth(140)
        self.widgets["search_page"]["display_num_input"] = display_num_input
        group_layout.addWidget(display_num_input)

        # 排序顺序转换按钮
        sort_result_reverse_btn = SwitchButton()
        # sort_result_reverse_btn.hBox.setSpacing(0)
        self.widgets["search_page"]["sort_result_reverse_btn"] = sort_result_reverse_btn
        # sort_result_reverse_btn.setFixedWidth(10)
        sort_result_reverse_btn.setOffText("当前:从小到大")
        sort_result_reverse_btn.setOnText("当前:从大到小")
        sort_result_reverse_btn.setChecked(True)  # 默认从大到小
        sort_result_reverse_btn.setStyleSheet(get_switch_button_style())
        sort_result_reverse_btn.label.setStyleSheet(
            f"""
            font-size: 23px;
            font-family: "{FONT_FAMILY["chi"]}";
            """
        )
        sort_result_reverse_btn.checkedChanged.connect(
            self.place_record
        )  # 每次改变都会重新布局
        group_layout.addWidget(sort_result_reverse_btn)

        # 排序依据选择框
        group_by_style = {
            "min_height": 24,
            "max_height": 35,
            "max_width": 80,
            "min_width": 80,
        }
        group_by_hint_style = {
            "font_size": 23,
            "min_width": 100,
            "max_width": 100,
        }
        sort_by_list = ["无", "acc", "单曲rks", "得分", "定数"]
        sort_by = combobox(
            sort_by_list, "排序依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["sort_by"] = sort_by
        group_layout.addWidget(sort_by)
        sort_by.bind_react_click_func(self.place_record)  # 每次切换的时候都重新布局

        # 分组依据选择框
        group_by_list = [
            "无",
            "曲名",
            "曲师",
            "谱师",
            "画师",
            "难度",
            "评级",
            # "分组",
        ]
        group_by = combobox(
            group_by_list, "分组依据", group_by_style, group_by_hint_style
        )
        self.widgets["search_page"]["group_by"] = group_by
        group_layout.addWidget(group_by)
        group_by.bind_react_click_func(self.place_record)  # 每次切换的时候都重新布局

        # ---------------- 下层 卡片展示区 ------------
        result_display_scroll = SmoothScrollArea()
        self.widgets["search_page"]["result_display_scroll"] = result_display_scroll
        result_layout.addWidget(result_display_scroll)
        result_display_scroll.setStyleSheet(
            "QScrollArea{background: transparent; border: none}"
        )
        result_display_scroll.setWidgetResizable(True)

        result_display_content = QWidget()
        self.widgets["search_page"]["result_display_content"] = result_display_content
        result_display_scroll.setWidget(result_display_content)

        result_display_flow = FlowLayout(result_display_content)
        self.widgets["search_page"]["result_display_flow"] = result_display_flow
        result_display_flow.setSpacing(0)
        result_display_flow.setContentsMargins(0, 0, 0, 0)

        self.widgets["search_page"]["result_list"] = []
        return widget

    # 从全部歌曲中筛选符合条件的歌曲
    def filter_from_all_song(self):
        """从全部歌曲中筛选符合条件的歌曲"""
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

        if self.always_update:
            self.update_data()

        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        logical_link = filter_obj_list[0].logical_cbb.get_content()
        if not logical_link and len(filter_obj_list) > 1:
            # 存在多个筛选条件但未选择连接逻辑
            InfoBar.warning(
                title="连接逻辑未选择",
                content="使用多个筛选条件前请先选择连接逻辑",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        if len(filter_obj_list) == 1:
            # 单个筛选项时忽略连接逻辑
            logical_link = ""

        self.filter_result: set[int] = (
            set()
        )  # 或 逻辑就是从0开始添加 存储适合条件歌曲的index
        model = self.song_list_widget.model
        if logical_link == "并且(与)":
            self.filter_result = set(
                i for i in range(model.rowCount())
            )  # 与 逻辑就是从全集里面删掉各种东西

        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            if conditioni is None:
                return
            if logical_link == "并且(与)":
                result_list = self.filt_with_condition(self.filter_result, conditioni)
                self.filter_result = set(result_list)
            else:
                filt_result = self.filt_with_condition(
                    set(i for i in range(model.rowCount())), conditioni
                )
                for resulti in filt_result:
                    self.filter_result.add(resulti)

        self.place_record()

    # 在已有 self.filter_result 的基础上继续做筛选
    def filter_from_previous_song(self):
        """在已有 self.filter_result 的基础上继续做筛选"""
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
        if not hasattr(self, "filter_result"):
            InfoBar.warning(
                title="流程错误",
                content="先筛选一遍才能从之前的结果中继续筛选哦",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        if self.always_update:
            self.update_data()

        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        logical_link = filter_obj_list[0].logical_cbb.get_content()
        filter_result_copy = copy.deepcopy(self.filter_result)  # 深拷贝一份

        if logical_link != "并且(与)":
            # 如果不是 与 逻辑 则从空集开始累加
            self.filter_result = set()

        if not logical_link and len(filter_obj_list) > 1:
            # 存在多个筛选条件但未选择连接逻辑
            InfoBar.warning(
                title="连接逻辑未选择",
                content="使用多个筛选条件前请先选择连接逻辑",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=window,
            )
            return

        if len(filter_obj_list) == 1:
            logical_link = ""

        for filter_obji in filter_obj_list:
            conditioni = filter_obji.get_all_condition()
            if logical_link == "并且(与)":
                self.filter_result = set(
                    self.filt_with_condition(self.filter_result, conditioni)
                )  # 把自己放进去筛 然后覆盖自己
            else:
                result_list = self.filt_with_condition(
                    filter_result_copy, conditioni
                )  # 重复把备份放进去筛
                for resulti in result_list:
                    self.filter_result.add(resulti)

        self.place_record()

    # 从给定的序号中筛选出符合条件的序号并返回
    def filt_with_condition(
        self, song_info: set[int], condition: tuple[str, str, str]
    ) -> set[int]:
        """
        从给定的序号中筛选出符合条件的序号并返回

        入参:
            song_info: 待筛选的歌曲序号
            condition: (属性, 限制, 限制值)

        返回:
            匹配的集合
        """
        (attribution, limit, limit_val) = condition
        result = set()
        if attribution in ("曲名", "曲师", "谱师", "画师", "分组", "简评"):
            limit_val = limit_val.replace(" ", "").lower()

        model = self.song_list_widget.model
        for songi in song_info:  # 取出index
            item = model.get_item(songi)
            # combine_name = item.combine_name
            diffi = item.diff
            score = item.score
            acc = item.acc
            level = item.level
            is_fc = item.is_fc
            singal_rks = item.rks
            song_name = item.name
            composer = item.composer
            drawer = item.drawer
            chapter = item.chapter
            # groups = item.groups
            # comments = item.comment

            if attribution == "acc":
                if limit == "大于" and acc > float(limit_val):
                    result.add(songi)
                elif limit == "大于等于" and acc >= float(limit_val):
                    result.add(songi)
                elif limit == "小于" and acc < float(limit_val):
                    result.add(songi)
                elif limit == "小于等于" and acc <= float(limit_val):
                    result.add(songi)
                elif limit == "等于" and acc == float(limit_val):
                    result.add(songi)
                elif limit == "不等于" and acc != float(limit_val):
                    result.add(songi)
            elif attribution == "单曲rks":
                if limit == "大于" and singal_rks > float(limit_val):
                    result.add(songi)
                elif limit == "大于等于" and singal_rks >= float(limit_val):
                    result.add(songi)
                elif limit == "小于" and singal_rks < float(limit_val):
                    result.add(songi)
                elif limit == "小于等于" and singal_rks <= float(limit_val):
                    result.add(songi)
                elif limit == "等于" and singal_rks == float(limit_val):
                    result.add(songi)
                elif limit == "不等于" and singal_rks != float(limit_val):
                    result.add(songi)
            elif attribution == "得分":
                if limit == "大于" and score > int(limit_val):
                    result.add(songi)
                elif limit == "大于等于" and score >= int(limit_val):
                    result.add(songi)
                elif limit == "小于" and score < int(limit_val):
                    result.add(songi)
                elif limit == "小于等于" and score <= int(limit_val):
                    result.add(songi)
                elif limit == "等于" and score == int(limit_val):
                    result.add(songi)
                elif limit == "不等于" and score != int(limit_val):
                    result.add(songi)
            elif attribution == "定数":
                if limit == "大于" and level > float(limit_val):
                    result.add(songi)
                elif limit == "大于等于" and level >= float(limit_val):
                    result.add(songi)
                elif limit == "小于" and level < float(limit_val):
                    result.add(songi)
                elif limit == "小于等于" and level <= float(limit_val):
                    result.add(songi)
                elif limit == "等于" and level == float(limit_val):
                    result.add(songi)
                elif limit == "不等于" and level != float(limit_val):
                    result.add(songi)
            elif attribution == "评级":
                score_level = get_score_level(int(score), is_fc).value
                if limit == "等于" and score_level == limit_val:
                    result.add(songi)
                elif limit == "不等于" and score_level != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in score_level:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in score_level:
                    result.add(songi)
            elif attribution == "难度":
                if limit == "等于" and diffi == limit_val:
                    result.add(songi)
                elif limit == "不等于" and diffi != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in diffi:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in diffi:
                    result.add(songi)
            elif attribution == "曲名":
                sn = song_name.replace(" ", "").lower()
                if limit == "等于" and sn == limit_val:
                    result.add(songi)
                elif limit == "不等于" and sn != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in sn:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in sn:
                    result.add(songi)
            elif attribution == "曲师":
                comp = composer.replace(" ", "").lower()
                if limit == "等于" and comp == limit_val:
                    result.add(songi)
                elif limit == "不等于" and comp != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in comp:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in comp:
                    result.add(songi)
            elif attribution == "画师":
                dr = drawer.replace(" ", "").lower()
                if limit == "等于" and dr == limit_val:
                    result.add(songi)
                elif limit == "不等于" and dr != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in dr:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in dr:
                    result.add(songi)
            elif attribution == "谱师":
                chapter = chapter.replace(" ", "").lower()
                if limit == "等于" and chapter == limit_val:
                    result.add(songi)
                elif limit == "不等于" and chapter != limit_val:
                    result.add(songi)
                elif limit == "包含" and limit_val in chapter:
                    result.add(songi)
                elif limit == "不包含" and limit_val not in chapter:
                    result.add(songi)
            # elif attribution == "分组":
            #     groups_low = [g.replace(" ", "").lower() for g in groups]
            #     if limit == "包含" and limit_val in groups_low:
            #         result.add(songi)
            #     elif limit == "不包含" and limit_val not in groups_low:
            #         result.add(songi)
            # elif attribution == "简评":
            #     comments_low = comments.replace(" ", "").lower()
            #     if limit == "包含" and limit_val in comments_low:
            #         result.add(songi)
            #     elif limit == "不包含" and limit_val not in comments_low:
            #         result.add(songi)
        return result

    # 根据各种条件布局筛选结果
    def place_record(self):
        """根据各种条件布局筛选结果"""
        if not self.filter_result:
            return
        # print(f'搜索结果是{self.filter_result}')
        self.time_record = datetime.now()
        # 获取个数限制
        display_num: str = self.widgets["search_page"]["display_num_input"].text()
        if display_num.isdigit():
            display_num = int(display_num)
        elif display_num == "":
            display_num = 1e9
        else:
            self.log_write(f"个数限制 非法输入{display_num}")
            return
        # 获取 分组/排序 依据
        group_by = self.widgets["search_page"]["group_by"].get_content()
        sort_by = self.widgets["search_page"]["sort_by"].get_content()
        is_reversed = self.widgets["search_page"]["sort_result_reverse_btn"].isChecked()

        # 清理上次的布局
        # self.log_write(f'place前是{self.widgets["search_page"]["card_and_folder"]}')
        for song_cardi in self.widgets["search_page"]["card_and_folder"]:
            try:
                song_cardi.deleteLater()
            except Exception:
                pass
        self.widgets["search_page"]["card_and_folder"] = []

        result_display_flow: FlowLayout = self.widgets["search_page"][
            "result_display_flow"
        ]

        # 在批量插入期间关闭更新以避免频繁重绘
        self.widgets["search_page"]["scroll_content_widget"].setUpdatesEnabled(False)

        visited_folder: dict[str, list[folder, list[tuple[str, song_info_card]]]] = (
            {}
        )  # 键映射到folder 最内层的列表是folder里的所有card控件
        empty_sort_list: list[int | float | None, song_info_card] = (
            []
        )  # 当不分组时，直接保存要显示的卡片

        model = self.song_list_widget.model
        for row in self.filter_result:
            item = model.get_item(row)
            combine_name = item.combine_name
            diffi = item.diff
            score = item.score
            acc = item.acc
            level = item.level
            is_fc = item.is_fc
            singal_rks = item.rks

            # 排序依据
            sort_rely = None
            if sort_by == "acc":
                sort_rely = float(acc)
            elif sort_by == "单曲rks":
                sort_rely = float(singal_rks)
            elif sort_by == "得分":
                sort_rely = int(score)
            elif sort_by == "定数":
                sort_rely = float(level)

            cardi = self.song_list_widget.build_card(row, is_expanded=False)
            if cardi is None:
                continue
            # cardi.right_func = self.link_and_show
            self.widgets["search_page"]["card_and_folder"].append(cardi)

            # 玩家个人编辑的部分
            # selected_group = GROUP_INFO.get(cardi.combine_name, "").split("`")
            # now_comment = COMMENT_INFO.get(cardi.combine_name, {}).get(cardi.diff, "")
            # cardi.set_edited_info(selected_group, now_comment)

            # 计算分组标题与分组依据值
            if group_by == "曲名":
                title = cardi.name
                group_rely = combine_name
            elif group_by == "曲师":
                title = cardi.composer
                group_rely = cardi.composer
            elif group_by == "画师":
                title = cardi.drawer
                group_rely = cardi.drawer
            elif group_by == "谱师":
                title = cardi.chapter
                group_rely = cardi.chapter
            elif group_by == "难度":
                title = diffi
                group_rely = diffi
            elif group_by == "评级":
                score_level = get_score_level(int(score), is_fc)
                title = score_level.value
                group_rely = score_level.value
            # elif group_by == "分组":
            #     title = GROUP_INFO.get(combine_name, "").split("`")
            #     group_rely = GROUP_INFO.get(combine_name, "").split("`")
            else:
                title = None
                group_rely = None

            if group_by != "无":  # 需要分组
                if group_by == "分组":  # 根据玩家定义的组进行分组
                    # 一首歌可能在多个组里 可能需要把cardi放到多个folder中
                    for index in range(len(title)):
                        key = title[index]
                        if visited_folder.get(key) is None:  # 还没有建立folder
                            song_folderi = folder(key, expend=True)
                            self.widgets["search_page"]["card_and_folder"].append(
                                song_folderi
                            )
                            result_display_flow.addWidget(song_folderi)
                            visited_folder[key] = [song_folderi, []]  # 用过了
                        visited_folder[key][1].append((sort_rely, cardi))
                else:
                    if visited_folder.get(group_rely) is None:  # 还没有建立folder
                        song_folderi = folder(title, expend=True)
                        self.widgets["search_page"]["card_and_folder"].append(
                            song_folderi
                        )
                        result_display_flow.addWidget(song_folderi)
                        visited_folder[group_rely] = [song_folderi, []]
                    visited_folder[group_rely][1].append((sort_rely, cardi))
            else:  # 不需要分组 直接加到列表里就行
                empty_sort_list.append((sort_rely, cardi))
                # result_display_flow.addWidget(cardi)
        card_count = 0
        if group_by != "无":  # 需要分组
            # print("个数", min(display_num, len(visited_folder)))
            for folderi, cards in visited_folder.values():  # folder内排序
                # print(f"最后的结果是{cards}")
                if cards and cards[0][0] is not None:
                    cards = sorted(cards, key=lambda x: x[0], reverse=is_reversed)
                    cards = cards[: min(display_num, len(cards)) :]
                    card_count += len(cards)
                for _, cardi in cards:
                    folderi.add_widget(cardi)
        else:
            # print(f"最后的结果是{empty_sort_list}")
            if empty_sort_list and empty_sort_list[0][0] is not None:
                empty_sort_list = sorted(
                    empty_sort_list, key=lambda x: x[0], reverse=is_reversed
                )
                empty_sort_list = empty_sort_list[
                    : min(display_num, len(empty_sort_list)) :
                ]
            card_count += min(display_num, len(empty_sort_list))

            for _, cardi in empty_sort_list[: min(display_num, len(empty_sort_list)) :]:
                result_display_flow.addWidget(cardi)

        # 恢复滚动内容更新并完成布局
        self.widgets["search_page"]["scroll_content_widget"].setUpdatesEnabled(True)
        # self.log_write(f'place结束后是{self.widgets["search_page"]["card_and_folder"]}')

        end_time = datetime.now()
        time_difference = end_time - self.time_record
        total_seconds = time_difference.total_seconds()
        seconds = int(total_seconds % 60)
        microseconds = time_difference.microseconds
        InfoBar.info(
            title="布局完成",
            content=f"成功布局{card_count}个控件\n用时:{seconds:02d}.{microseconds:06d}s",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=window,
        )

    # 重置搜索结果
    def reset_filter_result(self):
        """重置搜索结果"""
        filter_obj_list: list[filter_obj] = self.widgets["search_page"][
            "filter_obj_list"
        ]
        # self.log_write(filter_obj_list)
        for idx in range(1, len(filter_obj_list)):  # 下标为0的留着
            filter_obj_list[idx].deleteLater()
            # self.log_write('delete')
        filter_obj_list = filter_obj_list[:1:]  # 只留第一个 还原

        # 重置带逻辑控件的这个
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
            "card_and_folder"
        ]:  # 先清除掉上一次布局的所有东西
            song_cardi.deleteLater()
        self.widgets["search_page"]["card_and_folder"] = []

    # -------------------编辑页面-------------------
    def init_edit_info_page(self) -> QWidget:
        self.widgets["edit_info_page"] = {}
        # widget = bg_widget(self.page_bg_cache["edit"])
        widget = QWidget()
        self.widgets["edit_info_page"]["widget"] = widget

        main_layout = QHBoxLayout(widget)
        self.widgets["edit_info_page"]["main_layout"] = main_layout

        # ----------------左侧：卡片信息区域----------------
        display_widget = QWidget()
        self.widgets["edit_info_page"]["display_widget"] = display_widget
        main_layout.addWidget(display_widget)

        display_layout = QVBoxLayout(display_widget)
        self.widgets["edit_info_page"]["display_layout"] = display_layout

        example_song = song_info_card(
            self.illustration_cache["云女孩.符白牙SiYFics"],
            self.page_bg_cache["IN"],  # 作为背景 这里的键就是跟难度相关
            "云女孩",
            "00.0000",
            "00.000",
            "00.0",
            "IN",
            True,
            1000000,
            0,
            "曲师名称",
            "谱师名称",
            "画师名称",
            True,
            "云女孩.符白牙SiYFics",
            comment="豪庭好玩",
            group=["好歌!", "初见杀"],
        )
        display_layout.addWidget(example_song, 0, Qt.AlignCenter)
        self.widgets["edit_info_page"]["song_info_card"] = example_song
        self.widgets["edit_info_page"]["example_song"] = example_song

        # ----------------右侧：编辑信息----------------
        edit_widget = QWidget()
        self.widgets["edit_info_page"]["edit_widget"] = edit_widget
        main_layout.addWidget(edit_widget)

        edit_layout = QVBoxLayout(edit_widget)
        self.widgets["edit_info_page"]["edit_layout"] = edit_layout

        group_label = label("分组:")
        edit_layout.addWidget(group_label)
        group_ccb = multi_check_combobox()
        self.widgets["edit_info_page"]["group_ccb"] = group_ccb

        self.get_userd_group()
        group_ccb.addItems(self.used_group)
        edit_layout.addWidget(group_ccb)

        comment_label = multiline_text()
        self.widgets["edit_info_page"]["comment_label"] = comment_label
        edit_layout.addWidget(comment_label)

        confirm_btn = button("保存更改", iconpath=resource_path(SAVE_ICON_PATH))
        self.widgets["edit_info_page"]["confirm_btn"] = confirm_btn
        edit_layout.addWidget(confirm_btn)
        confirm_btn.set_icon_size(30, 30)
        confirm_btn.bind_click_func(self.save_user_edit)

        return widget

    # 在编辑页面显示指定的 song_info_card
    def link_and_show(self, info_card: song_info_card):
        """在编辑页面显示指定的 song_info_card"""
        info_card_copy = info_card.copy()  # 自己写的深拷贝
        self.switch_to(self.edit_info_page)
        self.widgets["edit_info_page"]["song_info_card"].deleteLater()
        self.widgets["edit_info_page"]["song_info_card"] = info_card_copy
        display_layout: QVBoxLayout = self.widgets["edit_info_page"]["display_layout"]
        display_layout.addWidget(info_card_copy, 0, Qt.AlignCenter)

        # 同步编辑区的控件状态
        group_ccb: multi_check_combobox = self.widgets["edit_info_page"]["group_ccb"]
        selected_group = info_card_copy.group
        group_ccb.set_selected_items(selected_group)

        comment_label: multiline_text = self.widgets["edit_info_page"]["comment_label"]
        now_comment = info_card_copy.comment
        comment_label.set_text(now_comment)

    def get_userd_group(self):
        """获取已经存在的分组"""
        group_path = appdata_path(f"{self.user_name}_{GROUP_PATH}")
        if not os.path.exists(group_path) or os.path.getsize(group_path) == 0:
            shutil.copy2(resource_path(DEFUALT_GROUP), group_path)

        df = pd.read_csv(
            group_path,
            sep=",",
            header=None,
            encoding="utf-8",
            names=["c_name", "group"],
        )
        df = df.fillna("")
        df.set_index(df.columns[0], inplace=True)
        # used_group = set()
        self.used_group = set()
        for idx, rowi in df.iterrows():
            group_raw = str(rowi["group"])  # 组合名称 : 分组
            if group_raw:
                group_raw = group_raw.split("`")
                for i in group_raw:
                    self.used_group.add(i)
        print(f"已经使用过的分组是{self.used_group}")

    # 保存用户编辑后的信息
    def save_user_edit(self):
        """保存用户编辑后的信息"""

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
            return
        now_card: song_info_card = self.widgets["edit_info_page"]["song_info_card"]
        if not isinstance(now_card, song_info_card):
            return
        # 从编辑控件读取新值
        song_combine_name = now_card.combine_name
        diff = now_card.diff
        group_ccb: multi_check_combobox = self.widgets["edit_info_page"]["group_ccb"]
        new_group = "`".join(group_ccb.get_selected_items())
        new_comment = self.widgets["edit_info_page"]["comment_label"].get_plain_text()
        model = self.song_list_widget.model
        item: SongItem = model.item_dict[f"{now_card.combine_name}.{now_card.diff}"]
        item.comment = new_comment
        item.groups = group_ccb.get_selected_items()
        now_card.comment = new_comment
        now_card.group = item.groups
        self.song_list_widget.GROUP_INFO[now_card.combine_name] = item.groups
        self.song_list_widget.COMMENT_INFO[now_card.combine_name][
            now_card.diff
        ] = new_comment

        for i in range(model.rowCount()):
            if model.items[i].combine_name == now_card.combine_name:
                model.items[i] = item
                break
        try:
            group_path = appdata_path(f"{self.user_name}_{GROUP_PATH}")
            df = pd.read_csv(
                group_path,
                sep=",",
                header=None,
                encoding="utf-8",
                names=["combine_name", "group"],
                index_col=0,
            )
            df = df.fillna("")
            df.at[song_combine_name, "group"] = new_group
            df.to_csv(
                group_path,
                header=False,
                encoding="utf-8",
                index=True,
            )
        except Exception:
            pass

        try:
            comment_path = appdata_path(f"{self.user_name}_{COMMENT_PATH}")
            df = pd.read_csv(
                comment_path,
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
            colname = f"{diff}_comment"
            df.at[song_combine_name, colname] = new_comment
            df.to_csv(comment_path, header=False, encoding="utf-8", index=True)
        except Exception:
            pass

        self.get_userd_group()
        # print(f'玩家选择了的分组是{item.groups}')
        group_ccb.clear()
        group_ccb.addItems(self.used_group)
        group_ccb.set_selected_items(item.groups)

        self.place_b27_phi3()
        self.place_record()  # 更新搜索页面
        self.link_and_show(now_card)  # 自己show自己!
        now_card_in_edit: song_info_card = self.widgets["score_calculate_page"][
            "song_info_card"
        ]
        if (
            now_card_in_edit.combine_name == now_card.combine_name
            and now_card_in_edit.diff == now_card.diff
        ):  # 同一个卡片内容 需要更新
            self.link_and_show_score_page(now_card)  # 自己show自己!
        self.switch_to(self.edit_info_page)  # 否则会跳到分数可达页面

    # --------------- 账号页面 -------------------
    def transform_bakcground_name(self, text: str) -> str:
        if "." in text:  # 新版本背景 带点的
            if text[-2] == ".":
                try:
                    int(text[-1])
                    text = text[:-2:]
                except:
                    pass
            return text
        else:  # 旧版本的背景只有名称 需要遍历组合名称切换成新版的对应关系
            for combine_namei in COMBINE_NAME:
                name, composer = combine_namei.split(".")
                if name == text:
                    return combine_namei

    def init_account_page(self) -> QWidget:
        """生成账号页面的基本布局"""
        self.widgets["account_page"] = {}
        if self.token:  # 有token
            self.log_write(f"你的背景名称是{self.background_name}")

            # self.background_name = "Stasis.Maozon" # 调试用

            self.background_name = self.transform_bakcground_name(self.background_name)
            widget = bg_widget(self.illustration_cache[self.background_name], 10)
            self.widgets["account_page"]["widget"] = widget
        else:  # 没token 暂时用一下无背景的吧
            widget = QWidget()
            self.widgets["account_page"]["暂存"] = widget

        layout = QGridLayout(widget)
        self.widgets["account_page"]["layout"] = layout
        layout.setSpacing(0)

        # 二维码
        QRcode_img = ImageLabel(self.illustration_cache["QRcode_empty"])  # 空二维码
        self.widgets["account_page"]["QRcode_img"] = QRcode_img
        QRcode_img.setFixedSize(410, 410)
        QRcode_img.setAlignment(Qt.AlignCenter)
        layout.addWidget(QRcode_img)

        # 生成授权二维码按钮
        login_confirm_btn = button("点击这里开始授权")
        self.widgets["account_page"]["login_confirm_btn"] = login_confirm_btn
        layout.addWidget(login_confirm_btn)
        login_confirm_btn.bind_click_func(self.start_login)

        if self.token:
            login_confirm_btn.hide()  # 如果已经有了token就不用再获取了
            QRcode_img.hide()
            self.draw_account_detail(widget, layout)  #

        return widget

    # 绘制账号详细信息
    def draw_account_detail(self, widget: bg_widget, layout: QGridLayout):
        """绘制账号详细信息(头像 名称 rks 简介...)"""
        if self.avatar:
            original_pixmap = QPixmap(
                resource_path(AVATER_IMG_PREPATH + self.avatar + ".png")
            )
            avatar_widget = AvatarWidget(original_pixmap, widget)
            self.widgets["account_page"]["avatar_widget"] = avatar_widget
            avatar_widget.setFixedSize(110, 110)
            layout.addWidget(avatar_widget, 0, 0, 1, 1)
        else:
            self.log_write("无头像")

        lable_style = {
            "font_size": 33,
            "background_color": (255, 255, 255, 0.8),
        }

        if self.challengemode_rank:  # 挑战模式评级拆分
            bg_color = self.challengemode_rank[0]
            if bg_color == "0":
                bg_img = self.page_bg_cache["white"]
            elif bg_color == "1":
                bg_img = self.page_bg_cache["EZ"]
            elif bg_color == "2":
                bg_img = self.page_bg_cache["HD"]
            elif bg_color == "3":
                bg_img = self.page_bg_cache["IN"]
            elif bg_color == "4":
                bg_img = self.page_bg_cache["AT"]
            elif bg_color == "5":
                bg_img = self.page_bg_cache["colorful"]

            levelsum = self.challengemode_rank[1::]
            challenge_widget = bg_widget(bg_img.scaled(130, 46), 0)
            challenge_widget.setFixedSize(130, 46)
            layout.addWidget(challenge_widget, 1, 0, 1, 1)

            challenge_part_layout = QHBoxLayout(challenge_widget)
            cahllenge_text_label = label(
                levelsum,
                {
                    "font_size": 40,
                    "font_color": (255, 255, 255, 1),
                    "max_height": 42,
                },
            )
            challenge_part_layout.addWidget(
                cahllenge_text_label, alignment=Qt.AlignHCenter | Qt.AlignTop
            )

        name_rks_widget = QWidget()
        layout.addWidget(name_rks_widget, 0, 1, 1, 2)
        name_rks_layout = QVBoxLayout(name_rks_widget)
        name_rks_layout.setSpacing(0)

        if self.user_name:
            name_label = label(self.user_name, lable_style)
            name_label.setAlignment(Qt.AlignLeft)
            # name_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            name_rks_layout.addWidget(name_label)
            name_label.adjustSize()

        rks_label = label(self.rks if self.rks else "", lable_style)
        # rks_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        rks_label.setAlignment(Qt.AlignCenter)
        self.widgets["account_page"]["rks_label"] = rks_label
        name_rks_layout.addWidget(rks_label)

        self_introduction_label_style = {
            "font_size": 23,
            "min_width": 450,
            "max_width": 450,
            "max_height": 500,
            "background_color": (255, 255, 255, 0.8),
        }
        self_introduction_label = label(
            self.user_introduction, self_introduction_label_style
        )
        self_introduction_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self_introduction_label, 2, 0, 5, 4)
        self_introduction_label.adjustSize()

        # ------------------ 打歌统计部分 -------------------
        summary_label_style = {
            "font_size": 26,
            "max_width": 110,
            "min_width": 110,
            "background_color": (255, 255, 255, 0.8),
            "other": """border-width: 2px;
                    border-style: solid;
                    border-color: rgba(138, 225, 252, 1);""",
        }
        # -------第1行 标题-------
        empty_label = label("", summary_label_style)
        layout.addWidget(empty_label, 2, 4, 1, 1)

        clear_label = label("Cleared", summary_label_style)
        clear_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(clear_label, 2, 5, 1, 1)

        FC_label = label("FC", summary_label_style)
        FC_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(FC_label, 2, 6, 1, 1)

        AP_label = label("AP", summary_label_style)
        AP_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(AP_label, 2, 7, 1, 1)

        # -------第2行 EZ统计数据-------
        EZ_label = label("EZ", summary_label_style)
        EZ_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(EZ_label, 3, 4, 1, 1)

        EZclear_label = label(self.EZ_statistical_data[0], summary_label_style)
        EZclear_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(EZclear_label, 3, 5, 1, 1)

        EZFC_label = label(self.EZ_statistical_data[1], summary_label_style)
        EZFC_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(EZFC_label, 3, 6, 1, 1)

        EZAP_label = label(self.EZ_statistical_data[2], summary_label_style)
        EZAP_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(EZAP_label, 3, 7, 1, 1)

        # -------第3行 HD统计数据-------
        HD_label = label("HD", summary_label_style)
        HD_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(HD_label, 4, 4, 1, 1)

        HDclear_label = label(self.HD_statistical_data[0], summary_label_style)
        HDclear_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(HDclear_label, 4, 5, 1, 1)

        HDFC_label = label(self.HD_statistical_data[1], summary_label_style)
        HDFC_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(HDFC_label, 4, 6, 1, 1)

        HDAP_label = label(self.HD_statistical_data[2], summary_label_style)
        HDAP_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(HDAP_label, 4, 7, 1, 1)

        # -------第4行 IN统计数据-------
        IN_label = label("IN", summary_label_style)
        IN_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(IN_label, 5, 4, 1, 1)

        INclear_label = label(self.IN_statistical_data[0], summary_label_style)
        INclear_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(INclear_label, 5, 5, 1, 1)

        INFC_label = label(self.IN_statistical_data[1], summary_label_style)
        INFC_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(INFC_label, 5, 6, 1, 1)

        INAP_label = label(self.IN_statistical_data[2], summary_label_style)
        INAP_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(INAP_label, 5, 7, 1, 1)

        # -------第5行 AT统计数据-------
        AT_label = label("AT", summary_label_style)
        AT_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(AT_label, 6, 4, 1, 1)

        ATclear_label = label(self.AT_statistical_data[0], summary_label_style)
        ATclear_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(ATclear_label, 6, 5, 1, 1)

        ATFC_label = label(self.AT_statistical_data[1], summary_label_style)
        ATFC_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(ATFC_label, 6, 6, 1, 1)

        ATAP_label = label(self.AT_statistical_data[2], summary_label_style)
        ATAP_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(ATAP_label, 6, 7, 1, 1)

        log_out_btn = button("退出登录")
        log_out_btn.bind_click_func(self.log_out)
        self.widgets["account_page"]["log_out_btn"] = log_out_btn
        layout.addWidget(log_out_btn, 7, 0, 1, 2)

    # 开始登入
    def start_login(self):
        """开始登入"""
        self.QRCode_info = TapTapLogin.RequestLoginQRCode()
        # self.log_write(f"获取二维码信息成功：{self.QRCode_info}")

        qrcod = make(self.QRCode_info["qrcode_url"]).convert("RGBA")
        # self.log_write(f'二维码的种类是{type(qrcod)}')
        # 3. 获取图像的原始数据、宽度和高度
        #    'raw' 指定原始字节顺序，'RGBA' 指定解释这些字节的方式
        data = qrcod.tobytes("raw", "RGBA")
        width, height = qrcod.size
        #    QImage.Format_RGBA8888 表示每个像素 4 字节，顺序为 RGBA
        qimage = QImage(data, width, height, QImage.Format_RGBA8888)
        # 5. 从 QImage 创建 QPixmap
        qpixmap = QPixmap.fromImage(qimage)
        # self.log_write("添加二维码成功")
        self.widgets["account_page"]["QRcode_img"].setPixmap(qpixmap)

        self.login_check_timer = QTimer()
        self.login_interval = self.QRCode_info["interval"] * 1000
        self.login_check_timer.setInterval(self.login_interval)
        self.login_check_timer.timeout.connect(self.check_login)
        self.login_check_timer.start()

    # 检测是否授权
    def check_login(self):
        Login_info = TapTapLogin.CheckQRCodeResult(self.QRCode_info)
        if Login_info.get("data"):
            self.login_check_timer.stop()
            Profile = TapTapLogin.GetProfile(Login_info["data"])
            Token = TapTapLogin.GetUserData({**Profile["data"], **Login_info["data"]})

            # 保存token
            self.token = Token["sessionToken"]

            self.get_save_data()  # 获取存档数据并初始化变量
            self.token_file[self.user_name] = self.token
            self.token_file["last_user"] = self.user_name
            print("token文件内容是", self.token_file)
            with open(appdata_path(TOKEN_PATH), "w", encoding="utf-8") as f:
                json.dump(  # dump是写回
                    self.token_file,
                    f,
                    ensure_ascii=False,  # 支持中文
                    indent=4,  # 格式化缩进 便于阅读
                )

            self.widgets["account_page"]["QRcode_img"].hide()
            self.widgets["account_page"]["login_confirm_btn"].hide()

            # self.background_name = "Stasis.Maozon"
            self.background_name = self.transform_bakcground_name(self.background_name)
            widget = bg_widget(self.illustration_cache[self.background_name])
            self.widgets["account_page"]["widget"] = widget
            self.account_page = widget
            widget.setLayout(
                self.widgets["account_page"]["layout"]
            )  # 不是layout.setParent 而是要widget.setLayout
            self.widgets["account_page"]["暂存"].deleteLater()

            self.draw_account_detail(widget, self.widgets["account_page"]["layout"])
            self.switch_to(self.account_page)  # 不写会报错

        else:
            InfoBar.info(
                title="用户未登录",
                content="二维码登录未授权...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=self.login_interval,
                parent=window,
            )

    # 玩家登出后还原页面及变量
    def log_out(self):
        """玩家登出后还原页面及变量"""
        with open(appdata_path(TOKEN_PATH), "w", encoding="utf-8") as f:  # 清空tokn记录
            self.token_file[self.user_name] = ""
            json.dump(
                self.token_file, f, ensure_ascii=False, indent=4  # 支持中文
            )  # 格式化缩进 便于阅读)
            self.init_variable()  # 还原所有与账号相关的变量

            # 还原主页
            self.widgets["place_b27_phi3_page"]["player_rks_label"].deleteLater()
            self.widgets["place_b27_phi3_page"]["b27_folder"].deleteLater()
            self.widgets["place_b27_phi3_page"]["phi3_folder"].deleteLater()

            # 还原分数可达页面
            self.link_and_show_score_page(
                self.widgets["score_calculate_page"]["example_song"]
            )
            self.widgets["score_calculate_page"]["result_list"] = []  # 还原合法结果
            result_display_flow: FlowLayout = self.widgets["score_calculate_page"][
                "result_display_flow"
            ]
            while result_display_flow.count():  # 删掉所有展示的结果
                print("删除结果1个")
                item = result_display_flow.takeAt(0)
                widget = item.widget()

                if widget is not None:
                    widget.deleteLater()

            self.widgets["score_calculate_page"]["example_song"]

            score_input_elm: input_line = self.widgets["score_calculate_page"][
                "score_input_elm"
            ]
            score_input_elm.clear()

            # 还原搜索页面
            self.reset_filter_result()

            # 还原编辑页面
            self.link_and_show(self.widgets["edit_info_page"]["example_song"])

            # 还原账号页面
            self.widgets["account_page"]["widget"].deleteLater()
            self.account_page = self.init_account_page()

            self.switch_to(self.account_page)

    # --------------- 设置页面 -------------------
    def init_setting_page(self) -> QWidget:
        self.widgets["setting_page"] = {}
        widget = QWidget()
        self.widgets["setting_page"]["widget"] = widget

        main_layout = QVBoxLayout(widget)
        self.widgets["setting_page"]["main_layout"] = main_layout

        segment = SegmentedWidget(widget)
        self.widgets["setting_page"]["segment"] = segment
        main_layout.addWidget(segment)
        segment.setFixedHeight(25)

        self.stacked_layout = QStackedLayout()
        self.widgets["setting_page"]["stacked_layout"] = self.stacked_layout
        main_layout.addLayout(self.stacked_layout)

        segment.currentItemChanged.connect(self.on_segment_changed)
        segment.addItem("main_setting_widget", "总设置")
        segment.addItem("search_setting_widget", "搜索页设置")
        segment.setCurrentItem("main_setting_widget")

        # -------------- 主设置页面 --------------
        main_setting_widget = QWidget()
        self.widgets["setting_page"]["main_setting_widget"] = main_setting_widget

        main_setting_layout = QVBoxLayout(main_setting_widget)
        self.widgets["setting_page"]["main_setting_layout"] = main_setting_layout

        # 常更新切换按钮
        always_update_sbtn = SwitchButton()
        self.widgets["setting_page"]["always_update_sbtn"] = always_update_sbtn
        always_update_sbtn.setOffText("当前:懒更新")
        always_update_sbtn.setOnText("当前:常更新")
        always_update_sbtn.setChecked(self.always_update)
        always_update_sbtn.setStyleSheet(get_switch_button_style())
        always_update_sbtn.label.setStyleSheet(
            f"""
            font-size: 23px;
            font-family: "{FONT_FAMILY["chi"]}";
            """
        )
        main_setting_layout.addWidget(always_update_sbtn)

        # 设置默认启动页面
        cbb_style = {
            "max_width": 110,
            "min_width": 110,
            "min_height": 35,
            "max_height": 35,
            "font_size": 20,
        }
        label_style = {"min_width": 210, "max_width": 210, "font_size": 24}
        default_open_page = combobox(
            [
                "主页",
                "rks组成页",
                "分数计算页",
                "搜索页面",
                "编辑页面",
                "账号页面",
                "设置页面",
            ],
            "设置默认启动页面",
            cbb_style,
            label_style,
        )
        self.widgets["setting_page"]["default_open_page"] = default_open_page
        main_setting_layout.addWidget(default_open_page)
        main_setting_layout.setAlignment(Qt.AlignLeft)

        main_setting_layout.addStretch(1)

        self.stacked_layout.addWidget(main_setting_widget)  # index 0

        # -------------- 搜索设置页面 --------------
        search_setting_widget = QWidget()
        self.widgets["setting_page"]["search_setting_widget"] = search_setting_widget

        search_setting_layout = QVBoxLayout(search_setting_widget)
        self.widgets["setting_page"]["search_setting_layout"] = search_setting_layout

        default_filter_obj = filter_obj(0, [], FlowLayout)
        self.widgets["setting_page"]["default_filter_obj"] = default_filter_obj
        default_filter_obj.add_btn.hide()
        default_filter_obj.delete_btn.hide()
        default_filter_obj.attribution_choose_cbb.set_hint_text("设置默认筛选条件")

        default_filter_obj.attribution_choose_cbb.set_current_choose(
            default_filter_obj.filter_attribution_list.index(
                self.default_filter["attribution"]
            )
        )
        default_filter_obj.limit_choose_cbb.set_current_choose(
            default_filter_obj.filter_limit_list.index(self.default_filter["limit"])
        )
        default_filter_obj.adapt_limit_option()  # 手动adapt根据定好的东西布局补全器和列表
        default_filter_obj.limit_val_cbb.set_text(self.default_filter["value"])
        # default_filter_obj.attribution_choose_cbb.setMaximumWidth(160)
        default_filter_obj.setFixedHeight(65)
        search_setting_layout.addWidget(default_filter_obj)

        search_setting_layout.addStretch(1)

        self.stacked_layout.addWidget(search_setting_widget)  # index 1

        # ------------------ 保存按钮 ------------------
        confirm_btn = button("保存更改", iconpath=resource_path(SAVE_ICON_PATH))
        self.widgets["setting_page"]["confirm_btn"] = confirm_btn
        main_layout.addWidget(confirm_btn)
        confirm_btn.set_icon_size(30, 30)
        confirm_btn.bind_click_func(self.save_user_setting)

        # 默认显示第一个页面
        self.stacked_layout.setCurrentIndex(0)

        return widget

    # 保存用户设置
    def save_user_setting(self):
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

        setting_file_path = appdata_path(SETTING_PATH)

        # 读取现有设置
        with open(setting_file_path, "r", encoding="utf-8") as f:
            setting_file = json.load(f)

        # 修改设置
        user_setting = setting_file[self.user_name]
        main_setting = user_setting["main_setting"]

        # 常更新写入
        always_update_sbtn: SwitchButton = self.widgets["setting_page"][
            "always_update_sbtn"
        ]
        main_setting["always_update"] = always_update_sbtn.isChecked()

        # 默认开屏页面写入
        default_open_page: combobox = self.widgets["setting_page"]["default_open_page"]
        default_open_page_text = default_open_page.get_content()

        page_map = {
            "主页": "home_page",
            "rks组成页": "place_b27_phi3_page",
            "分数计算页": "score_calculate_page",
            "搜索页面": "search_page",
            "编辑页面": "edit_info_page",
            "账号页面": "account_page",
            "设置页面": "setting_page",
        }
        main_setting["default_open_page"] = page_map[default_open_page_text]

        # 搜索页默认筛选条件写入
        search_page_setting = user_setting["search_page_setting"]
        default_filter = search_page_setting["default_filter"]
        default_filter_obj: filter_obj = self.widgets["setting_page"][
            "default_filter_obj"
        ]
        attribution, limit, value = default_filter_obj.get_all_condition()
        default_filter["attribution"] = attribution
        default_filter["limit"] = limit
        default_filter["value"] = value

        # 写回文件
        with open(setting_file_path, "w", encoding="utf-8") as f:
            json.dump(  # dump是写回
                setting_file,
                f,
                ensure_ascii=False,  # 支持中文
                indent=4,  # 格式化缩进 便于阅读
            )

        InfoBar.success(
            title="成功保存",
            content="用户设置已保存",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=window,
        )

    # 响应设置页切换
    def on_segment_changed(self):
        segment: SegmentedWidget = self.widgets["setting_page"]["segment"]
        route_key = segment.currentRouteKey()

        # 获取页面索引
        if route_key == "main_setting_widget":
            self.stacked_layout.setCurrentIndex(0)
        elif route_key == "search_setting_widget":
            self.stacked_layout.setCurrentIndex(1)


# ---------- 程序入口 ----------
if __name__ == "__main__":
    window = MainWindow()
    sys.exit(app.exec_())
