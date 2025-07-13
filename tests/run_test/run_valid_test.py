import sys
import json
from pathlib import Path
import pytest
from dependencies.test_model import valid_test

# import sys
# from pathlib import Path
# sys.path.append(str(Path(__file__).parent.parent.parent))
# 第一次使用需要添加项目根目录到Python路径 记得写__init__
"""
python -m pytest python/rhythmgame_database/tests/run_test/run_valid_test.py -s
--html=bpm_reports.html
-k "test_bpm"  过滤测试用例
-m smoke  运行标记(@pytest.mark.smoke)的测试
-q  简化输出
-s  显示print输出
-v  详细输出
--lf/--last-failed  仅运行上次失败的用例
--html={路径}  在指定路径处生成html诊断文件
--junitxml={路径}  在指定路径处生成JUnit格式(xml)诊断文件
--pdb  失败后进入调试 (Pdb) print(variable) 即输入代码进行查看
--trace  立即进入调试 (Pdb) continue 继续运行
"""

["bpm", "单曲rks", "物量", "时长"]
test_part = "bpm"
JSON_PATH = "python/rhythmgame_database/tests/test_data/valid_case.json"
report_path = f"python/rhythmgame_database/tests/reports/{test_part}_reports.html"


def load_cases(test_part):  # 加载指定测试数据
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data[test_part]


@pytest.mark.parametrize(
    "case",  # 通过传入的参数与下面调用的函数的参数名称一致来进行匹配
    load_cases(test_part),  # 生成测试用例
    ids=lambda case: f"{case['test_id']}:{case['description']}",  # 提示语句
)
def test_func(case):  # 测试函数(必须紧跟在后面)
    actual = valid_test(test_part, case["input"])
    assert actual == case["expected"], (
        f"\n{case['test_id']}:"  # 外层用双引号 内层用单引号 防止f混淆
        f"\n输入:{case['input']}"
        f"\n正确输出:{actual}"
        f"\n实际输出:{case['expected']}"
        f"\n数据描述:{case['description']}"
    )
