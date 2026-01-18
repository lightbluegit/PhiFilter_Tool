import pandas as pd
from pathlib import Path
import json
import time

import pandas as pd
import os

# 从info.tsv中读取新的信息
df = pd.read_csv(
    filepath_or_buffer="python/rhythmgame_database/assets/data/info.tsv",
    sep="\t",
    header=None,
    encoding="utf-8",
    names=["c_name", "name", "composer", "drawer", "EZ", "hd", "in", "at", "lgc"],
)
df = df.fillna("")
preinfo_list: list[str] = [
    "# 组合名称\nCOMBINE_NAME: list[str] = [",
    "# 曲名\nSONG_NAME_LIST: list[str] = [",
    "# 曲师\nCOMPOSER_LIST: list[str] = [",
    "# 画师\nDRAWER_NAME_LIST: list[str] = [",
    "# 谱师\nCHARTER_LIST: list[str] = [",
]
dft_file = open(
    "python/rhythmgame_database/src/core/update/default_file.txt",
    "w",
    encoding="utf-8",
)
with open(
    "python/rhythmgame_database/src/core/update/output.txt",
    "w",
    encoding="utf-8",
) as f:
    # 一行一行输出 然后手动更新到consts的缓存里面
    for i in range(4):
        f.write(preinfo_list[i])
        for _, row in df.iterrows():
            text = (
                row.iloc[i]
                .replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace('"', '\\"')
            )
            if not i:
                dft_file.write(f"{text},\n")
            f.write(f'"""{text}""",\n')  # 三引号防止换行 单个  \  '  "  换成转义形式
        f.write("]\n")

    f.write(preinfo_list[4])
    # 更新谱师列表
    chapter = set()
    for idx in range(4, 9):
        for _, row in df.iterrows():
            chapter.add(row.iloc[idx])
    for chapteri in chapter:
        if chapteri:
            f.write(
                f'\"\"\"{chapteri.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')}\"\"\",\n'
            )
    f.write("]\n")

dft_file.close()
