# PhiFilterTool贡献指南
文件树总览：
```
PhiFilterTool/
├── assets/                       # 资源文件
│   ├── data/                     # 数据文件
│   │   ├── avatar.txt            # 头像对应
│   │   ├── default_comment.csv   # 初始化简评表
│   │   ├── default_group.csv     # 初始化分组表
│   │   ├── difficulty.tsv        # 难度数据
│   │   ├── info.tsv              # 歌曲信息
│   │   └── note_count.csv        # 键型数量
│   ├── fonts/                    # 字体文件
│   │   └── Source Han Sans & Saira Hybrid-Regular #5446.ttf
│   ├── images/                   # 图片资源
│   │   ├── avatars/              # 头像
│   │   ├── backgrounds/          # 背景图
│   │   ├── icons/                # 图标score_level_icons
│   │   │   └── score_level_icons/# 评级图标
│   │   └── illustrations/        # 曲绘
├── docs/                         # 文档目录
│   ├── README.md                 # 主文档
│   ├── CONTRIBUTING              # 贡献指南
│   │   └── CONTRIBUTING.md       # 总览
│   └── README/                   # 其他语言的README文件
│       └── README_zh-CN.md       # 中文文档
├── src/                          # 源代码目录
│   ├── core/                     # 核心逻辑模块
│   │   ├── phi_cloud/            # 获取用户数据的项目(来自千柒)
│   │   │    └── get_play_data.py
│   │   └── update                # 快捷同步phigros更新
│   │        ├── output.txt       # 格式化更新输出
│   │        └── update_info.py
│   ├── ui/                       # 界面模块
│   │   ├── widgets.py            # 自定义控件
│   │   └── styles.py             # 样式函数
│   └── utils/                    # 工具
│       ├── consts.py             # 自定义控件
│       └── base.py               # 基础函数：日志输出 文件位置转换等
├── main.py                       # 主程序
└── LICENSE                       # GPL-3.0许可证文件
```
存放可读写信息的文件夹：
```
PhiFilterTool/                 # 
├── username_comment.csv       # 玩家(username)对每首歌的简评
├── username_group.csv         # 玩家(username)对每首歌的分组
├── PhiFilterTool_infolog.log  # 普通日志文件
├── PhiFilterTool_log.log      # 反馈时建议提交的报错日志文件
├── PhiFilterTool_setting.json # 玩家配置文件
└── session_token.json         # 存放玩家token
```

各个文件详细作用以及规范见：<a href="FILES.md">文件解析</a>

如果您希望优化现有的页面，<a href="PAGE_DESIGN.MD">页面设计信息</a> 可以帮助您更快地了解代码中各个部分的作用
