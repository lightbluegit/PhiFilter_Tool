import pandas as pd

df = pd.read_csv(
    "projects/PhiFilter Tool/dependences/info.tsv",
    sep="\t",
    header=None,
    encoding="utf-8",
    names=["c_name", "name", "composer", "drawer", "EZ", "hd", "in", "at", "lgc"],
)
df = df.fillna("无")  # 将NaN替换为空字符串
with open("projects/PhiFilter Tool/dependences/update/output.txt", "w", encoding="utf-8") as f:
    # for _, row in df.iterrows():
    #     combine_name = row.iloc[0]
    # name = row.iloc[1]
    # composer = row.iloc[2]
    # drawer = row.iloc[3]
    # f.write(
    #     f'\"\"\"{drawer.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')}\"\"\",\n'
    # )
    chapter = set()
    for idx in range(4, 9):
        for _, row in df.iterrows():
            chapter.add(row.iloc[idx])
    for chapteri in chapter:
        f.write(
            f'\"\"\"{chapteri.replace("\\", "\\\\").replace("\'", "\\'").replace('\"', '\\"')}\"\"\",\n'
        )
