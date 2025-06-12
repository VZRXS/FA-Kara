import argparse
import librosa
import numpy as np
import os
import re

import align
# import ass2lrc
import haruraw2norm as hn
import norm2ass
from norm2lrc import *

def non_silent_recog(audio_path):
    '识别非静音片段'
    y, sr = librosa.load(audio_path, sr=None)
    frame_length = int(sr * 1)  # 1s 帧
    hop_length = frame_length // 2  # 50% 重叠
    energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    threshold = np.percentile(energy, 90) * 0.1  # 取前10%能量的10%作为阈值
    non_silent_frames = energy > threshold
    times = librosa.frames_to_time(np.arange(len(energy)), sr=sr, hop_length=hop_length) # 转换为时间点
    
    # 合并连续片段
    segments = []
    start = None
    for i, (t, active) in enumerate(zip(times, non_silent_frames)):
        if active and start is None:
            start = t
        elif not active and start is not None:
            segments.append((start, t))
            start = None
    if start is not None:
        segments.append((start, times[-1]))

    return segments

if __name__=='__main__':
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser(description='可选参数')
    parser.add_argument('-t', '--tail_correct', type=int, default=1, help='1,2分别为两种尝试延长尾音的方式，否则不拖长')
    parser.add_argument('-p', '--path_io', default='', help='输入输出文件路径')
    args = parser.parse_args()

    tail_correct = args.tail_correct
    user_path = args.path_io
    real_io_path = os.path.normpath(user_path) if os.path.isabs(user_path) else os.path.normpath(os.path.join(script_dir, user_path))

    input_text_path = os.path.join(real_io_path, 'i.txt')
    input_audio_path = os.path.join(real_io_path, 'i.wav')

    print('Loading files...')
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

    non_silent_ranges = non_silent_recog(input_audio_path)

    print('Adding timelines...')
    alignment_results = align.align_audio_with_text(input_audio_path, alignment_tokens, non_silent_ranges)
    for i, result in enumerate(alignment_results):
        if i in token_to_index_map:
            original_index = token_to_index_map[i]
            result_list[original_index]['start'] = result['start']
            result_list[original_index]['end'] = result['end']

    main_output = process_main(result_list)
    ruby_output = process_ruby(result_list)
    content = f"{main_output}\n{ruby_output}"
    with open(os.path.join(real_io_path, 'o_ruby.lrc'), 'w', encoding='utf-8') as f:
        f.write(content)
    rlf_output = process_rlf(result_list)
    with open(os.path.join(real_io_path, 'o_rlf.lrc'), 'w', encoding='utf-8') as f:
        f.write(rlf_output)
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
    with open(os.path.join(real_io_path, 'o.ass'), 'w', encoding='utf-8') as f:
        f.write(ass_head+ass_output)
    # hrhlrc_output = ''
    # for i in ass_output.splitlines():
    #     hrhlrc_output += ass2lrc.ass2lrc(i, 0)+'\n'
    # with open(os.path.join(real_io_path, 'o_hrh.lrc'), 'w', encoding='utf-8') as f:
    #     f.write(hrhlrc_output)
    print('Success!')