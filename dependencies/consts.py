PATH = {
    "database_code": "python/rhythmgame_database/database.py",
    "xml": "python/rhythmgame_database/phigros_data.xml",
    "image_prefix": "python/rhythmgame_database/images/song_illustration/",
    "icon_prefix": "python/rhythmgame_database/images/icons/",
}
FONT = {
    "ctext_font": "python/rhythmgame_database/dependencies/fonts/NotoSerifSC-VariableFont_wght.ttf",
    "ctitle_font": "仿宋",
    "ctext_size": 20,
    "ctitle_size": 25,
}

MAX_LEVEL = 17.6
DIFFICULTY_LIST = ["AT", "IN", "HD", "EZ"]
DIFFICULTY_COLOR = {"AT": "#ff8aba", "IN": "#ff6a5c", "HD": "#3D71B2", "EZ": "#5ffe5d"}
COMMEN_ATTRI = [
    "歌曲id",
    "名称",
    "曲师",
    "俗称",
    "章节",
    "bpm",
    "时长",
    "画师",
]  # 通用属性
DIFF_ATTRI = ["定数", "acc", "单曲rks", "简评", "物量", "谱师"]  # 难度差分属性
SINGLE_TASK_TIMEOUT = 1  # 单个检查超时限制
GLOBAL_TIMEOUT = 5  # 全局超时限制
