import re

def ass_time_to_cs(time_str):
    """将ass时间格式转换为厘秒数"""
    hours, minutes, rest = time_str.split(':', 2)
    seconds, centiseconds = rest.split('.')
    return (int(hours)*3600 + int(minutes)*60 + int(seconds)) * 100 + int(centiseconds)

def cs_to_lrc_time(cs):
    """厘秒数转lrc时间格式（MM:SS:CS）"""
    minutes = cs // 6000
    cs %= 6000
    seconds = cs // 100
    centiseconds = cs % 100
    return f"[{minutes:02d}:{seconds:02d}:{centiseconds:02d}]"

def ass2lrc(ass_txt, partwk = True, partwk_logocs = 0, tail = False):
    """
        逐行转换.ass为.lrc格式，支持连结注音格式转换，可设置是否保留句末延长时间
    """
    parts = ass_txt.split(',', 9)
    assert len(parts) == 10, "此行属性有缺失！"
    start_cs = ass_time_to_cs(parts[1].strip())
    if partwk: # 暂未实现注音处分词
        speaker = '【'+parts[4]+'】' if parts[4]!='' else ''
        content = re.sub(r'{\\k(-?\d+\.?\d*)}{\\-([^\\{}]+)}([^{])', r'{\\-\2}{\\k\1}\3', parts[9])
        content = re.sub(r'{\\k(-?\d+\.?\d*)\\-([^\\{}]+)}', r'{\\-\2}{\\k\1}', content)
        content = re.sub(r'{\\-([^\\{}]+)\\k(-?\d+\.?\d*)}', r'{\\-\1}{\\k\2}', content)
        content = re.sub(r'{\\-([^\\{}]+)}', r'{\\k0}【\1】', content)
#         content = re.sub(r'{\\-([^\\{}]+)}', r'{\\k-'+str(partwk_logocs)+r'}{\\k'+str(partwk_logocs)+r'}【\1】', content)
    else:
        speaker = ''
        content = re.sub(r'\\-[^{}\\]+', '', re.sub(r'{\\-[^{}\\]+}', '', parts[9]))
        content = re.sub(r'{\\pos[^{}\\]+}', '', content) # vmoe位置信息处理
    t1 = re.split(r'{\\k(-?\d+\.?\d*)}', content)
    assert '#' not in t1[0], "此行首个k值前含有#号！"
    mojiraw = [t1[i] for i in range(0, len(t1), 2)]
    timekraw = [start_cs]
    timekraw += [int(t1[i]) for i in range(1, len(t1),2)]
    for i in range(1, len(timekraw)):
        timekraw[i] += timekraw[i-1]
    moji_furistruct = []
    for i in mojiraw:
        if '|' not in i:
            moji_furistruct.append((0,))
        else:
            concat = 0
            if '|<' in i:
                tmp_base, tmp_ruby = i.split('|<', 1)
            else:
                tmp_base, tmp_ruby = i.split('|', 1)
                concat = 1
            assert tmp_base!='', "此行空字符串有注音假名！"
            if tmp_base=='#' and moji_furistruct[-1][0] in (1,2):
                moji_furistruct.append((2, '', tmp_ruby))
            else: moji_furistruct.append((1, tmp_base, tmp_ruby, concat))
    lrctxt = speaker + mojiraw[0]
    furi_base, furi_ruby, base_plus = '', '', 0
    for i in range(0, len(timekraw)-1):
        if (moji_furistruct[i+1][0]==0 or moji_furistruct[i+1][0]==1 and moji_furistruct[i+1][3]==0) and furi_base!='':
            lrctxt += '{' + furi_base + '|' + furi_ruby + base_plus*'＋' + '}'
            furi_base, furi_ruby, base_plus = '', '', 0
        elif moji_furistruct[i+1][0]==1 and moji_furistruct[i+1][3]==1 and furi_base!='':
            furi_ruby += (base_plus+1) * '＋'
            base_plus = 0
        if moji_furistruct[i+1][0] == 0:
            lrctxt += cs_to_lrc_time(timekraw[i])
            lrctxt += mojiraw[i+1]
        elif moji_furistruct[i+1][0] == 1:
            furi_base += moji_furistruct[i+1][1]
            furi_ruby += cs_to_lrc_time(timekraw[i])+moji_furistruct[i+1][2]
            base_plus = max(len(moji_furistruct[i+1][1])-1, 0)
        else:
            furi_ruby += cs_to_lrc_time(timekraw[i])+moji_furistruct[i+1][2]
    if furi_base!='':
        lrctxt += '{' + furi_base + '|' + furi_ruby + base_plus*'＋' + '}'
    if tail==True or mojiraw[-1]!='':
        lrctxt += cs_to_lrc_time(timekraw[-1])
    return lrctxt

if __name__=='__main__':
    lrcstr = r'''

Dialogue: 0,0:00:13.90,0:00:17.56,Default,knd,0,0,0,karaoke,{\k23}小|<こ{\k17}石|<い{\k22}#|し{\k21}を{\k17}高|<た{\k19}#|か{\k23}く{\k19}高|<た{\k11}#|か{\k22}く{\k4}　{\k22}積|<つ{\k20}み{\k19}上|<あ{\k19}げ{\k19}て{\k27}は{\k42}
Dialogue: 0,0:00:17.30,0:00:20.53,Default,knd,0,0,0,karaoke,{\k22}吹|<ふ{\k21}き{\k21}さ{\k10}ら{\k28}す{\k20}心|<こ{\k21}#|こ{\k11}#|ろ{\k24}は{\k4}　{\k22}夕|<ゆ{\k38}#|う{\k33}暮|<ぐ{\k38}れ{\k10}

'''
    for i in lrcstr.splitlines():
        if i.startswith('Dialogue:') or i.startswith('Comment:'):
            print(ass2lrc(i))
