"""音频提取模块：视频 → WAV。"""

import subprocess
from pathlib import Path


class AudioExtractor:
    """使用 ffmpeg 从视频中提取音频。"""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate

    def extract(self, video_path: str | Path, output_path: str | Path) -> Path:
        """从视频中提取单声道 WAV 音频。"""
        video_path = Path(video_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "ffmpeg",
            "-y",  # 覆盖输出文件
            "-i", str(video_path),
            "-vn",  # 不要视频
            "-acodec", "pcm_s16le",
            "-ac", "1",  # 单声道
            "-ar", str(self.sample_rate),
            str(output_path),
        ]

        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return output_path

    def get_duration(self, video_path: str | Path) -> float:
        """获取视频时长（秒）。"""
        video_path = Path(video_path)
        command = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return float(result.stdout.strip())

    def get_mean_volume(self, audio_path: str | Path) -> float:
        """检测音频平均音量（dB）。用于判断视频是否包含可用语音。

        正常语音通常在 -15 ~ -30 dB；低于 -40 dB 视为近乎静音。
        """
        audio_path = Path(audio_path)
        command = [
            "ffmpeg",
            "-i", str(audio_path),
            "-af", "volumedetect",
            "-vn",
            "-f", "null",
            "-",
        ]
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # ffmpeg 把 volumedetect 结果输出到 stderr，行格式如：
        # [Parsed_volumedetect_0 @ 0x...] mean_volume: -48.1 dB
        for line in result.stderr.splitlines():
            if "mean_volume:" in line:
                try:
                    return float(line.rsplit("mean_volume:", 1)[1].strip().replace("dB", "").strip())
                except (ValueError, IndexError):
                    break
        return 0.0

