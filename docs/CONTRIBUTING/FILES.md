# 1 assets：资产文件
存放静态资源文件 如图片、字体等
## 1.1 data：统计文件
存放难度 歌曲信息等统计文件

### 1.1.1 default_comment.csv

每行为一个信息，代表玩家对指定歌曲的简评
例：`Glaciaxion.SunsetRay,EZ_comment,HD_comment,IN_comment,AT_comment`

| 信息  | Glaciaxion | SunsetRay | EZ_comment | HD_comment | IN_comment | AT_comment |
| --- | ---------- | --------- | ---------- | ---------- | ---------- | ---------- |
| 含义  | 曲名         | 曲师        | 对EZ难度的简评   | 对HD难度的简评   | 对IN难度的简评   | 对AT难度的简评   |

### 1.1.2 default_group.csv

每行为一个信息，代表玩家对指定歌曲的分组信息
例：```Glaciaxion.SunsetRay,groupa`groupb ```

| 信息  | Glaciaxion | SunsetRay | groupa\`groupb    |
| --- | ---------- | --------- | ----------------- |
| 含义  | 曲名         | 曲师        | 对歌曲的分组 通过 \` 进行拼接 |

### 1.1.3 difficulty.tsv
每行为一个信息，用组合名称代表指定歌曲并记录对应难度的定数

组合名称：通过 **曲名.曲师名称**(只保留文字和字母 去除下划线 空格 点和特殊符号) 拼接得到
此处不单用曲名来区分主要是为了区分`Another Me`之类的同名歌曲的情况

例：`大和撫子WildDances.adapatorvsDRIVE	5.5	11.8	15.1`

| 结构： | 组合名称 | 曲名 | 曲师 | EZ难度定数 | HD难度定数 | IN难度定数 | AT难度定数(可能没有) |
| --- | ------------------------------ | ------------------ | ------------------ | ------ | ------ | ------ | ------------ |
| 示例： | 大和撫子WildDances.adapatorvsDRIVE | 大和撫子 -Wild Dances- | adapator vs DRIVE. | 5.5    | 11.8   | 15.1   | 无 |

### 1.1.4 info.tsv
每行为一个信息，提供组合名称 名称 曲师 画师 各个难度谱师 等信息

例：`心の記憶.A39沙包P 心の記憶	A-39/沙包P	爱39的Konya	Su1fuR	Su1fuR	N-23`

| 结构： | 组合名称 | 曲名   | 曲师       | 画师        | EZ难度谱师 | HD难度谱师 | IN难度谱师 | AT难度谱师(可能没有) | Legacy难度谱师(可能没有) |
| --- | ------------------- | ---- | -------- | --------- | ------ | ------ | ------ | ------------ | ---------------- |
| 示例： | 心の記憶.A39沙包P         | 心の記憶 | A-39/沙包P | 爱39的Konya | Su1fuR | Su1fuR | N-23   |              |                  |

> 注意⚠️：目前只有`Lyrith -迷宮リリス-`有`Legacy难度谱师`这一项属性

### 1.1.5 note_count.csv
每行为一条记录 提供指定歌曲的某一难度的各种note统计信息

例：`大和撫子WildDances.adapatorvsDRIVE.IN,699.0,33.0,201.0,69.0,1002.0`

| 结构  | 组合名称.难度    | tap数 | hold数 | drag数 | flip数 | 总note数 |
| --- | ---------- | ---- | ----- | ----- | ----- | ---- |
| 示例  | 大和撫子WildDances.adapatorvsDRIVE.IN | 699  | 33    | 201   | 69   | 1002  |

## 1.2 font：字体文件
**来自Google Font的字体在使用时记得保留`OFL.txt`许可文件**
* `Source Han Sans & Saira Hybrid-Regular #5446.ttf`：中文字体
* `Playfair_Display`：英语字体
* `Share_Tech_Mono`：数字字体

## 1.3 images：图片素材

### 1.3.1 avatars
存储头像图片
直接以**头像素材名**命名 与玩家信息中的头像信息一致
例：`Marenol extra 1 -by 喵n葵.png`

### 1.3.2 backgrounds
存储主页小卡片背景图片以及歌曲卡片上层平行四边形背景
`green-EZ`：歌曲难度为EZ的时候使用的上层背景 以及 课题模式
`blue-HD`：歌曲难度为HD的时候使用的上层背景
`red-IN`：歌曲难度为IN的时候使用的上层背景
`gold-AT`：歌曲难度为AT的时候使用的上层背景
`colorful`：课题模式达到分时的背景
`white`：未尝试过课题模式时的背景

`default_rks_conpone_card_bg`：跳转至 rks组成页 卡片背景
`default_update_card_bg`：手动更新功能 卡片背景
`calculate_score_card_bg`：跳转至 计算分数是否可达页 卡片背景

### 1.3.3 icons
存储各种小图标
#### score_level_icons
存储各个评级的图标

# 2. docs：文档
## 2.1 CONTRIBUTING
贡献指南文档

### 2.1.1 CONTRIBUTING.md
贡献指南内容总览与中转

### 2.1.2 FILES.md
存储各个文档的详细内容解释以及格式解析

### 2.1.3 PAGE_DESIGN.md
存储各个页面的设计内容以及各个子控件对应的变量名

## 2.2 README
### 2.2.1 README_img
存储README文档用到的图片素材

### 2.2.2 README_zh-CN.md
中文版README文档

## 2.3 README.md
英文版README文档(显示在主页的那版)

# 3. src：源代码目录
## 3.1 core
存储实现特定功能的文件

### 3.1.1 phi_cloud
实现与TapTap的通信以及二维码生成功能

#### 3.1.1.1 get_play_data.py
整合了千柒的函数，待重写

### 3.1.2 update
快捷更新

#### 3.1.2.1 default_file.txt
默认文件(default_comment/default_group)内容输出位置

#### 3.1.2.2 output.txt
缓存内容(曲名 组合名称 曲师名称...)输出 直接缓存在consts文件里

#### 3.1.2.3 update_info.py
运行后自动根据 谱面chart 文件更新note_count文件
将缓存输出至output.txt文件中
将默认文件内容输出到default_file.txt文件中

## 3.2 ui
### 3.2.1 styles.py
加载字体 将各个控件的样式配置封装为函数的模版

### 3.2.2 widgets.py
存储各个重写/组合的控件

## 3.3 utils
### 3.3.1 base.py
存储通用函数 如日志输出及根据运行环境控制文件路径

### 3.3.2 consts.py
存储各种常量(路径 最高定数等) 和缓存内容

# 4. main.py
程序的入口 运行主文件以启动应用

# 5. requirements.txt
记录运行依赖

# 6 记录文件
## 6.1 (user_name)_comment.csv
存放指定玩家对每个歌曲的评论

| 结构  | 组合名称                | 对EZ难度的评论   | 对HD难度的评论 | 对IN难度的评论 | 对AT难度的评论 |
| --- | ------------------- | ---------- | -------- | -------- | -------- |
| 示例  | dBdoll.YUESTEVENuen | 万物起源(doge) |          |          |          |

## 6.2 (user_name)_group.csv
存放指定玩家对歌曲的分组
同一难度的不同分组用 \` 隔开

| 结构  | 组合名称                | 对EZ难度的分组 | 对HD难度的分组 | 对IN难度的分组 | 对AT难度的分组 |
| --- | ------------------- | -------- | -------- | -------- | -------- |
| 示例  | dBdoll.YUESTEVENuen | 好听\`练习曲  |          |          |          |


## 6.3 PhiFilterTool_log.txt
存放输出的日志

## 6.4 session_token.json
存放玩家的session_token
last_user用于加载上一次使用的记录

```json
{
    "last_user": "(user_name)",
    "(user_name)": "(user_token)"
}
```

## 6.5 PhiFilterTool_setting.json
存储玩家的设置数据 可在设置页面进行更改

```json
{
    "(user_name)": {
        "main_setting": { // 主要设置
            "always_update": false, // 是否常更新
            "default_open_page": "home_page" // 开启时默认显示页面
        },
        "search_page_setting": { // 搜索页面设置
            "default_filter": { // 默认搜索内容
                "attribution": "acc",
                "limit": "大于",
                "value": "99.3"
            }
        }
    }
}
```