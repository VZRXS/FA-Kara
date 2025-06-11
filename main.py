import os
import re
import align
import ass2lrc
import haruraw2norm as hn
import norm2ass

tail_correct = 1 # 1,2分别为两种尝试拖长尾音的方式，0则不拖长

def parse_time_to_hundredths(time_str):
    match = re.match(r'\[(\d{2}):(\d{2}):(\d{2})\]', time_str)
    minutes, seconds, hundredths = int(match.group(1)), int(match.group(2)), int(match.group(3))
    return minutes * 6000 + seconds * 100 + hundredths

def format_hundredths_to_time_str(total_hundredths):
    minutes = total_hundredths // 6000
    remaining = total_hundredths % 6000
    seconds = remaining // 100
    hundredths = remaining % 100
    return f"[{minutes:02d}:{seconds:02d}:{hundredths:02d}]"

def process_main(result_list):
    result = []
    current_line = ""
    last_end = None
    last_end_time = None

    i = 0
    while i < len(result_list):
        item = result_list[i]

        if ('start' in item and current_line == "" and item['type'] in [1, 2, 3]):
            current_start_time = parse_time_to_hundredths(item['start'])

            if ((last_end_time and current_start_time - last_end_time > 1000) or
                (last_end_time is None and current_start_time > 500)):
                marker_time = max(0, current_start_time - 300)
                marker_time_str = format_hundredths_to_time_str(marker_time)
                current_line += f"{marker_time_str}⬤⬤⬤"

        if item['type'] in [1, 3] or item['type'] == 0 and item['orig']!='\n' and 'start' in item:
            current_line += f"{item['start']}{item['orig']}"
            last_end = item['end']
        elif item['type'] == 2:
            if item['orig'] != '':
                current_line += f"{item['start']}{item['orig']}"
            last_end = item['end']
        elif item['type'] == 0 and 'start' not in item:
            if last_end:
                current_line += last_end+item['orig']
                result.append(current_line)
                last_end_time = parse_time_to_hundredths(last_end)
                current_line = ""
                last_end = None
            else:
                current_line += item['orig']
        elif item['type'] == 0 and item['orig']=='\n':
            current_line += item['start']+item['orig']
            result.append(current_line)
            last_end_time = parse_time_to_hundredths(last_end)
            current_line = ""
            last_end = None
            
        i += 1

    if current_line and last_end:
        current_line += last_end
        result.append(current_line)
    if item['orig']!='\n':
        result.append("\n")
    result.append("\n@Offset=-150")
    return "".join(result)

def process_ruby(result_list):
    ruby_annotations = []
    i = 0

    while i < len(result_list):
        item = result_list[i]

        if item['type'] == 2 and item['orig'] != '':
            ruby1 = item['orig']
            ruby2 = item['ruby']
            ruby3 = item['start']
            ruby4 = ''

            first_start_time = parse_time_to_hundredths(item['start'])

            j = i + 1
            while j < len(result_list) and result_list[j]['type'] == 2 and result_list[j]['orig'] == '':
                current_item = result_list[j]
                current_start_time = parse_time_to_hundredths(current_item['start'])
                time_diff = current_start_time - first_start_time
                time_diff_str = format_hundredths_to_time_str(time_diff)
                ruby2 += f"{time_diff_str}{current_item['ruby']}"
                j += 1

            for k in range(len(ruby_annotations) - 1, -1, -1):
                if ruby_annotations[k]['ruby1'] == ruby1:
                    ruby_annotations[k]['ruby4'] = item['start']
                    break

            ruby_annotations.append({'ruby1': ruby1, 'ruby2': ruby2, 'ruby3': ruby3, 'ruby4': ruby4})
            i = j
        else:
            i += 1

    result = []
    for idx, annotation in enumerate(ruby_annotations, 1):
        result.append(f"@Ruby{idx}={annotation['ruby1']},{annotation['ruby2']},{annotation['ruby3']},{annotation['ruby4']}")

    return "\n".join(result)

if __name__=='__main__':
    input_text_path = 'i.txt'
    input_audio_path = 'i.wav'

    result_list = []
    with open(input_text_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.strip():
                result_list.extend(hn.process_haruhi_line(line))

    if tail_correct == 1:
        for i in range(len(result_list)):
            if result_list[i]['type']==0:
                try:
                    if len(result_list[i-1]['pron'])>1 and result_list[i-1]['type']!=0:
                        pre_vowel = result_list[i-1]['pron'][-1]
                        post_consonant = ''
                        if i < len(result_list)-1:
                            post_i = i + 1
                            while post_i < len(result_list):
                                if 'pron' in result_list[post_i] and len(result_list[post_i]['pron'])>=1:
                                    post_consonant = result_list[post_i]['pron'][0]
                                    break
                                else:
                                    post_i += 1
                        if pre_vowel!=post_consonant and post_consonant not in ('a', 'e', 'i', 'o', 'u'):
                            result_list[i]['pron'] = pre_vowel + 'h'
                except:
                    continue
    elif tail_correct == 2:
        for i in range(len(result_list)):
            if result_list[i]['type']==0:
                try: # 合理利用baseline尾音特性
                    if len(result_list[i-1]['pron'])>=1 and result_list[i-1]['type']!=0:
                        result_list[i]['pron'] = result_list[i-1]['pron'][-1] + 'h'
                except:
                    continue

    alignment_tokens = []
    token_to_index_map = {}
    for i, item in enumerate(result_list):
        if 'pron' in item and item['pron']:
            alignment_tokens.append(item['pron'])
            token_to_index_map[len(alignment_tokens) - 1] = i

    for item in alignment_tokens:
        if hn.is_english(item):
            continue
        else:
            print(f"alignment_tokens可能包含错误数据{item}")

    print('Adding timelines...')
    alignment_results = align.align_audio_with_text(input_audio_path, alignment_tokens)
    for i, result in enumerate(alignment_results):
        if i in token_to_index_map:
            original_index = token_to_index_map[i]
            result_list[original_index]['start'] = result['start']
            result_list[original_index]['end'] = result['end']

    main_output = process_main(result_list)
    ruby_output = process_ruby(result_list)
    content = f"{main_output}\n{ruby_output}"
    with open('o_ruby.lrc', 'w', encoding='utf-8') as f:
        f.write(content)
    ass_output = norm2ass.process_norm2assV2(result_list)
    ass_head = '''[Script Info]
ScriptType: v4.00+
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Source Han Serif,71,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1.99999,1.99999,2,11,11,101,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    with open('o.ass', 'w', encoding='utf-8') as f:
        f.write(ass_head+ass_output)
    hrhlrc_output = ''
    for i in ass_output.splitlines():
        hrhlrc_output += ass2lrc.ass2lrc(i, 0)+'\n'
    with open('o_hrh.lrc', 'w', encoding='utf-8') as f:
        f.write(hrhlrc_output)
    print('Success!')