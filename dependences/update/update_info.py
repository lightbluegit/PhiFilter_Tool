import pandas as pd
from ..consts import INFO_PATH, OUTPUT_PATH

# 从info.tsv中读取新的信息
df = pd.read_csv(
    INFO_PATH,
    sep="\t",
    header=None,
    encoding="utf-8",
    names=["c_name", "name", "composer", "drawer", "EZ", "hd", "in", "at", "lgc"],
)
df = df.fillna("")
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    # 一行一行输出 然后手动更新到consts的缓存里面
    # for _, row in df.iterrows():
    #     combine_name = row.iloc[0]
    #     name = row.iloc[1]
    #     composer = row.iloc[2]
    #     drawer = row.iloc[3]
    #     f.write( # 三引号防止换行 单个  \  '  "  换成转义形式
    #         f'\"\"\"{drawer.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')}\"\"\",\n')

    # 更新谱师列表
    chapter = set()
    for idx in range(4, 9):
        for _, row in df.iterrows():
            chapter.add(row.iloc[idx])
    for chapteri in chapter:
        f.write(
            f'\"\"\"{chapteri.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')}\"\"\",\n'
        )
