import re

def int2asstime(cs: int) -> str:
    '厘秒整数转换为.ass时轴信息'
    hours = cs // 360000
    cs %= 360000
    minutes = cs // 6000
    cs %= 6000
    seconds = cs // 100
    cs %= 100
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"

def parse_time_to_hundredths(time_str):
    match = re.match(r'\[(\d{2}):(\d{2}):(\d{2})\]', time_str)
    minutes, seconds, hundredths = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return minutes * 6000 + seconds * 100 + hundredths

def process_norm2assV1(struc, pretime = 20, posttime = 20):
    '模型输出的实际时值，不再维护'
    result = ''
    for i in range(len(struc)):
        if not result or result[-1]=='\n':
            asstxt = ''
            nowtime = starttime = parse_time_to_hundredths([itemd for itemd in struc[i:] if itemd['type'] != 0][0]['start']) - pretime
        item = struc[i]
        if item['type'] == 0 and item['orig'] == '\n':
            try:
                nowtime = parse_time_to_hundredths(item['start'])
            except:
                pass
            finally:
                endtime = nowtime + posttime
                asstxt = 'Dialogue: 0,'+int2asstime(starttime)+','+int2asstime(endtime)+r',Default,,0,0,0,karaoke,'+asstxt+r'{\k'+str(posttime)+'}'
                result += asstxt+'\n'
        elif 'start' not in item:
            asstxt += item['orig']
        else:
            item_kbefore = parse_time_to_hundredths(item['start']) - nowtime
            if item_kbefore!=0:
                asstxt += r'{\k'+str(item_kbefore)+'}'
            item_kdur = parse_time_to_hundredths(item['end']) - parse_time_to_hundredths(item['start'])
            asstxt += r'{\k'+str(item_kdur)+'}'
            if item['type'] == 2:
                asstxt += ('#|' if item['orig']=='' else item['orig'] + '|<') + item['ruby']
            else:
                asstxt += item['orig']
            nowtime = parse_time_to_hundredths(item['end'])
    return result

def process_norm2assV2(struc, pretime = 20, posttime = 20):
    '仿NicokaraMaker.lrc时值'
    result = ''
    starttime = nowtime = None
    asstxt = r'{\k'+str(pretime)+'}'
    i = 0
    while i < len(struc):
        item = struc[i]
        if not starttime:
            try:
                starttime = parse_time_to_hundredths(item['start']) - pretime
                nowtime = parse_time_to_hundredths(item['start'])
            except:
                asstxt += item['orig']
                i += 1
                continue
        if item['type'] == 0 and item['orig'] == '\n':
            try:
                nowtime = parse_time_to_hundredths(item['start'])
            except:
                pass
            finally:
                endtime = nowtime + posttime
                result += 'Dialogue: 0,'+int2asstime(starttime)+','+int2asstime(endtime)+r',Default,,0,0,0,karaoke,'+asstxt+r'{\k'+str(posttime)+'}'+'\n'
                starttime = nowtime = None
                asstxt = r'{\k'+str(pretime)+'}'
        elif item['type'] == 0 and 'start' not in item:
            try:
                item_kdur = parse_time_to_hundredths(struc[i+1]['start']) - nowtime
                asstxt += r'{\k'+str(item_kdur)+'}'
                nowtime = parse_time_to_hundredths(struc[i+1]['start'])
            except:
                pass
            finally:
                asstxt += item['orig']
        else:
            if 'start' in struc[i+1]:
                item_kdur = parse_time_to_hundredths(struc[i+1]['start']) - parse_time_to_hundredths(item['start'])
                nowtime = parse_time_to_hundredths(struc[i+1]['start'])
            else:
                item_kdur = parse_time_to_hundredths(item['end']) - parse_time_to_hundredths(item['start'])
                nowtime = parse_time_to_hundredths(item['end'])
            asstxt += r'{\k'+str(item_kdur)+'}'
            if item['type'] == 2:
                asstxt += ('#|' if item['orig']=='' else item['orig'] + '|<') + item['ruby']
            else:
                asstxt += item['orig']
        i += 1
    return result


def norm2sturctured(normed_items, process_duet=False):
    # NOTE: type 0: non-char element, type 3: kana/en char, type 2: kanji+kana
    result_list = []
    structured = []
    is_start_of_stanza = False  # FIXME: duet feature, NOT IMPLEMENTED
    leading_text = ''  # FIXME: leading text w/o timing, NOT IMPLEMENTED
    element = {}
    for i, item in enumerate(normed_items):
        if item['type'] == 2:
            if item['orig'] == '':
                element['furigana'].append({'text':item['ruby'], 'start_cs':parse_time_to_hundredths(item['start']), 'end_cs':parse_time_to_hundredths(item['end'])})
                if i + 1 < len(normed_items) and normed_items[i + 1]['orig'] != '' or i + 1 == len(normed_items):
                    element['end_cs'] = parse_time_to_hundredths(normed_items[i]['end'])
                    structured.append(element)
                    assert element['start_cs'] < element['end_cs']
                    element = {}
            else:
                element['type'] = 'kanji'
                element['char'] = item['orig']
                element['start_cs'] = parse_time_to_hundredths(item['start'])
                element['furigana'] = [{'text':item['ruby'], 'start_cs':parse_time_to_hundredths(item['start']), 'end_cs':parse_time_to_hundredths(item['end'])}]
                if i + 1 < len(normed_items) - 1 and normed_items[i + 1]['orig'] != '' or i + 1 == len(normed_items):
                    element['end_cs'] = parse_time_to_hundredths(normed_items[i]['end'])
                    structured.append(element)
                    assert element['start_cs'] < element['end_cs']
                    element = {}
        
        elif item['type'] == 3:
            structured.append({'type': 'simple', 'char': item['orig'], 'start_cs': parse_time_to_hundredths(item['start']), 'end_cs': parse_time_to_hundredths(item['end'])})
        
        elif item['type'] == 0:
            if item['orig'] == '\n':
                result_list.append({'leading_text': leading_text, 'is_start_of_stanza': is_start_of_stanza, 'structured': structured})
                structured = []
                element = {}
            else:
                if structured == []:
                    # begining of a new line
                    dummy_timestamp = -1
                    while i < len(normed_items) and dummy_timestamp == -1:
                        # look ahead to find next timestamp
                        try:
                            dummy_timestamp = normed_items[i]['start']
                        except:                        
                            i += 1
                    structured.append({'type': 'simple', 'char': item['orig'], 'start_cs': parse_time_to_hundredths(dummy_timestamp), 'end_cs': parse_time_to_hundredths(dummy_timestamp)})
                else:
                    # middle of a line
                    if structured[-1]['type'] == 'simple':
                        # SCHEME1: merge to prev char
                        structured[-1]['char'] += item['orig']
                    else:
                        # SCHEME2: append as a new char if prev char is a kanji
                        structured.append({'type': 'simple', 'char':item['orig'], 'start_cs': structured[-1]['end_cs'], 'end_cs': structured[-1]['end_cs']})
                assert 'end' not in item.keys()
        else:
            raise Exception(f"Unexpected item type: {item['type']}")
            
    return result_list

def norm2ass_custom(lyric_lines, pretime=200, posttime=0, upper_line_indices=[-1], enable_duet=False, ass_header_path='ass_header.txt'):
    """Convert output to ASS format.
    `upper_line_indices`: A list of line indices that would be set as Upper style, `[-1]` to disable.
    `enable_duet`: Two lines after a `\\n` will appear together if set to `True`.
    """
    lyric_lines = norm2sturctured(lyric_lines, enable_duet)
    event_lines = []
    dialogue_format = "Dialogue: 0,{start},{end},{style},,0,0,0,karaoke,{text}"
    style_is_left = True
    i = 0
    pre_ktime_str = '{\\k0}'
    post_ktime_str = '{\\k0}'
    while i < len(lyric_lines):
        line_number = i + 1
        # is_duet =  enable_duet and lyric_lines['orig'] == '\n' and (i + 1 < len(lyric_lines))
        is_duet = lyric_lines[i]['is_start_of_stanza'] and (i + 1 < len(lyric_lines))

        if is_duet:
            is_duet = False
            line1_info = lyric_lines[i]
            line2_info = lyric_lines[i+1]
            structured_line1 = line1_info.get('structured')
            structured_line2 = line2_info.get('structured')

            if structured_line1 and structured_line2:
                start1_cs = structured_line1[0]['start_cs']
                end1_cs = structured_line1[-1]['end_cs']
                style1 = 'Upper' if line_number in upper_line_indices else 'Left'
                new_start1_cs = max(start1_cs - pretime, 0)
                new_end1_cs = end1_cs + posttime
                pre_ktime_str = f'{{\\k{(start1_cs - new_start1_cs)}}}'
                post_ktime_str = f'{{\\k{(new_end1_cs - end1_cs)}}}'
                text1 = pre_ktime_str + build_dialogue_text(line1_info['leading_text'], structured_line1) + post_ktime_str
                event_lines.append(dialogue_format.format(start=int2asstime(new_start1_cs), end=int2asstime(new_end1_cs), style=style1, text=text1))

                orig_start2_cs = structured_line2[0]['start_cs']
                new_start2_cs = new_start1_cs
                end2_cs = structured_line2[-1]['end_cs']
                style2 = 'Upper' if (line_number + 1) in upper_line_indices else 'Right'
                
                calculated_delay_cs = orig_start2_cs - new_start1_cs
                delay_k_tag = f"{{\\k{calculated_delay_cs}}}" if calculated_delay_cs > 0 else ""
                
                new_end2_cs = end2_cs + posttime
                post_ktime_str = f'{{\\k{(new_end2_cs - end2_cs)}}}'
                text2 = pre_ktime_str + delay_k_tag + build_dialogue_text(line2_info['leading_text'], structured_line2) + post_ktime_str
                event_lines.append(dialogue_format.format(start=int2asstime(new_start2_cs), end=int2asstime(end2_cs), style=style2, text=text2))
            
            i += 2
            style_is_left = True
        else:
            structured_line = lyric_lines[i].get('structured')
            if structured_line:
                start_cs = structured_line[0]['start_cs']
                end_cs = structured_line[-1]['end_cs']

                if line_number in upper_line_indices:
                    style = 'Upper'
                else:
                    style = 'Left' if style_is_left else 'Right'
                    style_is_left = not style_is_left

                new_start_cs = max(start_cs - pretime, 0)
                new_end_cs = end_cs + posttime
                pre_ktime_str = f'{{\\k{(start_cs - new_start_cs)}}}'
                post_ktime_str = f'{{\\k{(new_end_cs - end_cs)}}}'
                text = pre_ktime_str + build_dialogue_text(lyric_lines[i]['leading_text'], structured_line) + post_ktime_str
                event_lines.append(dialogue_format.format(start=int2asstime(new_start_cs), end=int2asstime(new_end_cs), style=style, text=text))
            
            i += 1
            
    try:
        with open(ass_header_path, 'r') as f:
            ass_header = f.read()
    except FileNotFoundError:
        print(f"Error: {ass_header_path} not found.")
            
    final_ass_content = ass_header + "\n" + "\n".join(event_lines)
    return final_ass_content



def build_dialogue_text(leading_text, structured_line):
    """Builds the karaoke text for a single line from its structured elements."""
    line_ass_text_parts = [leading_text] # Start with any untimed text
    for i, element in enumerate(structured_line):
        if element['type'] == 'simple':
            if i + 1 < len(structured_line):
                total_duration_cs = (structured_line[i + 1]['start_cs'] - element['start_cs'])
                # TODO: handle leading symbol
                if total_duration_cs == 0:
                    if structured_line[i + 1]['type'] == 'simple':
                        shift_time_cs = (structured_line[i + 1]['end_cs'] - element['start_cs']) // 2
                        structured_line[i + 1]['start_cs'] += shift_time_cs
                        element['end_cs'] += shift_time_cs
                    elif structured_line[i + 1]['type'] == 'kanji':
                        shift_time_cs = (structured_line[i + 1]['furigana'][0]['end_cs'] - element['start_cs']) // 2
                        structured_line[i + 1]['furigana'][0]['start_cs'] += shift_time_cs
                        element['end_cs'] += shift_time_cs
                    else:
                        raise Exception(f"Unexpected element type: {structured_line[i + 1]['type']}")
                    total_duration_cs += shift_time_cs
            else:
                total_duration_cs = (element['end_cs'] - element['start_cs'])
                
            # total_duration_cs = (element['end_cs'] - element['start_cs'])
            # total_duration_cs = max(0, total_duration_cs)
            if total_duration_cs < 0:
                print(f"WARNING: Negative duration for element: {element}")
            line_ass_text_parts.append(f"{{\\k{total_duration_cs}}}{element['char']}")
        
        elif element['type'] == 'kanji':
            text_part = ""
            num_syls = len(element['furigana'])
            
            if num_syls == 1:
                if i + 1 < len(structured_line):
                    total_duration_cs = (structured_line[i + 1]['start_cs'] - element['start_cs'])
                else:
                    total_duration_cs = (element['end_cs'] - element['start_cs'])
                if total_duration_cs < 0:
                    print(f"WARNING: Negative duration for element: {element}")
                text_part = (f"{{\\k{total_duration_cs}}}{element['char']}"
                             f"|<{element['furigana'][0]['text']}")
            else:
                # first_furi_duration_cs = (element['furigana'][0]['end_cs'] - element['furigana'][0]['start_cs'])
                first_furi_duration_cs = (element['furigana'][1]['start_cs'] - element['furigana'][0]['start_cs'])
                
                if first_furi_duration_cs < 0:
                    print(f"WARNING: Negative duration for element: {element}")
                text_part = (f"{{\\k{first_furi_duration_cs}}}{element['char']}"
                             f"|<{element['furigana'][0]['text']}")
                
                for j, furi_syl in enumerate(element['furigana'][1:]):
                    if j + 2 < num_syls:
                        duration_cs = (element['furigana'][j + 2]['start_cs'] - furi_syl['start_cs'])
                    elif i + 1 < len(structured_line):
                        duration_cs = (structured_line[i + 1]['start_cs'] - furi_syl['start_cs'])
                    else:
                        duration_cs = (furi_syl['end_cs'] - furi_syl['start_cs'])
                    if duration_cs < 0:
                        print(f"WARNING: Negative duration for element: {element}")
                    text_part += (f"{{\\k{duration_cs}}}#|{furi_syl['text']}")
            line_ass_text_parts.append(text_part)
    return "".join(line_ass_text_parts)


if __name__=='__main__':
    input_struc = [{'orig': '歌',
  'type': 2,
  'ruby': 'う',
  'pron': 'u',
  'start': '[00:01:38]',
  'end': '[00:01:40]'},
 {'orig': '',
  'type': 2,
  'ruby': 'た',
  'pron': 'ta',
  'start': '[00:01:54]',
  'end': '[00:01:64]'},
 {'orig': 'え',
  'type': 3,
  'pron': 'e',
  'start': '[00:03:12]',
  'end': '[00:03:14]'},
 {'orig': '\u3000', 'type': 0},
 {'orig': '踊',
  'type': 2,
  'ruby': 'お',
  'pron': 'o',
  'start': '[00:03:35]',
  'end': '[00:03:37]'},
 {'orig': '',
  'type': 2,
  'ruby': 'ど',
  'pron': 'do',
  'start': '[00:04:13]',
  'end': '[00:04:24]'},
 {'orig': 'れ',
  'type': 3,
  'pron': 're',
  'start': '[00:10:24]',
  'end': '[00:10:54]'},
 {'orig': '\n', 'type': 0},
 {'orig': '祈',
  'type': 2,
  'ruby': 'い',
  'pron': 'i',
  'start': '[00:11:17]',
  'end': '[00:11:20]'},
 {'orig': '',
  'type': 2,
  'ruby': 'の',
  'pron': 'no',
  'start': '[00:11:33]',
  'end': '[00:11:40]'},
 {'orig': 'れ',
  'type': 3,
  'pron': 're',
  'start': '[00:11:75]',
  'end': '[00:11:85]'},
 {'orig': '\u3000', 'type': 0},
 {'orig': '届',
  'type': 2,
  'ruby': 'と',
  'pron': 'to',
  'start': '[00:11:96]',
  'end': '[00:12:06]'},
 {'orig': '',
  'type': 2,
  'ruby': 'ど',
  'pron': 'do',
  'start': '[00:12:17]',
  'end': '[00:12:72]'},
 {'orig': 'け',
  'type': 3,
  'pron': 'ke',
  'start': '[00:12:83]',
  'end': '[00:12:93]'},
 {'orig': '\n', 'type': 0}]
    print(process_norm2assV2(input_struc))