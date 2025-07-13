"""
问题:爬虫报错之后退出但是进程未完全关闭

重名的内容需要进行区分: 曲名(曲师) 增添的时候名称上的曲师无关紧要，真正判重看的是曲师那一栏的东西
"""

import re
import os
import sys
import time
import queue
import heapq
import requests
import threading
import subprocess
import concurrent.futures
import customtkinter as ctk
from PIL import Image
from lxml import etree
from pathlib import Path
from tkinter import messagebox
from selenium import webdriver
from threading import Semaphore
from CTkToolTip import CTkToolTip
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from dependencies.consts import *
from dependencies.test_model import valid_test, split_complex_name

py_path = PATH["database_code"]
xmlpath = PATH["xml"]
image_path_prefix = PATH["image_prefix"]
ctitle_font = FONT["ctitle_font"]
ctitle_size = FONT["ctitle_size"]
ctext_font = FONT["ctext_font"]
ctext_size = FONT["ctext_size"]
find_by_id = etree.XPath("//song[@id=$song_id]")  # 预编译以减少处理时间
find_attri = etree.XPath('./*[name()=$attri][text()!="无"][normalize-space()]')
sys.path.append(str(Path(__file__).parent))


class ctktoplevel_frame(ctk.CTkToplevel):  # 副窗口
    def __init__(self, master, title):
        super().__init__(master)
        self.title = title

    def set_size(self, x, y, dx, dy):
        self.geometry("{}x{}+{}+{}".format(x, y, dx, dy))


class combobox_frame(ctk.CTkFrame):  # 下拉框+输入
    def __init__(self, master, title, button_name, values, default_value=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(height=32, fg_color="transparent")
        self.title = title
        self.button_name = button_name
        self.values = values
        self.default_value = default_value

        self.variable = ctk.StringVar(value=default_value)
        self.title = ctk.CTkLabel(
            self,
            text=self.title,
            fg_color="#F0FFFF",
            corner_radius=6,
            font=(ctitle_font, ctitle_size),
        )  # 提示标签
        self.title.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        self.option_menu = ctk.CTkComboBox(
            self,
            values=self.values,
            variable=self.variable,
            command=lambda _: self.click(button_name),
            font=(ctext_font, ctext_size),
        )  # 下拉框+输入
        self.option_menu.grid(row=0, column=1, padx=10, pady=2)
        self.option_menu.configure(width=300)

    def get(self):
        return self.option_menu.get()

    def set_size(self, width=300, height=32):
        self.option_menu.configure(width=width, height=height)

    def click(self, button_name):  # 响应选择选项 只起到一个根据输入更新控件内容的作用
        if button_name == "添加歌曲":
            complex_name = valid_test("名称", self.get(), phigros_root.nickname_dic)
            # print(complex_name)
            if complex_name == "无":
                return
            bracket_idx = complex_name.rindex("(")
            composer = complex_name[bracket_idx + 1 : -1 :]
            name = complex_name[:bracket_idx:]
            # click拿到的数据 所以一定能找到
            tree = etree.parse(xmlpath)
            xmlroot = tree.getroot()
            song_info = phigros_root.get_song_data(
                "complex_name", complex_name, xmlroot
            )
            if song_info is None:
                return
            avaliable_diff_list = []
            for diffi in DIFFICULTY_LIST:  # 按照频率排序 加进去的时候就是同样的顺序
                if diffi not in song_info.keys():
                    avaliable_diff_list.append(diffi)
            diff_var = ctk.StringVar(
                value=avaliable_diff_list[0]
            )  # 根据歌曲自动更新可用难度与对应曲师
            phigros_root.contain_item["增"]["难度"].option_menu.configure(
                values=tuple(avaliable_diff_list), variable=diff_var
            )

            name_var = ctk.StringVar(value=name)
            phigros_root.contain_item["增"]["名称"].option_menu.configure(
                variable=name_var
            )

            composer_var = ctk.StringVar(value=composer)
            phigros_root.contain_item["增"]["曲师"].option_menu.configure(
                variable=composer_var
            )

        elif button_name == "更改歌曲":
            song_name = valid_test("名称", self.get(), phigros_root.nickname_dic)
            if song_name == "无":
                return
            phigros_root.tip_song = song_name
            tree = etree.parse(xmlpath)  # 解析
            xmlroot = tree.getroot()
            song_info = phigros_root.get_song_data("complex_name", song_name, xmlroot)
            if song_info is None:
                return
            avaliable_diff_list = []

            for diffi in DIFFICULTY_LIST:  # 按照频率排序 加进去的时候就是同样的顺序
                if diffi in song_info.keys():
                    avaliable_diff_list.append(diffi)

            phigros_root.tip_diff = avaliable_diff_list[0]
            phigros_root.contain_item["改"]["难度"].option_menu.configure(
                values=avaliable_diff_list,
                variable=ctk.StringVar(value=phigros_root.tip_diff),
            )
            phigros_root.change_current_info()

            try:
                for widget in phigros_root.grid_item["改"]["曲绘窗口"].winfo_children():
                    widget.destroy()
                song_image = ctk.CTkImage(
                    light_image=Image.open(
                        image_path_prefix + f"{valid_test('文件路径', song_name)}.png"
                    ),
                    size=(454, 240),
                )
                image_label = ctk.CTkLabel(
                    phigros_root.grid_item["改"]["曲绘窗口"], text="", image=song_image
                )
                image_label.grid(row=0, column=0, pady=5, padx=10, sticky="nsew")
            except:
                messagebox.showwarning(
                    "更改歌曲页面", f"{song_info['名称']}未找到对应图片"
                )

        elif button_name == "删除歌曲":
            complex_name = valid_test("名称", self.get(), phigros_root.nickname_dic)
            if complex_name == "无":
                return
            tree = etree.parse(xmlpath)  # 解析
            xmlroot = tree.getroot()
            song_info = phigros_root.get_song_data(
                "complex_name", complex_name, xmlroot
            )
            if song_info is None:
                return
            diff = []
            for diffi in DIFFICULTY_LIST:
                if diffi in song_info.keys():
                    diff.append(diffi)
            phigros_root.contain_item["删"]["难度"].option_menu.configure(
                values=tuple(diff + [""])
            )
            try:
                for widget in phigros_root.grid_item["删"]["曲绘窗口"].winfo_children():
                    widget.destroy()
                song_image = ctk.CTkImage(
                    light_image=Image.open(
                        image_path_prefix
                        + f"{valid_test('文件路径', complex_name)}.png"
                    ),
                    size=(454, 240),
                )
                image_label = ctk.CTkLabel(
                    phigros_root.grid_item["删"]["曲绘窗口"], text="", image=song_image
                )
                image_label.grid(row=0, column=0, pady=5, padx=10, sticky="nsew")
            except:
                messagebox.showwarning(
                    "删除歌曲页面", f"{song_info['名称']}未找到对应图片"
                )

        elif button_name == "查找曲名":
            complex_name = valid_test("名称", self.get(), phigros_root.nickname_dic)
            if complex_name == "无":
                return
            tree = etree.parse(xmlpath)  # 解析
            xmlroot = tree.getroot()
            song_info = phigros_root.get_song_data(
                "complex_name", complex_name, xmlroot
            )
            if song_info is None:
                return
            # print(f'songinfo={song_info}')
            diff = []
            for diffi in DIFFICULTY_LIST:
                if diffi in song_info.keys():
                    diff.append(diffi)
            phigros_root.contain_item["查"]["名称-难度"].option_menu.configure(
                values=["All"] + diff, variable=ctk.StringVar(value=diff[0])
            )

        elif button_name == "展示数量":
            input_num = valid_test("每页条数", self.get())
            if input_num == "error":
                return
            phigros_root.show_num_perpage = input_num
            phigros_root.grid_find_rst()


class optionmenu_frame(ctk.CTkFrame):  # 下拉框
    def __init__(self, master, title, button_name, values, default_value=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(height=32, fg_color="transparent")
        self.title = title
        self.button_name = button_name
        self.values = values
        self.default_value = default_value
        self.radiobuttons = []
        self.variable = ctk.StringVar(value=default_value)

        Labeltitle = ctk.CTkLabel(
            self,
            text=self.title,
            fg_color="#F0FFFF",
            corner_radius=6,
            font=(ctitle_font, ctitle_size),
        )
        Labeltitle.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.option_menu = ctk.CTkOptionMenu(
            self,
            values=self.values,
            variable=self.variable,
            command=lambda x: self.click(button_name),
            font=(ctext_font, ctext_size),
        )
        self.option_menu.grid(row=0, column=1, padx=10, pady=5)

    def get(self):
        return self.option_menu.get()

    def set_size(self, width=140, height=28):
        self.option_menu.configure(width=width, height=height)

    def click(self, button_name):
        if button_name == "查找属性":
            seek_type = self.get()
            print(f"查找属性:指定{seek_type}")
            phigros_root.change_find_window(seek_type)

        if button_name == "更改属性":
            phigros_root.tip_attri = self.get()
            phigros_root.change_current_info()

        if button_name == "更改难度":
            phigros_root.tip_diff = self.get()
            phigros_root.change_current_info()


class entry_frame(ctk.CTkFrame):  # 单行输入框
    def __init__(self, master, title, placeholder_text="", default_value=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.configure(height=32, fg_color="transparent")
        self.title = title

        labeltitle = ctk.CTkLabel(
            self,
            text=self.title,
            fg_color="#F0FFFF",
            font=(ctitle_font, ctitle_size),
            corner_radius=6,
        )
        labeltitle.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.ctkentry = ctk.CTkEntry(
            self, placeholder_text=placeholder_text, font=(ctext_font, ctext_size)
        )
        if default_value != "":
            self.ctkentry.insert(
                0, default_value
            )  # 可以用var做 但是会覆盖掉place_holder内容
        self.ctkentry.configure(width=300, height=32)
        self.ctkentry.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

    def get(self):
        return self.ctkentry.get()

    def set_size(self, width=300, height=32):
        self.ctkentry.configure(width=width, height=height)


class muti_entry_frame(ctk.CTkFrame):  # 多行输入框
    def __init__(self, master, title, placeholder_text=""):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(height=32, fg_color="transparent")

        self.title = title
        self.placeholder_text = placeholder_text
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            fg_color="#F0FFFF",
            font=(ctitle_font, ctitle_size),
            corner_radius=6,
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.ctktext = ctk.CTkTextbox(
            self,
            wrap="word",
            font=(ctext_font, ctext_size),
            height=70,
            width=300,
            activate_scrollbars=True,
            border_width=2,
            corner_radius=8,
        )  # 自动换行模式：word/char/none

        if placeholder_text:
            self.ctktext.insert("0.0", placeholder_text)
            self.ctktext.bind("<FocusIn>", self.clear_placeholder)

        self.ctktext.bind("<FocusOut>", self.restore_placeholder)  # 光标移开
        self.ctktext.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

    def get(self):
        content = self.ctktext.get("0.0", "end-1c")  # 获取文本时去除末尾换行符
        return content.strip()

    def clear_placeholder(self, event):  # 清除提示文字
        if self.get() == self.placeholder_text:
            self.ctktext.delete("1.0", "end")  # 删除所有文字

    def restore_placeholder(self, event):
        if not self.get():
            self.ctktext.insert("0.0", self.placeholder_text)

    def set_size(self, x, y, dx, dy):
        self.width = x
        self.high = y
        self.geometry("{}x{}+{}+{}".format(x, y, dx, dy))


class expand_frame(ctk.CTkFrame):  # 文件夹类型控件
    def __init__(self, master, title, is_expanded=False, text_color="black"):
        super().__init__(master)
        self.title = title
        self.is_expanded = is_expanded
        self.text_color = text_color
        self.configure(border_width=4, border_color="#FFF5EE", fg_color="#fffef5")

        self.grid_columnconfigure(0, weight=1)  # 主窗口第0列可扩展
        self.header_button = ctk.CTkButton(
            self,
            text=f"▶{self.title}",
            command=self.change_expand,
            anchor="w",  # 文本对齐方式
            fg_color="transparent",
            text_color=text_color,
            font=(ctitle_font, ctitle_size),
            hover=False,  # 鼠标悬停不变色
        )
        self.header_button.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        self.content_frame = ctk.CTkFrame(
            self, fg_color="#E0FFFF", corner_radius=0
        )  # 内容部分
        self.content_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        if not is_expanded:
            self.content_frame.grid_remove()

    def change_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.header_button.configure(text=f"▼ {self.title}")
            self.content_frame.grid()
        else:
            self.header_button.configure(text=f"▶ {self.title}")
            self.content_frame.grid_remove()

    def set_color(self, fg_color):
        self.configure(fg_color=fg_color)


class phigros_data(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.configure(fg_color="#FFF5EE")
        self.title("phigros数据库")

        def refresh_root(event):
            self.destroy()
            subprocess.run(["python", py_path])

        self.bind("<F5>", refresh_root)
        self.bind("<Escape>", lambda event: self.destroy())

        self.grid_item = {
            "增": {},
            "删": {},
            "改": {},
            "查": {},
            "更": {},
        }  # 记录每个部分的主窗口 用来快捷隐藏/展示
        self.contain_item = {
            "增": {},
            "删": {},
            "改": {},
            "查": {},
            "更": {},
            "侧": {},
        }  # 记录其他小组件内容(tooltip) 便于在class外用 侧：侧边栏
        self.create_sidebar()
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=3, pady=0)
        self.content_frame.configure(fg_color="#F0FFF0")
        self.now_page_name = None  # 当前在主页面展示的页面

        self.sidebar_expanded = True
        self.tip_song = ""
        self.tip_attri = ""
        self.tip_diff = ""  # 查找时生成提示部分必备属性
        self.addable_song = {}
        self.ban_hid_attri = [
            "歌曲id",
            "章节",
            "bpm",
            "时长",
            "画师",
            "物量",
            "谱师",
            "俗称",
        ]  # 默认不在查找页面布局的属性 非常量

        tree = etree.parse(xmlpath)
        xmlroot = tree.getroot()  # 获取根节点
        self.get_song_list(xmlroot)
        for idxi in range(len(xmlroot)):
            avali_diff_list = []
            song_info = self.get_song_data("index", idxi, xmlroot)
            if song_info is not None:
                for diffi in DIFFICULTY_LIST:
                    if diffi not in song_info.keys():
                        avali_diff_list.append(diffi)
            if avali_diff_list:
                self.addable_song[f"{song_info['名称']}({song_info['曲师']})"] = (
                    avali_diff_list
                )
                if song_info["俗称"] != "无":
                    self.addable_song[f"{song_info['俗称']}"] = avali_diff_list
        # print(f'可添加难度歌曲:{self.addable_song}')

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.load_queue = queue.Queue()  # 线程安全的队列
        load_tasks = [
            (self.init_find_window, 40, "查"),
            (self.init_add_window, 20, "增"),
            (self.init_delete_window, 20, "删"),
            (self.init_change_window, 20, "改"),
        ]
        threading.Thread(
            target=self.init_all_window,  # 指定后台执行函数
            args=(load_tasks,),  # 传入init_all_window的参数 必须为可迭代对象
            daemon=True,  # 守护线程 主线程退出时自动终止
        ).start()
        self.check_load_finish()

    def set_size(self, x, y, dx, dy):
        self.geometry("{}x{}+{}+{}".format(x, y, dx, dy))

    def get_song_data(self, get_type, data, xmlroot):
        """{
        '歌曲id': '2',
        '名称': 'IndelibleScar',
        '曲师': 'Noah',
        '俗称': '无',
        '章节': 'Chapter EX-Paradigm:Reboot 精选集',
        'bpm': '223',
        '时长': '2:17',
        '画师': '兜',
        'AT': {
        '定数': '16.5',
        'acc': '99.08',
        '单曲rks': '15.8322',
        '简评': '无',
        '物量': '1207',
        '谱师': '上班睡大觉_Sleepyhead'_Sleepyhead'
        },
        'IN': {'定数': '15.3', 'acc': '99.11', '单曲rks': '14.7008', '简评': '无', '物量': '844', '谱师': 'Likey affected by Ancestral Xhronicle'},
        'HD': {'定数': '11.5', 'acc': '0', '单曲rks': '0', '简评': '无', '物量': '733', '谱师': 'Salt & Barbarianerman'},
        'EZ': {'定数': '7.0', 'acc': '0', '单曲rks': '0', '简评': '无', '物量': '316', '谱师': 'Clutter & Barbarianerman'}
        }"""
        song_info = {}
        if get_type == "complex_name":  # 单点搜索
            song_idx = self.song_dic[data]
            # song_lst = xmlroot.xpath(f'//song[@id="{song_idx}"]')
            song_lst = find_by_id(xmlroot, song_id=f"{song_idx}")
            if song_lst:
                song_elm = song_lst[0]
            else:
                print(f"id{song_idx}不存在 请检查数据库")
                return None
        elif get_type == "index":  # 遍历搜索
            try:
                song_elm = xmlroot[data]
            except:
                return None
        else:
            print(f"无效类型:{get_type}")
            return None

        song_info["歌曲id"] = song_elm.attrib["id"]

        # name_elm = song_elm.xpath('./名称[text()!="无"][normalize-space()]')
        name_elm = find_attri(song_elm, attri="名称")
        song_info["名称"] = name_elm[0].text if name_elm else "无"

        # composer_elm = song_elm.xpath('./曲师[text()!="无"][normalize-space()]')
        composer_elm = find_attri(song_elm, attri="曲师")
        song_info["曲师"] = composer_elm[0].text if composer_elm else "无"

        # nickname_elm = song_elm.xpath('./俗称[text()!="无"][normalize-space()]')
        nickname_elm = find_attri(song_elm, attri="俗称")
        song_info["俗称"] = nickname_elm[0].text if nickname_elm else "无"

        # chapter_elm = song_elm.xpath('./章节[text()!="无"][normalize-space()]')
        chapter_elm = find_attri(song_elm, attri="章节")
        song_info["章节"] = chapter_elm[0].text if chapter_elm else "无"

        # bpm_elm = song_elm.xpath('./bpm[text()!="无"][normalize-space()]')
        bpm_elm = find_attri(song_elm, attri="bpm")
        song_info["bpm"] = bpm_elm[0].text if bpm_elm else "0"

        # time_span_elm = song_elm.xpath('./时长[text()!="无"][normalize-space()]')
        time_span_elm = find_attri(song_elm, attri="时长")
        song_info["时长"] = time_span_elm[0].text if time_span_elm else "0:0"

        # drawer_elm = song_elm.xpath('./画师[text()!="无"][normalize-space()]')
        drawer_elm = find_attri(song_elm, attri="画师")
        song_info["画师"] = drawer_elm[0].text if drawer_elm else "无"

        for diffi in DIFFICULTY_LIST:
            avaliable_diff_elm = song_elm.find(diffi)
            if avaliable_diff_elm is not None:
                diff_attri = {}
                # level_elm = avaliable_diff_elm.xpath('./定数[text()!="无"][normalize-space()]')
                level_elm = find_attri(avaliable_diff_elm, attri="定数")
                diff_attri["定数"] = level_elm[0].text if level_elm else "0"

                # acc_elm = avaliable_diff_elm.xpath('./acc[text()!="无"][normalize-space()]')
                acc_elm = find_attri(avaliable_diff_elm, attri="acc")
                diff_attri["acc"] = acc_elm[0].text if acc_elm else "0"

                # singal_rks_elm = avaliable_diff_elm.xpath('./单曲rks[text()!="无"][normalize-space()]')
                singal_rks_elm = find_attri(avaliable_diff_elm, attri="单曲rks")
                diff_attri["单曲rks"] = (
                    singal_rks_elm[0].text if singal_rks_elm else "0"
                )

                # comment_elm = avaliable_diff_elm.xpath('./简评[text()!="无"][normalize-space()]')
                comment_elm = find_attri(avaliable_diff_elm, attri="简评")
                diff_attri["简评"] = comment_elm[0].text if comment_elm else "无"

                # note_cnt_elm = avaliable_diff_elm.xpath('./物量[text()!="无"][normalize-space()]')
                note_cnt_elm = find_attri(avaliable_diff_elm, attri="物量")
                diff_attri["物量"] = note_cnt_elm[0].text if note_cnt_elm else "0"

                # noter_elm = avaliable_diff_elm.xpath('./谱师[text()!="无"][normalize-space()]')
                noter_elm = find_attri(avaliable_diff_elm, attri="谱师")
                diff_attri["谱师"] = noter_elm[0].text if noter_elm else "无"

                song_info[diffi] = diff_attri

        # print(song_info)
        return song_info

    def get_song_list(self, xmlroot):
        self.song_dic = {}  # complex_name: id
        self.nickname_list = []
        self.nickname_dic = {}  # 俗称:name
        self.composer_list = []
        self.chapter_list = ["无"]
        for songi in xmlroot.iter("song"):
            # composer_lst = songi.xpath('./曲师[text()!="无"][normalize-space()]')
            composer_lst = find_attri(songi, attri="曲师")
            if composer_lst:
                composer = composer_lst[0].text
                self.composer_list.append(composer)  # 只会有一个结果
            # 没有name哪来的俗称对应关系?
            # name_lst = songi.xpath('./名称[text()!="无"][normalize-space()]')
            name_lst = find_attri(songi, attri="名称")
            if name_lst:
                name = name_lst[0].text
                if composer_lst:
                    self.song_dic[f"{name}({composer})"] = int(songi.attrib["id"])

                    # nickname_lst = songi.xpath('./俗称[text()!="无"][normalize-space()]')
                    nickname_lst = find_attri(songi, attri="俗称")
                    if nickname_lst:
                        nickname = nickname_lst[0].text
                        self.nickname_list.append(nickname)
                        self.nickname_dic[nickname] = (
                            f"{name}({composer})"  # 俗称和名称一定要一对一 如果没有其中的一个 宁可不记录
                        )

            # chapter_list = songi.xpath('./章节[text()!="无"][normalize-space()]')
            chapter_list = find_attri(songi, attri="章节")
            if chapter_list:
                chapter = chapter_list[0].text
                self.chapter_list.append(chapter)  # 只会有一个结果
        # print(self.song_dic)
        self.composer_list = list(set(self.composer_list))
        self.chapter_list = list(set(self.chapter_list))
        self.song_list = list(self.song_dic.keys())

    """侧边栏部分"""

    def create_sidebar(self):  # 创建侧边栏
        self.sidebar_frame = ctk.CTkFrame(self)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.configure(fg_color="#F0FFFF")

        rowi = 0
        self.change_hide_statue_btn = ctk.CTkButton(self.sidebar_frame, text="☰")
        self.change_hide_statue_btn.grid(
            row=rowi, column=0, pady=10, padx=10, sticky="nsew"
        )
        self.change_hide_statue_btn.grid_remove()
        rowi += 1
        tooltip = CTkToolTip(
            self.change_hide_statue_btn,
            message="折叠侧边栏",
            bg_color="gray90",
            font=(ctext_font, ctext_size),
            x_offset=30,
            y_offset=20,
        )
        self.contain_item["侧"]["折叠提示"] = tooltip

        pages = {  # 侧边栏按钮 关键字:提示内容
            "增": " 新增项目",
            "删": " 删除项目",
            "改": " 修改项目",
            "查": " 查询项目",
            "更": " 更新数据",
            "测": "测试模块",
        }

        icon_path = [
            "add song.png",
            "delete song.png",
            "change song.png",
            "find song.png",
            "grab.png",
            "test.png",
        ]
        tip_text = [
            "新增曲目或对已有曲子进行难度差分",
            "删除曲子或某个难度",
            "更改曲子的属性",
            "rks及各种属性查询",
            "通过萌娘百科中的内容更新数据库",
            "这是…测开?",
        ]
        idx = 0
        self.nav_buttons = {}  # 导航按钮
        for page_id, text in pages.items():
            icon_image = ctk.CTkImage(
                light_image=Image.open(PATH["icon_prefix"] + icon_path[idx]),
                size=(20, 20),
            )
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=text,
                command=lambda pid=page_id: self.switch_page(pid),
                anchor="w",
                image=icon_image,
                compound="left",
            )  # 图片在文字左侧
            btn.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
            rowi += 1
            self.nav_buttons[page_id] = btn  # 记录按钮地址 方便后续调用
            tooltip = CTkToolTip(
                btn,
                message=tip_text[idx],
                bg_color="gray90",
                font=(ctext_font, ctext_size),
                x_offset=30,
                y_offset=20,
            )
            idx += 1

        for i in self.nav_buttons.values():
            i.grid_remove()  # 默认全隐藏 初始化好一个显示一个

        self.nav_buttons["更"].grid()  # 开局就显示更新按钮
        self.show_test = False

        def show_test_part(event):
            if self.show_test:
                self.nav_buttons["更"].grid_remove()
                self.nav_buttons["测"].grid_remove()
            else:
                self.nav_buttons["更"].grid()
                self.nav_buttons["测"].grid()
            self.show_test = not self.show_test

        self.bind("<Shift-L>", show_test_part)  # 切换测试按钮可见性

    def change_siderbar_hide_statue(self):  # 切换侧边栏折叠状态
        if self.sidebar_expanded:
            self.sidebar_frame.configure(width=20)
            self.contain_item["侧"]["折叠提示"].configure(message="展开侧边栏")
            self.change_hide_statue_btn.configure(width=20)
            for keyi, vali in self.nav_buttons.items():
                if keyi == "测" or keyi == "更":
                    self.nav_buttons[keyi].grid_remove()
                vali.grid_remove()
        else:
            self.sidebar_frame.configure(width=250)
            self.contain_item["侧"]["折叠提示"].configure(message="折叠侧边栏")
            self.change_hide_statue_btn.configure(width=140)
            for keyi, vali in self.nav_buttons.items():
                if keyi == "测" or keyi == "更":
                    continue
                vali.grid()

        self.sidebar_expanded = not self.sidebar_expanded

    def switch_page(self, page_id):  # 切换主窗口显示页面
        if self.now_page_name != page_id and page_id in ["增", "删", "改", "查"]:
            self.view_page(self.now_page_name)  # 隐藏当前页
            # print(f"隐藏{self.now_page_name}")
            self.now_page_name = page_id
            self.view_page(page_id, True)
            # print(f"显示{page_id}")
            self.contain_item["查"]["设置按钮"].place_forget()
            if page_id == "查":
                self.change_find_window(self.find_now_page)
                self.contain_item["查"]["设置按钮"].place(
                    relx=0.30, rely=0.95, anchor="s", relwidth=0.7  # 相对宽度
                )
                self.contain_item["查"]["设置窗口"].withdraw()
        if page_id == "测":
            self.test()
        if page_id == "更":
            self.grab_info()

    def view_page(self, page_name, viewable=False):  # 更改页面可见性
        if page_name not in ["增", "删", "改", "查", "更"]:
            return
        for itemi in self.grid_item[page_name].values():
            if viewable:
                itemi.grid()
            else:
                itemi.grid_remove()

    """初始化界面"""

    def init_all_window(self, tasks):
        for func, weight, name in tasks:
            func()  # 初始化各个窗口
            self.load_queue.put(("progress", weight, name))  # 将进度更新放入队列

        self.load_queue.put(("complete", None))
        self.change_hide_statue_btn.configure(command=self.change_siderbar_hide_statue)

    def check_load_finish(self):  # 检查窗口是否初始化结束
        try:
            while True:
                data = self.load_queue.get_nowait()  # 非阻塞获取消息
                if data[0] == "progress":
                    print(data[2], "正在进行")
                else:
                    print("完成")
                    return
        except queue.Empty:
            self.after(50, self.check_load_finish)  # 50ms刷一次 直到完成

    """增"""

    def init_add_window(self):
        rowi = 0
        song_values = list(self.addable_song.keys())
        add_content_frame = ctk.CTkFrame(self.content_frame)
        add_content_frame.configure(fg_color="transparent")
        self.grid_item["增"]["窗口"] = add_content_frame

        add_name_choose = combobox_frame(
            add_content_frame, "歌曲名称*", "添加歌曲", song_values
        )
        add_name_choose.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["名称"] = add_name_choose
        rowi += 1

        def filter_values(event):  # 模糊搜索 过滤结果
            input_text = add_name_choose.get().strip().lower()
            if not input_text:
                add_name_choose.option_menu.configure(values=song_values)
                return
            filtered = [item for item in song_values if input_text in item.lower()]
            add_name_choose.option_menu.configure(values=filtered)

        add_name_choose.option_menu.bind("<KeyRelease>", filter_values)

        nickname_entry = entry_frame(add_content_frame, "歌曲俗称:", "儿童鞋垫")
        nickname_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["俗称"] = nickname_entry
        rowi += 1

        composer_choose = combobox_frame(
            add_content_frame, "曲师*", "增加曲师", self.composer_list
        )
        composer_choose.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["曲师"] = composer_choose
        rowi += 1

        bpm_entry = entry_frame(add_content_frame, "歌曲bpm:", "2333")
        bpm_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["bpm"] = bpm_entry
        rowi += 1

        time_span_entry = entry_frame(add_content_frame, "歌曲时长:", "7.21 or 07:21")
        time_span_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["时长"] = time_span_entry
        rowi += 1

        drawer_entry = entry_frame(add_content_frame, "曲绘画师:", "小咩兔")
        drawer_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["画师"] = drawer_entry
        rowi += 1

        chapter_choose = optionmenu_frame(
            add_content_frame, "章节名称", "增加章节", self.chapter_list, "无"
        )
        chapter_choose.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["章节"] = chapter_choose
        rowi += 1

        difficulty_choose = optionmenu_frame(
            add_content_frame, "歌曲难度*", "增加难度", DIFFICULTY_LIST, "IN"
        )
        difficulty_choose.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["难度"] = difficulty_choose
        rowi += 1

        level_entry = entry_frame(add_content_frame, "歌曲定数*", "11.3")
        level_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["定数"] = level_entry
        rowi += 1

        accuracy_entry = entry_frame(add_content_frame, "acc*", "66.6")
        accuracy_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["acc"] = accuracy_entry
        rowi += 1

        note_cnt_entry = entry_frame(add_content_frame, "歌曲物量:", "2085")
        note_cnt_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["物量"] = note_cnt_entry
        rowi += 1

        noter_entry = entry_frame(add_content_frame, "歌曲谱师:", "百九十八")
        noter_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["谱师"] = noter_entry
        rowi += 1

        comment_placeholder_text = "先生 买朵花吗~?"
        comment_entry = muti_entry_frame(
            add_content_frame, "简评一下:", comment_placeholder_text
        )
        comment_entry.grid(row=rowi, column=0, pady=5, padx=10, sticky="nsew")
        self.contain_item["增"]["简评"] = comment_entry
        rowi += 1

        def add_confirm():
            add_name = valid_test("名称", add_name_choose.get(), self.nickname_dic)
            add_name = split_complex_name(add_name)
            if add_name is None:
                return
            add_name = add_name[0]  # 取出 名称
            nickname = valid_test("俗名", nickname_entry.get())  # valid_test('', )
            composer = valid_test("曲师", composer_choose.get())
            bpm = valid_test("bpm", bpm_entry.get())
            time_span = valid_test("时长", time_span_entry.get())
            drawer = valid_test("画师", drawer_entry.get())
            chapter = valid_test("章节", chapter_choose.get())

            difficulty = difficulty_choose.get()
            # print(difficulty)
            level = valid_test("定数", level_entry.get())
            accuracy = valid_test("acc", accuracy_entry.get())
            comment = valid_test("简评", comment_entry.get())
            note_cnt = valid_test("物量", note_cnt_entry.get())
            noter = valid_test("谱师", noter_entry.get())
            if "无" in (add_name, composer) or "error" in (
                add_name,
                nickname,
                composer,
                bpm,
                time_span,
                drawer,
                chapter,
                level,
                accuracy,
                comment,
                note_cnt,
                noter,
            ):
                return
            if comment == comment_placeholder_text:
                comment = "无"

            tree = etree.parse(xmlpath)  # 解析
            xmlroot = tree.getroot()
            complex_name = f"{add_name}({composer})"
            if complex_name in self.song_list:  # 已有歌曲新差分
                print(f"{complex_name}已经在列表中,差分")
                # print('index = ', index)
                song_id = self.song_dic[complex_name]
                # add_song_lst = xmlroot.xpath(f'//song[@id="{song_id}"]')
                add_song_lst = find_by_id(xmlroot, song_id=f"{song_id}")
                if add_song_lst == []:
                    return
                add_song = add_song_lst[0]
                new_id = song_id
                if add_song.find(difficulty) is not None:
                    print(f"{difficulty}难度已经存在")
                    return
            else:
                print(f"新建歌曲{complex_name}")
                new_id = len(xmlroot)
                # 处理通用属性
                add_song = etree.Element(
                    "song", id=f"{new_id}"
                )  # 若是在下面len的话会多算已经创建的这个 导致id多+1
                etree.SubElement(add_song, "名称").text = add_name
                etree.SubElement(add_song, "俗称").text = nickname

                if nickname != "无":
                    self.nickname_list.append(nickname)
                    self.nickname_dic[nickname] = complex_name

                etree.SubElement(add_song, "曲师").text = composer
                self.song_dic[complex_name] = new_id
                self.song_list.append(complex_name)
                if composer not in self.composer_list:  # 实时更改
                    self.composer_list.append(composer)

                etree.SubElement(add_song, "章节").text = chapter
                if chapter not in self.chapter_list:
                    self.chapter_list.append(chapter)

                etree.SubElement(add_song, "bpm").text = bpm
                etree.SubElement(add_song, "时长").text = time_span
                etree.SubElement(add_song, "画师").text = drawer

            chafen = etree.SubElement(add_song, f"{difficulty}")
            etree.SubElement(chafen, "定数").text = level
            etree.SubElement(chafen, "acc").text = accuracy
            if float(accuracy) < 70:
                singal_rks = "0"
            else:
                singal_rks = str(
                    round(float(level) * pow((float(accuracy) - 55) / 45, 2), 4)
                )
            etree.SubElement(chafen, "单曲rks").text = singal_rks
            etree.SubElement(chafen, "简评").text = comment
            etree.SubElement(chafen, "物量").text = note_cnt
            etree.SubElement(chafen, "谱师").text = noter

            messagebox.showinfo("", f"{complex_name}成功加入数据库")
            # tree.write(xmlpath, encoding='utf-8', xml_declaration=True)
            root_node = xmlroot.xpath("//phigros")[0]  # 找到父节点
            root_node.insert(int(new_id), add_song)  # 追加新分支
            tree.write(
                xmlpath, encoding="utf-8", pretty_print=True, xml_declaration=True
            )  # 回写

            singal_rks = float(singal_rks)
            change = False
            if self.b27_list[-1][0] < singal_rks:  # 更新b27
                song_info = self.get_song_data("index", new_id, xmlroot)
                self.b27_list = self.b27_list[: len(self.b27_list) - 1 :]
                self.b27_list.append([singal_rks, song_info, difficulty])
                self.b27_list.sort(reverse=True, key=lambda x: x[0])  # 降序排列
                change = True

            if int(eval(accuracy)) == 100 and self.phi3_list[-1][0] < float(level):
                song_info = self.get_song_data("index", new_id, xmlroot)
                self.phi3_list = self.phi3_list[: len(self.phi3_list) - 1 :]
                self.phi3_list.append((float(level), song_info, difficulty))
                self.phi3_list.sort(reverse=True, key=lambda x: x[0])  # 降序排列
                change = True

            if change:
                self.generate_rks_conpound(self.contain_item["查"]["滚动页面"])

        confirm_button = ctk.CTkButton(
            add_content_frame,
            text="写入数据库",
            command=add_confirm,
            font=(ctext_font, ctext_size),
        )
        confirm_button.grid(row=rowi + 1, column=0, pady=10, padx=10)
        self.contain_item["增"]["确认"] = confirm_button
        rowi += 1
        add_content_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.view_page("增")  # 设为不可见
        self.nav_buttons["增"].grid()

    """删"""

    def init_delete_window(self):
        delete_content_frame = ctk.CTkFrame(self.content_frame)
        delete_content_frame.configure(fg_color="transparent")
        self.grid_item["删"]["窗口"] = delete_content_frame
        rowi = 0

        select_song = combobox_frame(
            delete_content_frame, "选择要删除的歌曲", "删除歌曲", self.song_list
        )

        def filter_values(event):
            input_text = select_song.get().strip().lower()
            if not input_text:
                select_song.option_menu.configure(values=self.song_list)
                return
            filtered = [
                item
                for item in (self.song_list + self.nickname_list)
                if input_text in item.lower()
            ]
            select_song.option_menu.configure(values=filtered)

        select_song.option_menu.bind("<KeyRelease>", filter_values)
        select_song.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["删"]["歌曲"] = select_song
        rowi += 1

        difficulty_choose = optionmenu_frame(
            delete_content_frame,
            "选择难度(留空则删掉整首歌)",
            "删除难度",
            [""] + DIFFICULTY_LIST,
            "",
        )
        difficulty_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["删"]["难度"] = difficulty_choose
        rowi += 1

        def delete_confirm():
            complex_name = valid_test(
                "名称", select_song.get(), self.nickname_dic
            )  # 玩家可能选择后又进行了输入
            if (complex_name == "无") or (complex_name not in self.song_list):
                messagebox.showwarning(
                    "名称错误", f"无法找到曲名为{complex_name}的歌曲"
                )
                return
            song_id = self.song_dic[complex_name]
            tree = etree.parse(xmlpath)
            xmlroot = tree.getroot()
            # song_lst = xmlroot.xpath(f'//song[@id="{song_id}"]')
            song_lst = find_by_id(xmlroot, song_id=f"{song_id}")
            if song_lst == []:
                return
            song = song_lst[0]
            diff = difficulty_choose.get()
            if diff == "":  # 没有指定难度 直接删掉整首歌
                print(f"删除歌曲{complex_name}")
                diff_exise = False
                singal_rks = 0
                for diffi in DIFFICULTY_LIST:
                    diff_elm = song.find(diffi)
                    if diff_elm is not None:
                        diff_exise = True
                        singal_rks = max(
                            singal_rks, float(diff_elm.find("单曲rks").text)
                        )
                        # print(diff_exise)
                if not diff_exise:  # 无难度存在 只剩个基本信息力…
                    diff_elm = None
                xmlroot.xpath("//phigros")[0].remove(song)

                for index in range(song_id, len(xmlroot)):  # 更新索引
                    song_elmi = xmlroot[index]
                    song_elmi.attrib["id"] = f"{index}"
                    self.song_dic[
                        f"{song_elmi.find('名称').text}({song_elmi.find('曲师').text})"
                    ] = index
                self.song_list.remove(complex_name)
                del self.song_dic[complex_name]
                nickname = song.find("俗称").text
                if nickname != "无":
                    self.nickname_list.remove(nickname)
                    del self.nickname_dic[nickname]
                self.contain_item["删"]["歌曲"].option_menu.configure(
                    variable=ctk.StringVar(value=""), values=[]
                )
            else:
                diff_elm = song.find(diff)  # 指定删除的难度
                singal_rks = float(diff_elm.find("单曲rks").text)
                if diff_elm is None:
                    messagebox.showwarning(
                        "难度不存在", f"{complex_name} 没有{diff}难度"
                    )
                    return
                else:
                    diff_exise = True
                    messagebox.showinfo("删除难度", f"删除难度{diff}")
                    song.remove(diff_elm)

            # print(diff_elm.find('acc').text)
            tree.write(
                xmlpath, encoding="utf-8", pretty_print=True, xml_declaration=True
            )

            # print(singal_rks, self.b27_list[-1][0])
            if not diff_exise:
                return  # 都无难度存在了不可能需要更新rks了
            if singal_rks >= self.b27_list[-1][0] or (
                diff_elm is not None
                and int(eval(diff_elm.find("acc").text)) == 100
                and singal_rks >= self.phi3_list[-1][0]
            ):
                # print('进入')
                self.get_rks_compose(xmlroot)
                self.generate_rks_conpound(self.contain_item["查"]["滚动页面"])

        confirm_button = ctk.CTkButton(
            delete_content_frame,
            text="删除选中歌曲的所选属性",
            command=delete_confirm,
            font=(ctext_font, ctext_size),
        )
        confirm_button.grid(row=rowi, column=0, pady=10, padx=10)
        self.contain_item["删"]["确认"] = confirm_button
        rowi += 1

        image_frame = ctk.CTkFrame(delete_content_frame)
        image_frame.configure(fg_color="transparent")
        image_frame.grid(row=rowi, column=0, sticky="nsew", padx=50, pady=0)
        self.grid_item["删"]["曲绘窗口"] = image_frame
        rowi += 1

        delete_content_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.view_page("删")  # 设为不可见
        self.nav_buttons["删"].grid()

    """改"""

    def init_change_window(self):
        change_content_frame = ctk.CTkFrame(self.content_frame)
        change_content_frame.configure(fg_color="transparent")
        self.grid_item["改"]["窗口"] = change_content_frame
        rowi = 0

        select_song_choose = combobox_frame(
            change_content_frame, "选择更改的歌曲:", "更改歌曲", self.song_list
        )
        select_song_choose.set_size(width=500)
        select_song_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["改"]["歌曲"] = select_song_choose
        rowi += 1

        def filter_values(event):
            input_text = select_song_choose.get().strip().lower()
            if not input_text:
                select_song_choose.option_menu.configure(values=self.song_list)
                return
            filtered = [
                item
                for item in (self.song_list + self.nickname_list)
                if input_text in item.lower()
            ]
            select_song_choose.option_menu.configure(values=filtered)

        select_song_choose.option_menu.bind("<KeyRelease>", filter_values)

        change_difficulty_choose = optionmenu_frame(
            change_content_frame,
            "选择更改的难度:",
            "更改难度",
            DIFFICULTY_LIST,
            DIFFICULTY_LIST[0],
        )
        change_difficulty_choose.grid(
            row=rowi, column=0, pady=10, padx=10, sticky="nsew"
        )
        self.contain_item["改"]["难度"] = change_difficulty_choose
        rowi += 1

        self.tip_attri = "acc"
        attribution_choose = optionmenu_frame(
            change_content_frame,
            "选择更改的属性:",
            "更改属性",
            (
                "名称",
                "俗称",
                "曲师",
                "章节",
                "bpm",
                "时长",
                "画师",
                "定数",
                "acc",
                "简评",
                "物量",
                "谱师",
            ),
            self.tip_attri,
        )
        attribution_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["改"]["属性"] = attribution_choose
        rowi += 1

        attribution_entry = muti_entry_frame(change_content_frame, "输入更改值:")
        attribution_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["改"]["值"] = attribution_entry
        rowi += 1

        tips = ctk.CTkLabel(
            change_content_frame,
            text="",
            font=(ctext_font, ctext_size),
            fg_color="transparent",
        )
        tips.grid(row=rowi, column=0, pady=5, padx=10)
        self.contain_item["改"]["提示"] = tips
        rowi += 1

        def change_confirm():
            song_name = valid_test("名称", select_song_choose.get(), self.nickname_dic)
            if (song_name == "无") or (song_name not in self.song_list):
                messagebox.showerror("无效名称", f"{song_name}不存在")
                return

            tree = etree.parse(xmlpath)
            xmlroot = tree.getroot()
            # song = xmlroot.xpath(f'//song[@id="{self.song_dic[song_name]}"]')
            song = find_by_id(xmlroot, song_id=f"{self.song_dic[song_name]}")
            if song == []:
                return
            song = song[0]
            difficulty = change_difficulty_choose.get()
            diff_elm = song.find(difficulty)
            singal_rks = diff_elm.find("单曲rks").text
            attribution_type = attribution_choose.get()
            if attribution_type in DIFF_ATTRI and diff_elm is None:
                messagebox.showwarning("", f"{song_name}没有难度{difficulty}")
                return

            attribution_value = attribution_entry.get()
            attribution_value = valid_test(
                attribution_type, attribution_value, self.nickname_dic
            )
            if attribution_value in ("无", "error"):
                return
            if attribution_type in DIFF_ATTRI:  # 更改难度相关属性
                reconfirm = False
                if attribution_type == "acc" and float(
                    diff_elm.find(attribution_type).text
                ) >= float(
                    attribution_value
                ):  # 更改后的acc<=改前的 二次确认
                    reconfirm = messagebox.askyesno("二次确认", "确认更改为更低的acc?")
                    if not reconfirm:
                        return
                messagebox.showinfo(
                    "更改",
                    f"{song_name}({difficulty}){attribution_type}:{diff_elm.find(attribution_type).text}->{attribution_value}",
                )
                diff_elm.find(attribution_type).text = attribution_value
            else:  # 更改通用属性
                if attribution_type in ("名称", "曲师"):  # 维护相应列表
                    bracket_idx = song_name.rindex("(")
                    name = (
                        song_name[:bracket_idx:]
                        if attribution_type == "曲师"
                        else attribution_value
                    )
                    composer = (
                        song_name[bracket_idx + 1 : -1 :]
                        if attribution_type == "名称"
                        else attribution_value
                    )
                    complex_name = f"{name}({composer})"
                    select_song_choose.option_menu.configure(
                        variable=ctk.StringVar(value=complex_name)
                    )  # 在更改名称或曲师后 自动将歌曲选择框的内容更改掉 以便继续更改其他属性

                    self.song_list.remove(song_name)
                    self.song_dic[complex_name] = self.song_dic[song_name]
                    del self.song_dic[song_name]
                    self.tip_song = complex_name
                    self.song_list.append(complex_name)
                    select_song_choose.option_menu.configure(values=[complex_name])

                elif attribution_type == "俗称":
                    nickname = song.find(attribution_type).text
                    if nickname != "无":
                        self.nickname_list.remove(nickname)
                        del self.nickname_dic[nickname]
                    if attribution_value != "无":
                        self.nickname_list.append(attribution_value)
                        self.nickname_dic[attribution_value] = song_name

                messagebox.showinfo(
                    "更改",
                    f"{song_name}({difficulty}){attribution_type}:{song.find(attribution_type).text}->{attribution_value}",
                )
                song.find(attribution_type).text = attribution_value

            if attribution_type in ["acc", "定数"]:
                if float(diff_elm.find("acc").text) >= 70:
                    singal_rks = str(
                        round(
                            float(diff_elm.find("定数").text)
                            * pow((float(diff_elm.find("acc").text) - 55) / 45, 2),
                            4,
                        )
                    )
                else:
                    singal_rks = "0"
                diff_elm.find("单曲rks").text = singal_rks

            tree.write(
                xmlpath, encoding="utf-8", pretty_print=True, xml_declaration=True
            )
            self.change_current_info()

            if attribution_type in ["acc", "定数"]:
                self.get_rks_compose(xmlroot)
                self.generate_rks_conpound(self.contain_item["查"]["滚动页面"])

        confirm_button = ctk.CTkButton(
            change_content_frame,
            text="更改选中歌曲信息",
            command=change_confirm,
            font=(ctext_font, ctext_size),
        )
        confirm_button.grid(row=rowi, column=0, pady=5, padx=10)
        self.contain_item["改"]["确认"] = confirm_button
        rowi += 1

        image_frame = ctk.CTkFrame(change_content_frame)
        image_frame.configure(fg_color="transparent")
        image_frame.grid(row=rowi, column=0, sticky="nsew", padx=50, pady=0)
        self.grid_item["改"]["曲绘窗口"] = image_frame
        rowi += 1

        change_content_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.view_page("改")
        self.nav_buttons["改"].grid()

    def change_current_info(self):
        tree = etree.parse(xmlpath)
        xmlroot = tree.getroot()
        show_text = ""
        if not (self.tip_attri and self.tip_diff and self.tip_song):
            return
        # print(self.tip_attri)
        song_id = self.song_dic[self.tip_song]
        # songi = xmlroot.xpath(f'//song[@id="{song_id}"]')
        songi = find_by_id(xmlroot, song_id=f"{song_id}")
        if songi == []:
            return
        songi = songi[0]
        self.contain_item["改"]["值"].ctktext.delete("0.0", "end")
        if self.tip_attri in ["定数", "acc", "简评", "物量", "谱师"]:  # 后面要+rks的
            diff = songi.find(self.tip_diff)
            singal_rks = diff.find("单曲rks").text  # .find('')
            show_text = diff.find(self.tip_attri).text
            self.contain_item["改"]["值"].ctktext.insert(
                "0.0", show_text if show_text else "无"
            )
            show_text += f"\n单曲rks:{singal_rks}"
        else:
            show_text = songi.find(self.tip_attri).text
            self.contain_item["改"]["值"].ctktext.insert(
                "0.0", show_text if show_text else "无"
            )
        show_text_form = ""
        for i in range(0, len(show_text), 40):  # 40个字符分一行
            show_text_form += show_text[i : i + 40 :]
        self.contain_item["改"]["提示"].configure(
            text=f"{self.tip_attri}:{show_text_form}\nb27地板:{self.b27_list[-1][0]}\nphi3地板:{self.phi3_list[-1][0]}"
        )
        self.update()

    """查"""

    def get_rks_compose(self, xmlroot):
        index_counter = 0
        self.b27_list = []
        self.phi3_list = []
        for index in range(len(xmlroot)):
            song_info = self.get_song_data("index", index, xmlroot)
            if song_info is None:
                continue
            # print(song_info)
            for diffi in DIFFICULTY_LIST:
                if diffi in song_info.keys():
                    acc = float(song_info[diffi]["acc"])
                    singal_rks = float(song_info[diffi]["单曲rks"])
                    index_counter += 1
                    item = [singal_rks, index_counter, song_info, diffi]

                    if len(self.b27_list) < 27:
                        heapq.heappush(self.b27_list, item)
                    else:
                        heapq.heappushpop(self.b27_list, item)

                    if int(acc) == 100:
                        # print(name)
                        if len(self.phi3_list) < 3:
                            heapq.heappush(self.phi3_list, item)
                        else:
                            heapq.heappushpop(self.phi3_list, item)

        self.b27_list = [[item[0], item[2], item[3]] for item in self.b27_list]
        self.b27_list.sort(reverse=True, key=lambda x: x[0])  # 降序排列

        self.phi3_list = [[item[0], item[2], item[3]] for item in self.phi3_list]
        self.phi3_list.sort(reverse=True, key=lambda x: x[0])  # 降序排列

    def generate_rks_conpound(self, scroll_frame):  # 布局rks组成结果
        print("rks组成正在生成中...")
        start_time = time.time()
        self.rks = 0
        rowi = 1
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        b27_frame = expand_frame(scroll_frame, "b27组成:", True)
        b27_frame.set_color("#FFFFF0")
        b27_frame.grid(row=rowi, column=0, pady=5, padx=2, sticky="nsew")
        self.contain_item["查"]["b27文件夹"] = b27_frame
        rowi += 1
        for i in range(min(len(self.b27_list), 27)):
            self.rks += self.b27_list[i][0]
            song_info = self.b27_list[i][1]  # (singal_rks, song_info, diffi)
            diffi = self.b27_list[i][2]

            b27_song_label = expand_frame(
                b27_frame.content_frame,
                f"{i + 1}.{song_info['名称'][:min(len(song_info['名称']), 20):]}: {self.b27_list[i][0]}",
                text_color=DIFFICULTY_COLOR[diffi],
            )
            b27_song_label.set_color("#FFFFF0")
            b27_song_label.grid(row=i, column=0, pady=5, padx=10, sticky="w")

            show_name = (
                song_info["俗称"]
                if song_info["俗称"] and song_info["俗称"] != "无"
                else song_info["名称"]
            )
            b27_hid_info = [
                f"名称:{show_name}",
                f"难度:{diffi}",
                f"rks:{self.b27_list[i][0]}",
                f"acc:{song_info[diffi]['acc']}",
                f"定数:{song_info[diffi]['定数']}",
            ]
            try:
                song_image = ctk.CTkImage(
                    light_image=Image.open(
                        image_path_prefix
                        + f"{valid_test('文件路径', f'{song_info['名称']}({song_info['曲师']})')}.png"
                    ),
                    size=(454, 240),
                )
                b27_hid_img_label = ctk.CTkLabel(
                    b27_song_label.content_frame, text="", image=song_image
                )
                b27_hid_img_label.grid(row=0, column=0, pady=5, padx=10, sticky="w")
            except:
                print(f"名称:{show_name}({diffi})图像生成错误")

            for rowj in range(1, len(b27_hid_info) + 1):  # 展示属性个数
                b27_hid_info_label = ctk.CTkLabel(
                    b27_song_label.content_frame,
                    text=b27_hid_info[rowj - 1],
                    font=(ctext_font, 30),
                    fg_color="#F0FFFF",
                    width=400,
                    anchor="w",
                )
                b27_hid_info_label.grid(row=rowj, column=0, pady=5, padx=10, sticky="w")

        phi3_frame = expand_frame(scroll_frame, "phi3组成:", True)
        phi3_frame.set_color("#FFFFF0")
        phi3_frame.grid(row=rowi, column=0, pady=5, padx=2, sticky="nsew")
        self.contain_item["查"]["phi3文件夹"] = phi3_frame
        rowi += 1

        for i in range(min(len(self.phi3_list), 3)):
            self.rks += self.phi3_list[i][0]
            song_info = self.phi3_list[i][1]  # (singal_rks, song_info, diffi)
            diffi = self.phi3_list[i][2]
            phi3_song_label = expand_frame(
                phi3_frame.content_frame,
                f"{i + 1}.{song_info['名称'][:min(len(song_info['名称']), 20):]}: {self.phi3_list[i][0]}",
                text_color=DIFFICULTY_COLOR[diffi],
            )
            phi3_song_label.set_color("#FFFFF0")
            phi3_song_label.grid(row=i, column=0, pady=5, padx=10, sticky="w")

            show_name = (
                song_info["俗称"]
                if song_info["俗称"] and song_info["俗称"] != "无"
                else song_info["名称"]
            )
            phi3_hid_info = [
                f"名称:{show_name}",
                f"难度:{diffi}",
                f"rks:{self.phi3_list[i][0]}",
                f"acc:{song_info[diffi]['acc']}",
                f"定数:{song_info[diffi]['定数']}",
            ]
            try:
                song_image = ctk.CTkImage(
                    light_image=Image.open(
                        image_path_prefix
                        + f"{valid_test('文件路径', f'{song_info['名称']}({song_info['曲师']})')}.png"
                    ),
                    size=(454, 240),
                )
                phi3_hid_info_label = ctk.CTkLabel(
                    phi3_song_label.content_frame, text="", image=song_image
                )
                phi3_hid_info_label.grid(row=0, column=0, pady=5, padx=10, sticky="w")
            except:
                print(f"名称:{show_name}({diffi})图像生成错误")
            for rowj in range(1, len(phi3_hid_info) + 1):  # 展示属性个数
                phi3_hid_info_label = ctk.CTkLabel(
                    phi3_song_label.content_frame,
                    text=phi3_hid_info[rowj - 1],
                    font=(ctext_font, 30),
                    fg_color="#F0FFFF",
                    width=400,
                    anchor="w",
                )
                phi3_hid_info_label.grid(
                    row=rowj, column=0, pady=5, padx=10, sticky="w"
                )

        rks_label = ctk.CTkLabel(
            scroll_frame,
            text=f"rks={round(self.rks/30, 4)}",
            font=(ctext_font, 35),
            fg_color="#F0FFFF",
            width=400,
            anchor="center",
        )
        rks_label.grid(row=0, column=0, pady=5, padx=5, sticky="w")
        self.contain_item["查"]["rks文字"] = rks_label

        print(f"rks组成生成完毕,用时{round(time.time() - start_time, 2)}s")

    def change_find_window(self, attri):  # 重置/切换页面
        if attri not in ["名称", "曲师", "章节", "单曲rks", "定数", "acc", "简评"]:
            messagebox.showerror("", "你这换页查找的属性输入不对啊")
            return
        for page_namei in ("名称", "曲师", "章节", "单曲rks", "定数", "acc", "简评"):
            if attri != page_namei:
                # print(f'移除{page_namei}')
                self.grid_item["查"][page_namei].grid_remove()
        self.grid_item["查"][attri].grid()
        # print(f'布局{attri}')
        self.find_now_page = attri
        self.switch_find_page("重置")
        for content_pagei in self.page_administrator:  # 把滚动框内容全清除
            content_pagei.destroy()
        self.page_administrator = []

    def init_find_attri_setting_window(self):  # 初始化查找结果设置页面
        find_attri_setting = ctktoplevel_frame(
            self.sidebar_frame, "查找结果可见属性设置"
        )
        find_attri_setting.set_size(300, 700, 100, 100)
        find_attri_setting.grid_columnconfigure(0, weight=1)
        find_attri_setting.grid_rowconfigure(0, weight=1)

        def ban_exit_window(event=None):
            # print('用户尝试关闭')
            find_attri_setting.withdraw()  # 隐藏

        find_attri_setting.bind("<Escape>", ban_exit_window)
        find_attri_setting.protocol("WM_DELETE_WINDOW", ban_exit_window)
        find_attri_setting.withdraw()  # 直接关闭页面的话要重载上次的操作 隐藏起来可以自动记录
        self.contain_item["查"]["设置窗口"] = find_attri_setting

        scroll_frame = ctk.CTkScrollableFrame(find_attri_setting, width=300, height=700)
        scroll_frame.configure(fg_color="transparent")
        self.contain_item["查"]["设置-滚动窗口"] = scroll_frame
        scroll_frame.grid(row=0, column=0, pady=0, padx=0, sticky="nsew")

        commen_folder = expand_frame(scroll_frame, "通用属性:", True)
        commen_folder.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")

        rowi = 0
        self.attri_var_dic = {}
        for attri in COMMEN_ATTRI + ["曲绘"]:
            if attri == "俗称":
                continue
            attri_var = ctk.BooleanVar(
                value=True if attri in ("名称", "曲师", "曲绘") else False
            )
            self.attri_var_dic[attri] = attri_var
            attri_checkbox = ctk.CTkCheckBox(
                master=commen_folder.content_frame,
                text=attri,
                variable=attri_var,
                font=(ctitle_font, ctitle_size),
            )
            attri_checkbox.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
            rowi += 1

        diff_folder = expand_frame(scroll_frame, "难度差分属性:", True)
        diff_folder.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")
        rowi = 0
        for attri in DIFF_ATTRI:
            attri_var = ctk.BooleanVar(
                value=True if attri in ("定数", "acc", "单曲rks", "简评") else False
            )
            self.attri_var_dic[attri] = attri_var
            attri_checkbox = ctk.CTkCheckBox(
                master=diff_folder.content_frame,
                text=attri,
                variable=attri_var,
                font=(ctitle_font, ctitle_size),
            )
            attri_checkbox.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
            rowi += 1

        def confirm():
            self.ban_hid_attri = ["俗称"]  # 覆盖上次的选择
            for attri, vari in self.attri_var_dic.items():
                if vari.get() is False:  # 不布局此属性
                    self.ban_hid_attri.append(attri)
            print("可见性更改成功")
            # print(self.ban_hid_attri)

        button = ctk.CTkButton(
            scroll_frame,
            text="更改可见性",
            command=confirm,
            font=(ctext_font, ctext_size),
        )
        button.grid(row=2, column=0, pady=10, padx=10)

    def init_find_window(self):  # 通用控件布局 确认后搜索
        global find_info_page, seek_type_choose
        tab_window = ctk.CTkTabview(
            self.content_frame,
            width=500,
            height=550,
            corner_radius=10,
            fg_color="lightblue",
        )
        self.grid_item["查"]["总框"] = tab_window

        def change_setting_viewable():
            self.contain_item["查"]["设置窗口"].deiconify()

        find_attri_setting_button = ctk.CTkButton(
            self.sidebar_frame,
            text="更改可见性",
            command=change_setting_viewable,
            font=(ctext_font, ctext_size),
        )
        find_attri_setting_tooltip = CTkToolTip(
            find_attri_setting_button,
            message="更改展示在查找结果中的属性",
            bg_color="gray90",
            font=(ctext_font, ctext_size),
            x_offset=30,
            y_offset=20,
        )
        self.contain_item["查"]["设置按钮提示"] = find_attri_setting_tooltip
        self.contain_item["查"]["设置按钮"] = find_attri_setting_button
        find_attri_setting_button.place(
            relx=0.30, rely=0.95, anchor="s", relwidth=0.7  # 相对宽度
        )
        find_attri_setting_button.place_forget()

        find_rks_page = tab_window.add("rks组成")
        find_info_page = tab_window.add("歌曲信息查找")

        """处理rks组成"""
        tree = etree.parse(xmlpath)
        xmlroot = tree.getroot()
        self.get_rks_compose(xmlroot)
        # print(f'phi3={self.phi3_list}')

        scroll_frame = ctk.CTkScrollableFrame(find_rks_page, width=540, height=540)
        scroll_frame.configure(fg_color="transparent")
        self.contain_item["查"]["滚动页面"] = scroll_frame
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.generate_rks_conpound(self.contain_item["查"]["滚动页面"])

        """按照属性查找"""
        self.find_now_page = "名称"  # find_now_page==查找页面当前的窗口
        seek_type_choose = optionmenu_frame(
            find_info_page,
            "选择查找属性",
            "查找属性",
            ["名称", "曲师", "章节", "单曲rks", "定数", "acc", "简评"],
            self.find_now_page,
        )
        seek_type_choose.configure(fg_color="transparent")
        seek_type_choose.grid(row=0, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["属性"] = seek_type_choose

        self.init_find_composor_page()
        self.init_find_chapter_page()
        self.init_find_name_page()
        self.init_find_comment_page()
        self.init_find_acc_page()
        self.init_find_rks_page()
        self.init_find_level_page()
        self.init_find_attri_setting_window()

        self.now_find_page = 0  # now_find_page==当前查找的页数
        self.find_rst_list = []
        self.total_find_page = 0
        self.show_num_perpage = 20
        self.find_rst_page = ""
        self.page_administrator = (
            []
        )  # 不预先定义 初始化切换查找页面无法通过 存储每页的底层窗口

        def confirm():
            input_num = valid_test(
                "每页条数", self.contain_item["查"]["展示数"].get(), True
            )
            if input_num == "error":
                # print('return')
                self.contain_item["查"]["展示数"].option_menu.configure(
                    variable=ctk.IntVar(value=20)
                )
                return
            self.show_num_perpage = input_num
            # print(self.show_num_perpage)
            self.find_rst_list = []
            page = seek_type_choose.get()
            self.change_find_window(page)  # 确认后切换页面 防止上一次布局残留
            if page in ["名称", "曲师", "章节", "简评"]:  # 内容选择框+难度框
                find_goal = valid_test(
                    page,
                    self.contain_item["查"][f"{page}-名称"].get(),
                    self.nickname_dic,
                )
                if find_goal in ["无", "error"]:
                    messagebox.showerror("", f"你这{page}输入有问题啊")
                    return
                # print(f'查找目标{find_goal}')
                if page != "简评":
                    difficulty = self.contain_item["查"][f"{page}-难度"].get()

                tree = etree.parse(xmlpath)
                xmlroot = tree.getroot()
                for song_idx in range(len(xmlroot)):
                    song_elm = xmlroot[song_idx]
                    if page == "名称":
                        if find_goal in self.song_list:  # 准确搜索
                            song_info = self.get_song_data(
                                "complex_name", find_goal, xmlroot
                            )
                            if not song_info:
                                continue
                            if difficulty != "All":
                                if difficulty in song_info.keys():
                                    self.find_rst_list.append((song_info, difficulty))
                                    break
                            else:
                                for diffi in DIFFICULTY_LIST:
                                    if diffi in song_info.keys():
                                        self.find_rst_list.append((song_info, diffi))
                                break

                        elif (
                            find_goal.lower() in f"{song_elm.find('名称').text}".lower()
                        ):  # 模糊搜索
                            song_info = self.get_song_data("index", song_idx, xmlroot)
                            if not song_info:
                                continue
                            if difficulty != "All":
                                if difficulty in song_info.keys():
                                    self.find_rst_list.append((song_info, difficulty))
                            else:
                                for diffi in DIFFICULTY_LIST:
                                    if diffi in song_info.keys():
                                        self.find_rst_list.append((song_info, diffi))

                    elif (
                        page == "曲师"
                        and find_goal.lower() in song_elm.find("曲师").text.lower()
                    ):
                        song_info = self.get_song_data("index", song_idx, xmlroot)
                        if not song_info:
                            continue
                        if difficulty != "All":
                            if difficulty in song_info.keys():
                                self.find_rst_list.append((song_info, difficulty))
                        else:
                            for diffi in DIFFICULTY_LIST:
                                if diffi in song_info.keys():
                                    self.find_rst_list.append((song_info, diffi))

                    elif (
                        page == "章节"
                        and find_goal.lower() in song_elm.find("章节").text.lower()
                    ):
                        song_info = self.get_song_data("index", song_idx, xmlroot)
                        if not song_info:
                            continue
                        if difficulty != "All":
                            if difficulty in song_info.keys():
                                self.find_rst_list.append((song_info, difficulty))
                        else:
                            for diffi in DIFFICULTY_LIST:
                                if diffi in song_info.keys():
                                    self.find_rst_list.append((song_info, diffi))

                    elif page == "简评":
                        song_info = self.get_song_data("index", song_idx, xmlroot)
                        for diffi in DIFFICULTY_LIST:
                            if diffi in song_info.keys():
                                commenti = song_info[diffi]["简评"].lower()
                                if commenti == "无":
                                    continue
                                if find_goal.lower() in commenti:
                                    self.find_rst_list.append((song_info, diffi))

            elif page in ["单曲rks", "定数", "acc"]:  # 范围输入框
                min_num = self.contain_item["查"][f"{page}-最小值"].get()
                if min_num == "":
                    min_num = "0"
                else:
                    min_num = valid_test(page, min_num)

                max_num = self.contain_item["查"][f"{page}-最大值"].get()
                if max_num == "":
                    if page == "acc":
                        max_num = "100"
                    elif page in ("单曲rks", "定数"):
                        max_num = MAX_LEVEL
                else:
                    max_num = valid_test(page, max_num)
                if "error" in (min_num, max_num):
                    return

                # print(f'min={min_num}max={max_num}')
                tree = etree.parse(xmlpath)
                xmlroot = tree.getroot()
                for song_idx in range(len(xmlroot)):
                    song_info = self.get_song_data("index", song_idx, xmlroot)
                    for diffi in DIFFICULTY_LIST:
                        if diffi in song_info.keys():
                            if song_info[diffi][page] != "无":
                                song_num = float(song_info[diffi][page])
                                if float(min_num) <= song_num <= float(max_num):
                                    self.find_rst_list.append((song_info, diffi))

                self.find_rst_list = sorted(
                    self.find_rst_list,
                    key=lambda x: float(x[0][x[1]][page]),
                    reverse=True,
                )

            self.find_rst_page = page
            if len(self.find_rst_list):
                # print(self.find_rst_list)
                self.grid_find_rst()
            else:
                messagebox.showinfo("", "无符合条件的数据")

        button = ctk.CTkButton(
            find_info_page,
            text="查找选中歌曲",
            command=confirm,
            font=(ctext_font, ctext_size),
        )
        button.grid(row=2, column=0, pady=10, padx=10)

        num_perpage_choose = combobox_frame(
            find_info_page, "每页展示结果数量:", "展示数量", ["10", "20", "30"], "20"
        )
        num_perpage_choose.grid(row=3, column=0, pady=0, padx=0, sticky="nsew")
        self.contain_item["查"]["展示数"] = num_perpage_choose

        last_page_button = ctk.CTkButton(
            find_info_page,
            text="上一页",
            command=lambda x=None: self.switch_find_page("上一页"),
            state="disabled" if (self.now_find_page < 1) else "normal",
            font=(ctext_font, ctext_size),
        )
        last_page_button.place(relx=0.25, rely=1.0, anchor="se", relwidth=0.25)
        self.contain_item["查"]["上一页"] = last_page_button
        tooltip = CTkToolTip(
            last_page_button,
            message=(
                "没有上一页了哦"
                if (self.now_find_page < 1)
                else f"前往{self.now_find_page - 1}页"
            ),
            bg_color="gray90",
            font=(ctext_font, ctext_size),
            x_offset=30,
            y_offset=20,
        )
        self.contain_item["查"]["上一页提示"] = tooltip

        page_label = ctk.CTkLabel(
            find_info_page, text="当前页数:1/?", fg_color="#F0FFFF", corner_radius=6
        )
        self.contain_item["查"]["当前页/总页"] = page_label
        page_label.place(relx=0.5, rely=1.0, anchor="s")

        next_page_button = ctk.CTkButton(
            find_info_page,
            text="下一页",
            command=lambda x=None: self.switch_find_page("下一页"),
            state="disabled",
            font=(ctext_font, ctext_size),
        )
        next_page_button.place(relx=0.75, rely=1.0, anchor="sw", relwidth=0.25)
        self.contain_item["查"]["下一页"] = next_page_button
        tooltip = CTkToolTip(
            next_page_button,
            message="正在布局中...",
            font=(ctext_font, ctext_size),
            x_offset=30,
            y_offset=20,
        )
        self.contain_item["查"]["下一页提示"] = tooltip

        tab_window.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.view_page("查")
        self.nav_buttons["查"].grid()
        self.change_hide_statue_btn.grid()

    def grid_find_rst(self):  # 布局搜索结果
        find_start_time = time.time()

        # 在滚动框架下布局 folder
        self.total_find_page = (
            len(self.find_rst_list) + self.show_num_perpage - 1
        ) // self.show_num_perpage
        if self.total_find_page == 0:
            return
        print(f"共找到 {self.total_find_page}页数据")
        self.contain_item["查"]["下一页提示"].configure(
            message=(
                f"前往{self.now_find_page + 2}页"
                if (self.now_find_page < self.total_find_page - 1)
                else "没有下一页了哦"
            )
        )
        try:
            self.contain_item["查"]["属性-内容滚动框"].destroy()
        except:
            pass
        scroll_frame = ctk.CTkScrollableFrame(find_info_page, width=460, height=320)
        scroll_frame.configure(fg_color="transparent")
        scroll_frame.place(
            relx=0.01,  # X起始位置占窗口宽度的1%
            rely=0.40,  # Y起始位置占窗口高度的40%
            relwidth=0.95,  # 控件宽度随窗口宽度变化（始终维持95%）
            relheight=0.45,  # 控件高度随窗口高度变化（始终维持45%）
            anchor="nw",  # 锚点控制延展方向（nw=左上角开始扩展）
        )
        self.contain_item["查"]["属性-内容滚动框"] = scroll_frame
        self.page_administrator = []

        for i in range(self.total_find_page):
            page_content_frame = ctk.CTkFrame(scroll_frame)
            page_content_frame.configure(fg_color="transparent")
            self.page_administrator.append(page_content_frame)
            self.page_administrator[i].grid(
                row=0, column=0, padx=0, pady=0, sticky="nsew"
            )
            self.page_administrator[i].grid_remove()
        self.page_administrator[0].grid()
        for index, songi in enumerate(self.find_rst_list):  # 遍历布局歌曲
            master = self.page_administrator[index // self.show_num_perpage]
            # print(songi)
            song_info = songi[0]
            difficulty = songi[1]
            if self.find_rst_page in ("曲师", "章节"):
                title_info = song_info[
                    self.find_rst_page
                ]  # 跟在folder顶端布局的提示内容
            elif self.find_rst_page in ("单曲rks", "定数", "acc", "简评"):
                title_info = song_info[difficulty][self.find_rst_page]
            elif self.find_rst_page == "名称":
                title_info = song_info[difficulty]["单曲rks"]
            songi_frame = expand_frame(
                master,
                f"{index + 1}.{song_info['名称']}:{title_info[:min(len(title_info), 20):]}",
                text_color=DIFFICULTY_COLOR[difficulty],
            )
            songi_frame.grid(
                row=index % self.show_num_perpage, column=0, padx=10, pady=5, sticky="w"
            )
            # 布局歌曲隐藏属性
            # print(song_info)
            rowi = 0
            if "曲绘" not in self.ban_hid_attri:
                try:
                    song_image = ctk.CTkImage(
                        light_image=Image.open(
                            image_path_prefix
                            + f"{valid_test('文件路径', f'{song_info['名称']}({song_info['曲师']})')}.png"
                        ),
                        size=(454, 240),
                    )
                    image_label = ctk.CTkLabel(
                        songi_frame.content_frame, text="", image=song_image
                    )
                    image_label.grid(row=rowi, column=0, pady=5, padx=10, sticky="w")
                    rowi += 1
                except:
                    print(f"{index + 1}.{song_info['名称']}未找到图片")

            for titlei, attri in list(song_info.items()):
                if titlei in DIFFICULTY_LIST and titlei != songi[1]:  # 仅布局指定难度
                    continue
                if titlei in self.ban_hid_attri:
                    # print('禁止布局')
                    continue
                if type(attri) is not type({1: 1}):
                    # print(f'{titlei}:{attri}')
                    info_label = ctk.CTkLabel(
                        songi_frame.content_frame,
                        text=f"{titlei}:{attri}",
                        fg_color="#F0FFFF",
                        corner_radius=6,
                        width=300,
                        anchor="w",
                    )
                    info_label.grid(row=rowi, column=0, padx=10, pady=5, sticky="w")
                    rowi += 1
                else:
                    for dic_titlei, dic_attri in song_info[difficulty].items():
                        if dic_titlei in self.ban_hid_attri:  # 禁止分级属性
                            continue
                        # print(f'{dic_titlei}:{dic_attri}')
                        info_label = ctk.CTkLabel(
                            songi_frame.content_frame,
                            text=f"{dic_titlei}:{dic_attri}",
                            fg_color="#F0FFFF",
                            corner_radius=6,
                            width=300,
                            anchor="w",
                        )
                        info_label.grid(row=rowi, column=0, padx=10, pady=5, sticky="w")
                        rowi += 1

            self.update()
            self.contain_item["查"]["下一页"].configure(
                state=(
                    "normal"
                    if (self.now_find_page < self.total_find_page - 1)
                    else "disabled"
                )
            )

        # self.contain_item['查']['下一页'].configure(state="normal" if (self.now_find_page < self.total_find_page-1) else 'disabled')
        self.contain_item["查"]["当前页/总页"].configure(
            text=f"当前页数:{self.now_find_page + 1}/{self.total_find_page}"
        )
        print(
            f"搜索完毕 共找到{len(self.find_rst_list)}个项目 用时{round(time.time() - find_start_time, 5)}s"
        )

    def switch_find_page(self, operation):  # 更改找到的结果的页数
        if self.page_administrator == []:
            return
        self.page_administrator[self.now_find_page].grid_remove()
        self.contain_item["查"]["属性-内容滚动框"]._parent_canvas.yview_moveto(
            0
        )  # 重置换页后滚动条的位置
        self.contain_item["查"]["属性-内容滚动框"].update_idletasks()
        if operation == "上一页":
            self.now_find_page -= 1
        elif operation == "下一页":
            self.now_find_page += 1
        elif operation == "重置":
            self.now_find_page = -1
            self.total_find_page = 1
        if operation != "重置":
            self.page_administrator[self.now_find_page].grid()
        self.contain_item["查"]["下一页"].configure(
            state=(
                "normal"
                if (self.now_find_page < self.total_find_page - 1)
                else "disabled"
            )
        )
        self.contain_item["查"]["下一页提示"].configure(
            message=(
                f"前往{self.now_find_page + 2}页"
                if (self.now_find_page < self.total_find_page - 1)
                else "没有下一页了哦"
            )
        )

        self.contain_item["查"]["上一页"].configure(
            state="disabled" if (self.now_find_page < 1) else "normal"
        )
        self.contain_item["查"]["上一页提示"].configure(
            message=(
                "没有上一页了哦"
                if (self.now_find_page < 1)
                else f"前往{self.now_find_page}页"
            )
        )

        self.contain_item["查"]["当前页/总页"].configure(
            text=f"当前页数:{self.now_find_page + 1}/{self.total_find_page}"
        )

    def init_find_name_page(self):  # 布局根据名称寻找歌曲的限制条件
        find_name_content_frame = ctk.CTkFrame(find_info_page)
        find_name_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["名称"] = find_name_content_frame

        rowi = 0
        seek_list = self.song_list + self.nickname_list
        select_song = combobox_frame(
            find_name_content_frame, "选择要查找的歌名称/俗称", "查找曲名", seek_list
        )
        select_song.configure(fg_color="transparent")
        select_song.set_size(230)
        select_song.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["名称-名称"] = select_song
        rowi += 1

        def filter_values(event):
            input_text = select_song.get().strip().lower()
            if not input_text:
                select_song.option_menu.configure(values=seek_list)
                return
            filtered = [item for item in seek_list if input_text in item.lower()]
            select_song.option_menu.configure(values=filtered)

        select_song.option_menu.bind("<KeyRelease>", filter_values)

        difficulty_choose = optionmenu_frame(
            find_name_content_frame,
            "选择查找难度",
            "查找难度",
            ["All"] + DIFFICULTY_LIST,
            "IN",
        )
        difficulty_choose.configure(fg_color="transparent")
        difficulty_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"][
            "名称-难度"
        ] = difficulty_choose  # 查找页面的名称页面下的难度控件
        rowi += 1

        find_name_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def init_find_composor_page(self):
        find_composor_content_frame = ctk.CTkFrame(find_info_page)
        find_composor_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["曲师"] = find_composor_content_frame
        find_composor_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        rowi = 0
        seek_list = self.composer_list
        select_song = combobox_frame(
            find_composor_content_frame, "选择要查找的曲师名称", "查找曲师", seek_list
        )
        select_song.configure(fg_color="transparent")
        select_song.set_size(230)
        select_song.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["曲师-名称"] = select_song
        rowi += 1

        def filter_values(event):
            input_text = select_song.get().strip().lower()
            if not input_text:
                select_song.option_menu.configure(values=seek_list)
                return
            filtered = [item for item in seek_list if input_text in item.lower()]
            select_song.option_menu.configure(values=filtered)

        select_song.option_menu.bind("<KeyRelease>", filter_values)

        difficulty_choose = optionmenu_frame(
            find_composor_content_frame,
            "选择查找难度",
            "查找难度",
            ["All"] + DIFFICULTY_LIST,
            "IN",
        )
        difficulty_choose.configure(fg_color="transparent")
        difficulty_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["曲师-难度"] = difficulty_choose
        rowi += 1

    def init_find_chapter_page(self):
        find_chapter_content_frame = ctk.CTkFrame(find_info_page)
        find_chapter_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["章节"] = find_chapter_content_frame

        rowi = 0
        seek_list = self.chapter_list
        select_song = combobox_frame(
            find_chapter_content_frame, "选择要查找的章节", "查找章节", seek_list
        )
        select_song.configure(fg_color="transparent")
        select_song.set_size(230)
        select_song.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["章节-名称"] = select_song
        rowi += 1

        def filter_values(event):
            input_text = select_song.get().strip().lower()
            if not input_text:
                select_song.option_menu.configure(values=seek_list)
                return
            filtered = [item for item in seek_list if input_text in item.lower()]
            select_song.option_menu.configure(values=filtered)

        select_song.option_menu.bind("<KeyRelease>", filter_values)

        difficulty_choose = optionmenu_frame(
            find_chapter_content_frame,
            "选择查找难度",
            "查找难度",
            ["All"] + DIFFICULTY_LIST,
            "IN",
        )
        difficulty_choose.configure(fg_color="transparent")
        difficulty_choose.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["章节-难度"] = difficulty_choose
        rowi += 1

        find_chapter_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def init_find_comment_page(self):
        find_comment_content_frame = ctk.CTkFrame(find_info_page)
        find_comment_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["简评"] = find_comment_content_frame

        rowi = 0

        comment_entry = entry_frame(find_comment_content_frame, "输入简评内容")
        comment_entry.configure(fg_color="transparent")
        comment_entry.set_size(230)
        comment_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["简评-名称"] = comment_entry
        rowi += 1

        find_comment_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def init_find_acc_page(self):
        find_acc_content_frame = ctk.CTkFrame(find_info_page)
        find_acc_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["acc"] = find_acc_content_frame
        rowi = 0

        min_entry = entry_frame(find_acc_content_frame, "最小acc(不写默认0)")
        min_entry.configure(fg_color="transparent")
        min_entry.set_size(230)
        min_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["acc-最小值"] = min_entry
        rowi += 1

        max_entry = entry_frame(find_acc_content_frame, "最大acc(不写默认100)")
        max_entry.configure(fg_color="transparent")
        max_entry.set_size(230)
        max_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["acc-最大值"] = max_entry
        rowi += 1

        find_acc_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def init_find_rks_page(self):
        find_rks_content_frame = ctk.CTkFrame(find_info_page)
        find_rks_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["单曲rks"] = find_rks_content_frame
        rowi = 0

        min_entry = entry_frame(find_rks_content_frame, "最小单曲rks(不写默认0)")
        min_entry.configure(fg_color="transparent")
        min_entry.set_size(230)
        min_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["单曲rks-最小值"] = min_entry
        rowi += 1

        max_entry = entry_frame(
            find_rks_content_frame, f"最大单曲rks(不写默认{MAX_LEVEL})"
        )
        max_entry.configure(fg_color="transparent")
        max_entry.set_size(230)
        max_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["单曲rks-最大值"] = max_entry
        rowi += 1

        find_rks_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def init_find_level_page(self):
        find_level_content_frame = ctk.CTkFrame(find_info_page)
        find_level_content_frame.configure(fg_color="transparent")
        self.grid_item["查"]["定数"] = find_level_content_frame
        rowi = 0

        min_entry = entry_frame(find_level_content_frame, "最小定数(不写默认0)")
        min_entry.configure(fg_color="transparent")
        min_entry.set_size(230)
        min_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["定数-最小值"] = min_entry
        rowi += 1

        max_entry = entry_frame(
            find_level_content_frame, f"最大定数(不写默认{MAX_LEVEL})"
        )
        max_entry.configure(fg_color="transparent")
        max_entry.set_size(230)
        max_entry.grid(row=rowi, column=0, pady=10, padx=10, sticky="nsew")
        self.contain_item["查"]["定数-最大值"] = max_entry
        rowi += 1

        find_level_content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    """爬虫"""

    def grab_info(self):
        # https://mzh.moegirl.org.cn/robots.txt 网站爬虫公开声明
        session = (
            requests.Session()
        )  # 创建一个持久化会话对象 用于在多个 HTTP 请求之间保持连接和共享配置（如 Cookies、Headers、代理等） 相比直接使用 requests.get() 能显著提升性能 尤其需要发送多次请求时
        retries = Retry(
            total=5,  # 最大重试次数 包含首次请求 实际最多6次
            backoff_factor=0.5,  # 重试间隔时间因子{backoff_factor} * (2^{重试次数-1})
            status_forcelist=[500, 502, 503, 504, 408, 429],  # 需要重试的HTTP状态码
            allowed_methods=["GET", "POST"],  # 允许重试的HTTP方法
        )
        session.mount(
            "http://", HTTPAdapter(max_retries=retries)
        )  # HTTPAdapter 是 requests 的底层适配器 mount() 将其绑定到会话的协议前缀
        session.mount(
            "https://", HTTPAdapter(max_retries=retries)
        )  # 为HTTPS请求配置重试机制

        # 设置请求头，模拟浏览器行为
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # 浏览器标识 直接抄 反反爬机制
            "Accept-Encoding": "gzip, deflate, br",  # 支持压缩传输以节省带宽
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # 声明客户端可处理的响应类型
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",  # 语言偏好
            "Connection": "keep-alive",  # 保持 TCP 连接复用
            "Cache-Control": "no-cache",  # 禁用缓存
            "Pragma": "no-cache",  # 兼容旧版HTTP
        }

        # 配置Chrome浏览器选项
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # 无头模式
        options.add_argument("--disable-gpu")  # 禁用GPU加速
        options.add_argument("--disable-images")  # 禁用图片加载
        options.add_argument("--disable-javascript")  # 禁用JavaScript
        options.add_argument("--disable-plugins")  # 禁用插件
        options.add_argument("--disable-extensions")  # 禁用扩展
        options.add_argument("--disable-dev-shm-usage")  # 禁用共享内存
        options.add_argument(
            "--window-size=1920,1080"
        )  # 设置窗口大小 无头浏览器仍会模拟视口（viewport）渲染页面 部分网站会检测视口尺寸（通过 window.innerWidth）非常规尺寸（如默认的 800x600）可能被识别为爬虫
        options.add_argument("--disable-notifications")  # 禁用通知弹窗
        options.page_load_strategy = "eager"  # 页面加载策略 比默认normal更快

        # 定义图片下载函数
        REQUEST_RATE_LIMIT = Semaphore(5)  # 令牌桶容量

        def download_image(img_url, complex_name, headers, retry_count=0):
            with REQUEST_RATE_LIMIT:
                try:
                    time.sleep(0.4)
                    response = session.get(
                        img_url, headers=headers, timeout=5
                    )  # 下载图片 超时时间（秒），避免无限等待 相对于之前的requests.get()更快
                    response.raise_for_status()  # 检查HTTP错误 如果状态码非2xx（如404/500），抛出 HTTPError 异常。
                    if not os.path.exists(image_path_prefix):  # 检查目录是否存在
                        os.makedirs(image_path_prefix)  # 创建目录
                    full_path = os.path.join(
                        image_path_prefix, f"{complex_name}.png"
                    )  # 跨平台拼接路径（避免硬编码/或\）
                    with open(full_path, "wb") as f:  # 二进制模式写入文件
                        f.write(response.content)
                    return True
                except Exception as e:  # 捕获所有异常
                    if retry_count <= 1:  # 最多重试1次
                        time.sleep(2**retry_count)  # 指数退避
                        return download_image(
                            img_url, complex_name, headers, retry_count + 1
                        )
                    print(f"下载图片失败 {complex_name}: {str(e)}")
                    return False

        # 初始化WebDriver
        try:
            driver = webdriver.Chrome(options=options)  # 创建Chrome实例
            driver.set_page_load_timeout(30)  # 设置页面加载超时时间
        except Exception as e:
            print(f"初始化WebDriver失败: {str(e)}")
            return

        # 加载页面函数
        def load_page(driver, url, max_retries=3):
            for attempt in range(max_retries):  # 最多重试3次
                try:
                    driver.get(url)  # 访问URL
                    wait = WebDriverWait(
                        driver, 10
                    )  # 等待元素出现 超时则抛出 TimeoutException
                    wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "table.wikitable")
                        )
                    )  # 等待至少一个匹配元素出现在DOM中（不保证可见/可交互）
                    return True
                except TimeoutException:  # 超时异常
                    if attempt == max_retries - 1:
                        print("页面加载超时")
                        return False
                    time.sleep(2)  # 等待2秒后重试
                except WebDriverException as e:  # WebDriver异常
                    if attempt == max_retries - 1:
                        print(f"页面加载错误: {str(e)}")
                        return False
                    time.sleep(2)
            return False

        try:
            if not load_page(
                driver,
                "https://mzh.moegirl.org.cn/Phigros/%E8%B0%B1%E9%9D%A2%E4%BF%A1%E6%81%AF",
            ):
                return

            tree = etree.parse(xmlpath)
            xmlroot = tree.getroot()
            self.get_song_list(xmlroot)
            add_idx = len(xmlroot) + 1  # 新id

            # 创建线程池用于并行下载图片
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=5
            ) as executor:  # 线程多了反而慢
                future_to_song = {}  # 存储future和song_id的映射

                alltable = driver.find_elements(By.CSS_SELECTOR, "table.wikitable")
                cnt = 0
                """
                tr
                0名称
                1图片 img.
                2章节 td 1.text
                3 td 1:BPM 3:曲师
                4 td 1:时长 3:画师
                5各种标题 省略
                6EZ等级 定数 物量 谱师
                7HD
                8IN
                (9AT)
                ...len(tr)
                """
                for tablei in alltable:  # 一个wikitable一首歌
                    try:
                        alltr = tablei.find_elements(By.TAG_NAME, "tr")  # 拿到所有行
                        cnt_tr = len(alltr)
                        diff_dic = {6: "EZ", 7: "HD", 8: "IN", 9: "AT"}  # 难度映射
                        song_data = {}
                        for tr_idx in range(cnt_tr):
                            try:
                                now_tr = alltr[tr_idx]
                                if tr_idx == 0:
                                    song_name = now_tr.text.replace("（", "(").replace(
                                        "）", ")"
                                    )
                                    song_name = re.sub(
                                        r"\[\d+\]", "", song_name
                                    )  # 有的名称有上标 全部去掉
                                    song_name = valid_test(
                                        "名称", song_name, self.nickname_dic, True
                                    )
                                    song_data["名称"] = song_name
                                    print(f"正在处理{cnt}.{song_name}")
                                    # print(f'')

                                elif tr_idx == 2:
                                    alltd = now_tr.find_elements(By.TAG_NAME, "td")
                                    song_data["章节"] = valid_test(
                                        "chapter", alltd[1].text, True
                                    )
                                    # print(f'章节{chapter}')

                                elif tr_idx == 3:
                                    alltd = now_tr.find_elements(By.TAG_NAME, "td")
                                    bpm = alltd[1].text
                                    if valid_test("bpm", bpm, True) == "error":
                                        bpm = "0"
                                    song_data["bpm"] = bpm
                                    # print(f'bpm{bpm}')

                                    composer = alltd[3].text
                                    composer = re.sub(r"\[\d+\]", "", composer)
                                    composer = valid_test("曲师", composer, True)
                                    song_data["曲师"] = composer
                                    # print(f'曲师{composer}')

                                    complex_name = f"{song_name}({composer})"
                                    if complex_name in self.song_list:
                                        # print(f'{complex_name}在列表中')
                                        song_idx = self.song_dic[complex_name]
                                        # song = xmlroot.xpath(f'//song[@id="{song_idx}"]')
                                        song = find_by_id(
                                            xmlroot, song_id=f"{song_idx}"
                                        )
                                        if song == []:
                                            print(f"无法找到{song_idx}:{complex_name}")
                                            break
                                        song = song[0]

                                    else:
                                        print(f"{complex_name}不在列表中")
                                        song = etree.Element("song")
                                        song.attrib["id"] = f"{add_idx}"
                                        add_idx += 1

                                    song_data["song_elm"] = song
                                    song_data["song_id"] = song.attrib["id"]

                                elif tr_idx == 4:  # 4td 1:时长 3:画师
                                    alltd = now_tr.find_elements(By.TAG_NAME, "td")

                                    time_span = valid_test("时长", alltd[1].text, True)
                                    if time_span == "error":
                                        time_span = "0.0"
                                    song_data["时长"] = time_span
                                    # print(f'时长{time_span}')

                                    drawer = valid_test("画师", alltd[3].text, True)
                                    # print(f'画师{drawer}')
                                    song_data["画师"] = drawer

                                elif tr_idx > 5:  # 6 EZ 等级 定数 物量 谱师 7HD 8IN 9AT
                                    alltd = now_tr.find_elements(By.TAG_NAME, "td")
                                    level = valid_test("定数", alltd[2].text, True)
                                    if level == "error":
                                        level = "0"
                                    note_cnt = valid_test("物量", alltd[3].text, True)
                                    if note_cnt == "error":
                                        note_cnt = "0"
                                    noter = valid_test("谱师", alltd[4].text, True)
                                    noter = re.sub(r"\[\d+\]", "", noter)
                                    now_diff = diff_dic[tr_idx]

                                    song_data[now_diff] = {
                                        "物量": note_cnt,
                                        "谱师": noter,
                                        "定数": level,
                                    }

                            except Exception as e:
                                print(f"处理行 {tr_idx} 时发生错误: {str(e)}")
                                continue

                        # 批量更新XML数据 重点加速部分
                        try:
                            song = song_data["song_elm"]
                            for key in ["名称", "曲师", "章节", "bpm", "时长", "画师"]:
                                if key in song_data:  # 抓取到数据了
                                    key_elm = song.find(key)
                                    if key_elm is not None:
                                        key_elm.text = song_data[key]
                                    else:
                                        etree.SubElement(song, key).text = song_data[
                                            key
                                        ]

                            for key in DIFFICULTY_LIST:
                                if key in song_data:
                                    diff_data = song_data[key]
                                    key_elm = song.find(key)
                                    if key_elm is not None:
                                        diff = key_elm
                                        for keyi, value in diff_data.items():
                                            diff_elm = diff.find(keyi)
                                            if diff_elm is not None:
                                                diff_elm.text = value
                                            else:
                                                etree.SubElement(diff, keyi).text = (
                                                    value
                                                )

                                        rks_elm = diff.find("单曲rks")
                                        if rks_elm is None:
                                            etree.SubElement(song, "单曲rks").text = "0"

                                        acc_elm = diff.find("acc")
                                        if acc_elm is not None:
                                            # 计算单曲rks
                                            if float(acc_elm.text) >= 70:
                                                singal_rks = str(
                                                    round(
                                                        float(diff.find("定数").text)
                                                        * pow(
                                                            (float(acc_elm.text) - 55)
                                                            / 45,
                                                            2,
                                                        ),
                                                        4,
                                                    )
                                                )
                                            else:
                                                singal_rks = "0"
                                            rks_elm.text = singal_rks
                                        else:
                                            etree.SubElement(song, "acc").text = "0"
                                    else:
                                        diff = etree.SubElement(song, key)
                                        for keyi, value in diff_data.items():
                                            etree.SubElement(diff, keyi).text = value
                                        etree.SubElement(diff, "acc").text = "0"
                                        etree.SubElement(diff, "单曲rks").text = "0"
                                        etree.SubElement(diff, "简评").text = "无"

                            if song.find("俗称") is None:
                                etree.SubElement(song, "俗称").text = "无"

                            # 异步下载图片
                            img_path = tablei.find_element(
                                By.CSS_SELECTOR, "img.lazyload"
                            ).get_attribute("data-lazy-src")
                            future = executor.submit(
                                download_image,
                                img_path,
                                valid_test(
                                    "文件路径",
                                    f"{song_data['名称']}({song_data['曲师']})",
                                ),
                                headers,
                            )
                            future_to_song[future] = (
                                f"{song_data['song_id']}.{valid_test('文件路径', f'{song_data['名称']}({song_data['曲师']})')}"
                            )

                        except Exception as e:
                            print(f"更新XML数据失败: {str(e)}")

                        cnt += 1
                        if cnt and ((cnt & 1) == 0):  # 每处理两个表格滚动一次
                            try:
                                driver.execute_script(
                                    """
                                    arguments[0].scrollIntoView({
                                        behavior: 'auto',
                                        block: 'end',
                                        inline: 'nearest'
                                    });
                                """,
                                    tablei,
                                )  # 将 tablei 转换为 JavaScript 可操作的 DOM 元素（通过 arguments[0] 传递）
                            except Exception as e:
                                print(f"滚动页面失败: {str(e)}")

                    except Exception as e:
                        print(f"处理表格时发生错误: {str(e)}")
                        continue

                print(f"总长{len(future_to_song)}")
                checkidx = 0
                print("等待处理中...")
                time.sleep(5)
                print("等待完成")
                for i, j in future_to_song.items():
                    print(i, j)
                try:
                    for future in concurrent.futures.as_completed(
                        future_to_song, timeout=GLOBAL_TIMEOUT
                    ):  # 生成器，按照任务完成的顺序（而非提交顺序）迭代 futures
                        song_info = future_to_song[future]
                        print(f"检查{checkidx}:", song_info)
                        checkidx += 1
                        try:
                            while not future.done():
                                print("等待")
                                time.sleep(0.1)
                            success = future.result(
                                timeout=SINGLE_TASK_TIMEOUT
                            )  # 单个任务最多等待时长
                            if not success:
                                print(f"图片 {song_info} 下载失败")
                        except concurrent.futures.TimeoutError:
                            print(f"图片 {song_info} 下载超时")
                        except Exception as e:
                            print(f"处理图片 {song_info} 时发生错误: {str(e)}")
                except TimeoutError:
                    print("全局超时")
                    for future, info in future_to_song.items():
                        print("关闭任务", info)
                        future.cancel()  # 取消所有未完成的任务
                    executor.shutdown(wait=False)  # 不等待，立即关闭线程池
                    driver.quit()  # 确保关闭浏览器
                    session.close()  # 资源释放 等效于文件用完关闭
                    print("关闭进程池")
                    return
            # 保存XML文件
            tree.write(xmlpath, encoding="utf-8", xml_declaration=True)
            self.get_song_list(xmlroot)
            print("爬取数据完成")

        except Exception as e:
            print(f"发生未知错误: {str(e)}")
        finally:
            try:
                driver.quit()  # 确保关闭浏览器
                session.close()  # 资源释放 等效于文件用完关闭
            except:
                pass

    """测试"""

    def test(self):  # 测试模块
        print("test start")
        print("test end")


phigros_root = phigros_data()
phigros_root.set_size(1000, 750, 720, 300)
phigros_root.mainloop()
