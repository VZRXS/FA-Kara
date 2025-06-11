# FA-Kara
一个基于RL输出歌词文本和人声音频的自动打轴工具，主要参考了[yohane](https://github.com/Japan7/yohane)、[Forced-Alignment-For-NicoKara](https://github.com/oHEILIo/Forced-Alignment-For-NicoKara/)。

建议使用此工具处理日语歌曲，但底层模型实际上不限语种。

## 使用说明
配置好Python环境后，准备歌词和音频文件（参考项目中的两个文件）：

### 1. 音频
- **格式及命名**: `i.wav`
- **要求**: 从歌曲中的分离出的人声，例如可以用UVR或MSST生成

### 2. 歌词
- **格式及命名**: `i.txt`
- **要求**: 需要有振假名注音，可使用RhythmicaLyrics，出力->春日向けテキスト

接下来运行脚本，以Windows系统为例：（这里不介绍环境变量和虚拟环境）
```
D:\Python\Python313\python.exe main.py
```

运行成功后，该目录下会生成三个文件：
- `o.ass`: 可在Aegisub中灵活编辑
- `o_rlf.lrc`: 可在RhythmicaLyrics中灵活编辑
- `o_ruby.lrc`: 可直接在NicoKaraMaker3使用，默认提前150ms

## 环境配置
参考`requirements.txt`，请根据实际情况自行配置。建议先参考[PyTorch官网](https://pytorch.org/get-started/locally/)的说明安装PyTorch，再安装其他库。

## 模型简介
主要使用了PyTorch的[MMS_FA](https://arxiv.org/abs/2305.13516)。

目前的效果尚不尽如人意，欢迎交流。