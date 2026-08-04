"""视频链接导入服务：平台 URL 用 yt-dlp，直链视频文件用 httpx 直接下载。

- 平台 URL（B站/YouTube 等）：yt-dlp 解析+下载
- 直链视频（.mp4/.mkv 等，如内网 NAS/CDN）：httpx 流式下载，更可靠
"""

import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yt_dlp

from backend.config import settings

logger = logging.getLogger(__name__)

# 视频文件后缀：命中则视为直链，用 httpx 直接下载
VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".m4v", ".ts")


def _is_direct_video(url: str) -> bool:
    """URL 路径以视频后缀结尾（忽略 query）则视为直链视频文件。"""
    path = urlparse(url).path.lower()
    return path.endswith(VIDEO_EXTS)


class VideoImportService:
    """从 URL 下载视频。"""

    def download(self, url: str, course_id: int) -> tuple[str, str]:
        """下载视频到 upload_dir/{course_id}/，返回 (标题, 本地文件路径)。"""
        dest_dir = settings.resolve_path(settings.upload_dir) / str(course_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        if _is_direct_video(url):
            return self._download_direct(url, dest_dir)
        return self._download_ytdlp(url, dest_dir)

    def _download_direct(self, url: str, dest_dir: Path) -> tuple[str, str]:
        """直链视频文件：httpx 流式下载（适合内网 NAS/CDN 直链）。"""
        ext = "." + urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ".mp4"
        ext = ext[:6]  # 限制长度
        dest = dest_dir / f"video{ext}"
        try:
            # 内网/自签证书（如 NAS）不校验 SSL，避免 CERTIFICATE_VERIFY_FAILED
            with httpx.stream("GET", url, follow_redirects=True, verify=False, timeout=httpx.Timeout(300.0, connect=30.0)) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
        except Exception as e:
            logger.warning("直链视频下载失败 %s: %s", url, e)
            raise ValueError(f"视频下载失败：{e}")
        # 标题用文件名（去扩展名）
        name = urlparse(url).path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        title = name or "导入视频"
        return title, str(dest)

    def _download_ytdlp(self, url: str, dest_dir: Path) -> tuple[str, str]:
        """平台 URL：yt-dlp 解析并下载为 mp4。"""
        ydl_opts = {
            "outtmpl": str(dest_dir / "video.%(ext)s"),
            "format": "best[ext=mp4]/bestvideo*+bestaudio/best",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "http_headers": {"User-Agent": "Mozilla/5.0"},
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True) or {}
        except Exception as e:
            logger.warning("视频下载失败 %s: %s", url, e)
            raise ValueError(f"视频下载失败：{e}")

        title = info.get("title") or "导入视频"
        files = sorted(dest_dir.glob("video.*"))
        mp4 = [f for f in files if f.suffix.lower() == ".mp4"]
        chosen = (mp4 or files)[0] if (mp4 or files) else None
        if not chosen:
            raise ValueError("下载完成但未找到视频文件")
        return title, str(chosen)
