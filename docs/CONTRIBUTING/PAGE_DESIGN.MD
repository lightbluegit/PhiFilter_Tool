全局存储的控件键值对及其意义
```python
# 伪代码描述
self.widgets = {
    'basepage': { # 基础页面布局 切开内容区和导航栏区
        'main_layout': 左右向布局 布局导航栏和内容栏,
        'navigation_interface': 导航栏,
        'content_widget': 内容页面管理器,
    }
    'home_page': {
        'widget': 主控件,
        'main_layout': 纵向布局,
        'flow_layout': 布局快捷跳转卡片,
        'tip_layout': 布局左下角tips,
        'tip_label': tip的文本控件,
        # 卡片集合
        'generate_rsk_conpone_card': 生成rks组成,
        'update_savedata_card': 重新拉取数据,
        'calculate_score_card': 计算分数是否可达,
    }
    'place_b27_phi3_page':{
        'widget': 主控件,
        'main_layout': 纵向布局,
        'player_rks_label': 展示玩家rks的控件
        'b27_folder': b27文件夹控件,
        'phi3_folder': phi3文件夹控件':{
        'widget': 主控件,
        'main_layout': 纵向布局,
        
        'scroll_area': 滚动区域,
        'scroll_content_widget': 滚动区域内容控件,
        'flow_layout': 流式布局滚动区域内容,
        'filter_obj_list': 筛选条件组件列表,
        
        'filter_confirm_widget': 确认按钮区域控件,
        'filter_confirm_layout': 横向布局,
        'filter_from_all_song_btn': 从所有歌曲中筛选,
        'filter_from_previous_song_btn': 从之前筛选的结果中继续筛选,
        
        'result_widget': 搜索结果布局区域,
        'result_layout': 纵向布局,
        
        'group_widget': 分组 or 排序依据控件,
        'group_widget_layout': 横向布局,
        'reset_page_btn': 终止标签,
        'sort_result_reverse_btn': 排序顺序转换按钮,
        'sort_by': 排序依据,
        'group_by': 分组依据,
        
        'result_display_scroll': 筛选后的歌曲卡片布局区域,
        'result_display_content': 结果展示控件,
        'result_display_flow': 流式布局,
        
        'card_and_folder': 列表 装的folder和歌曲卡片 用于重置时的清理
    }
    'edit_info_page': {
        'widget': 主控件,
        'main_layout': 横向布局,
        
        'display_widget': 展示区域,
        'display_layout': 竖向布局,
        'song_info_card': 展示位的歌曲,
        'example_song': 默认展示歌曲 退出的时候重新布局用的,
        
        'edit_widget': '编辑区域'控件,
        'edit_layout': 竖向布局,
        'group_ccb': 分组选择控件,
        'comment_label': 简评填写控件,
        'confirm_btn': 确认更改按钮,
    }
    'account_page':{
        'widget': 主控件,
        '暂存': 没有token的时候暂时使用的无背景主控件,
        'layout': 网格式布局,
        
        # 无token时的布局
        'QRcode_img': 二维码放置位置,
        'login_confirm_btn': 生成授权二维码按钮,
    }
    'score_calculate_page': {
        'widget': 主控件,
        'main_layout': 横向布局,
        'song_info_card': 布局在右边的卡片,
        'example_song': 默认歌曲卡片,
        'result_list': 存储合法结果,

        # 左侧
        'left_widget': 左侧主控件,
        'left_layout': 纵向布局,
        'score_input_elm': 分数输入,
        'sort_result_reverse_btn': 计算结果 从小到大 or 从大到小 转换按钮,
        'sort_by': 排序依据,
        'label_title': 合法结果的表头 哪一行代表什么,

        'result_display_scroll': 滚动布局,
        'result_display_content': 内容部分,
        'result_display_flow': 流动布局,
        'start_calculate_btn': 开始计算按钮, 

        # 右侧
        'right_widget': 歌曲卡片展示部分主控件,
        'display_layout': 纵向布局,
        'score_display_widget_list': 存储布局的结果控件,
    }
    'setting_page':{
        'widget': 主控件,
        'main_layout': 纵向布局,
        'segment': 顶部页面栏,
        'stacked_layout': 页面栈 管理当前展示的页面,
        'confirm_btn': 保存设置按钮,
        
        # 总设置页面
        'main_setting_widget': 总设置页面主控件,
        'main_setting_layout': 纵向布局,
        'always_update_sbtn': 常更新 or 懒更新 切换按钮,
        'default_open_page': 默认启动页选择,

        # 搜索页面设置
        'search_setting_widget': 搜索设置页面主控件,
        'search_setting_layout': 纵向布局,
        'default_filter_obj': 默认筛选条件,
    }
}
```