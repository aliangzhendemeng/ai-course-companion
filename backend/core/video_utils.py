"""视频处理工具函数。"""

import subprocess
from pathlib import Path


def get_video_duration(video_path: str | Path) -> float:
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


def get_video_info(video_path: str | Path) -> dict:
    """获取视频基本信息。"""
    video_path = Path(video_path)
    duration = get_video_duration(video_path)
    return {
        "path": str(video_path),
        "duration": duration,
    }
