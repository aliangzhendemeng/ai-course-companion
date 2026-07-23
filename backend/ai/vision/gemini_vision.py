"""Gemini Vision 视觉分析实现（预留）。"""

from pathlib import Path

from backend.ai.vision.base import BaseVisionAnalyzer


class GeminiVisionAnalyzer(BaseVisionAnalyzer):
    """Gemini Pro Vision 视觉分析器（预留实现）。"""

    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像。"""
        raise NotImplementedError("Gemini Vision 尚未实现")
