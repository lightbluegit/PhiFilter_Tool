# 动态配置
def pytest_configure(config):
    from rhythmgame_database.tests.run_test.run_valid_test import report_path
    config.option.htmlpath = report_path  # 动态注入路径
    config.option.self_contained_html = True
