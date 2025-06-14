# FA-Kara
一个基于RL输出歌词文本和人声音频的自动打轴工具，主要参考了[yohane](https://github.com/Japan7/yohane)、[Forced-Alignment-For-NicoKara](https://github.com/oHEILIo/Forced-Alignment-For-NicoKara/)。

建议使用此工具处理日语歌曲，但底层模型实际上不限语种。

## 使用说明
配置好Python环境后，准备以下两个文件（可参考示例）：
#### 1. 音频
- **格式及命名**: `i.wav`
- **要求**: 从歌曲中的分离出的人声，例如可以用UVR或MSST生成

#### 2. 歌词
- **格式及命名**: `i.txt`
- **要求**: 需要有振假名注音，可使用RhythmicaLyrics，出力->春日向けテキスト

将音频、歌词和各个`.py`文件放在同一目录，运行指令：
``` shell
python main.py
```

若运行成功，该目录下会生成三个文件：
- `o.ass`: 可在Aegisub中灵活编辑
- `o_rlf.lrc`: 可在RhythmicaLyrics中灵活编辑
- `o_ruby.lrc`: 可直接在NicoKaraMaker3使用，默认提前150ms

### 可选参数
运行指令时还可以添加参数，例如一首歌曲的语速偏快，你可以尝试如下指令：
``` shell
python main.py -v 0.5
```
此时，模型将以0.5倍速处理音频（你无需调整时间轴），可能有助于提升推理效果。

更多选项请用`-h`查看。

## 环境配置
参考`requirements.txt`，请根据实际情况调整。

如果你从未接触过Python，可按照如下步骤配置环境：
1. 安装[Python](https://www.python.org/)（推荐版本3.13），并配置好环境变量；
2. 根据操作系统与GPU情况，安装对应的[PyTorch](https://pytorch.org/get-started/locally/)；
3. 再用pip安装其他库，如Janome, librosa, pykakasi等。

## 模型简介
主要使用了PyTorch的[MMS_FA](https://arxiv.org/abs/2305.13516)。

目前的效果尚不尽如人意，欢迎交流。