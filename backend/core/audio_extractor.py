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
