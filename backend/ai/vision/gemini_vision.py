"""Gemini Vision 视觉分析实现。"""

from pathlib import Path

from PIL import Image

from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings


class GeminiVisionAnalyzer(BaseVisionAnalyzer):
    """Gemini Pro Vision 视觉分析器。"""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        import google.generativeai as genai

        self.api_key = api_key or settings.gemini_api_key or settings.vision_api_key
        self.model_name = model_name or "gemini-1.5-flash"
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name)

    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像。"""
        image_path = Path(image_path)
        image = Image.open(image_path)

        prompt = """
        请详细描述这个教学视频画面：
        1. 是否有图表？描述图表类型和内容
        2. 是否有架构图？描述结构和连接关系
        3. 是否有公式？提取完整的数学公式
        4. 是否有代码？提取代码及其语法
        5. 是否有重要文字？提取关键信息
        """

        response = self.client.generate_content([prompt, image])
        return response.text or ""
