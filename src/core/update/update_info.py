import pandas as pd
from pathlib import Path
import json
import time


def update_note_count_csv():
    """根据文酱的Phigros_Resource-master获取的 谱面chart 文件更新note_count文件"""
    start_time = time.time()

    folder_path = "C:/Users/Administrator/Downloads/Phigros_Resource-master/chart"  # 替换为Phigros_Resource-master/chart文件对应的地址
    folder = Path(folder_path)

    csv_path = "projects/PhiFilterTool/assets/data/note_count.csv"
    df = pd.read_csv(
        csv_path,
        sep=",",
        header=None,
        encoding="utf-8",
        names=["combine_name", "tap", "hold", "drag", "flick", "sum"],
        index_col=0,
    )
    df = df.fillna("")

    for song_folderi in folder.glob("*"):  # rglob 递归，glob 非递归
        if song_folderi.is_dir():  # 依次选中所有文件夹 (暗夜苏醒REANIMATE.Warak.0)
            combine_name = song_folderi.name[
                :-2:
            ]  # 去掉最后的 '.0' (random有差分 .0~.6)
            for charti in song_folderi.glob(
                "*json"
            ):  # 读取文件夹中所有的json文件 (EZ.json)
                cname_with_diff = (
                    f"{combine_name}.{charti.name.replace('.json', '')}"  # 构建 键
                )
                json_path = f"{folder_path}/{song_folderi.name}/{charti.name}"
                tap_count = 0
                drag_count = 0
                hold_count = 0
                flick_count = 0
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)  # 解析json文件
                    list = data["judgeLineList"]  # 以 996的EZ为例方便弄懂结构
                    for dicti in list:
                        for notei in dicti["notesAbove"] + dicti["notesBelow"]:
                            if notei["type"] == 1:
                                tap_count += 1
                            elif notei["type"] == 2:
                                drag_count += 1
                            elif notei["type"] == 3:
                                hold_count += 1
                            elif notei["type"] == 4:
                                flick_count += 1
                df.at[cname_with_diff, "tap"] = int(tap_count)
                df.at[cname_with_diff, "drag"] = int(drag_count)
                df.at[cname_with_diff, "hold"] = int(hold_count)
                df.at[cname_with_diff, "flick"] = int(flick_count)
                df.at[cname_with_diff, "sum"] = int(
                    tap_count + drag_count + hold_count + flick_count
                )
                # print(
                #     f"{cname_with_diff}统计数据是:{tap_count}, {drag_count}, {hold_count}, {flick_count}, 总共{tap_count + drag_count + hold_count + flick_count}"
                # )
    df.to_csv(csv_path, header=False, encoding="utf-8", index=True)

    print(f"所有歌曲的note计数更新完成 用时{time.time() - start_time}")


update_note_count_csv()

# 从info.tsv中读取新的信息
df = pd.read_csv(
    filepath_or_buffer="projects/PhiFilterTool/assets/data/info.tsv",
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
    "projects/PhiFilterTool/src/core/update/default_file.txt",
    "w",
    encoding="utf-8",
)
with open(
    "projects/PhiFilterTool/src/core/update/output.txt",
    "w",
    encoding="utf-8",
) as f:
    # 一行一行输出 然后手动更新到consts的缓存里面
    for i in range(4):
        f.write(preinfo_list[i])
        for _, row in df.iterrows():
            # combine_name = row.iloc[0]
            # name = row.iloc[1]
            # composer = row.iloc[2]
            # drawer = row.iloc[3]
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
