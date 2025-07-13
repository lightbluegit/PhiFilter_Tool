from tkinter import messagebox
from .consts import MAX_LEVEL
import re


def split_complex_name(complex_name):
    if ('(' not in complex_name):
        return None
    blanket_idx = complex_name.rindex('(')
    name = complex_name[:blanket_idx:]
    composer = complex_name[blanket_idx + 1::].replace(')', '')
    return (name, composer)


def valid_test(s_type, val, nickname_dic=None, ban=False):
    val = val.strip()
    if (not val):
        return '无'

    def invalid_float_char(attri_type, val, ban):
        valid_char = [str(i) for i in range(10)] + ['.']
        error_char = ''
        point_cnt = 0
        for i in val:
            if (i not in valid_char):
                error_char += i
            elif (i == '.'):
                point_cnt += 1
                if (point_cnt > 1):
                    # if (not ban):
                    #     messagebox.showerror(f'{attri_type}报错', '输入中包含过多小数点')
                    return 'error'
        # if (not ban):
        #     messagebox.showerror(f'{attri_type}报错', f'输入中包含 {set(error_char)} 等非法字符')
        return 'error'

    def valid_float(attri_type, val, minn, maxx, ban):
        try:
            rst = float(val)
            if (minn <= rst <= maxx):
                return str(rst)
            else:
                if (not ban):
                    messagebox.showerror(f'{attri_type}非法范围', f'哪有{attri_type}为{rst}的歌啊?\n有效范围{minn}~{maxx}')
                return 'error'
        except:
            return invalid_float_char(attri_type, val, ban)

    if (s_type == '名称' and nickname_dic is not None):
        if (val in nickname_dic.keys()):
            val = nickname_dic[val]
            # print(f'俗称转名称:{val}')

    elif (s_type in ['定数', '单曲rks']):
        return valid_float(s_type, val, 0, MAX_LEVEL, ban)

    elif (s_type == 'acc'):
        return valid_float(s_type, val, 0, 100, ban)

    elif (s_type == '物量'):
        if (val.isdigit()):
            return str(int(val))
        if (not ban):
            messagebox.showerror(f'{s_type}非法输入', f'{s_type}必须是纯数字')
        return 'error'

    elif (s_type == 'bpm'):
        val = val.replace(' ', '')  # 避免空格输入干扰
        valid_char = [str(i) for i in range(10)] + ['~', '.']
        range_type = False
        for chari in val:
            if (chari not in valid_char):
                return 'error'
            elif (chari == '~'):
                if (range_type):  # 多个波浪号 并非合法范围
                    return 'error'
                range_type = True
        try:
            if (range_type):
                splited_val = val.split('~')
                min_bpm = float(splited_val[0])
                max_bpm = float(splited_val[1])
                if ((max_bpm <= min_bpm) or (min_bpm <= 0)):  # 有~应该是范围 == 的情况不合法
                    return 'error'
                return f'{min_bpm}~{max_bpm}'
            else:  # 无 '~' 单个数字
                val = float(val)
                if (val <= 0):
                    return 'error'
                return str(val)
        except:
            return 'error'

    elif (s_type == '时长'):
        try:
            if (':' in val):
                val = val.replace(':', '.')  # 适应网页读取
            val = val.replace(" ", '')
            if (val.count('.') == 1):
                temp_val = val.split('.')
                fen = int(temp_val[0])
                miao = int(temp_val[1])
                if (60 <= miao or miao < 0 or miao + fen == 0):
                    if (not ban):
                        messagebox.showerror(f'{s_type}非法输入', f'哪有{temp_val[1]}秒啊?')
                    return 'error'
                return f'{fen}.{miao}'
            else:
                return 'error'
        except:
            return invalid_float_char(s_type, val, ban)

    elif (s_type == '每页条数'):
        try:
            val = int(val)
            if (val <= 0):
                if (not ban):
                    messagebox.showerror(f'{s_type}输入错误', '输入值<=0了')
                return 'error'
            elif (val > 50):
                if (not ban):
                    messagebox.showwarning(f'{s_type}输入不合理', '输入值>50了,单页布局这么多容易造成积压')
                return 'error'
        except:
            if (not ban):
                messagebox.showerror(f'{s_type}输入错误', '输入非整数')
            return 'error'

    elif (s_type == '文件路径'):
        return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', val)

    return val
