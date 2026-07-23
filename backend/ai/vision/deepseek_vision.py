"""DeepSeek-VL 视觉分析实现。"""

import base64
from pathlib import Path

from openai import OpenAI

from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings
from backend.core.ocr_engine import OCREngine


class DeepSeekVisionAnalyzer(BaseVisionAnalyzer):
    """DeepSeek-VL 视觉分析器。"""

    def __init__(self, api_key: str | None = None, ocr_engine: OCREngine | None = None) -> None:
        self.api_key = api_key or settings.deepseek_api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
        self.model = "deepseek-vl-chat"
        self.ocr_engine = ocr_engine or OCREngine()

    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像。

        API 不可用时降级为纯 OCR 输出。
        """
        try:
            return self._call_vl(image_path)
        except Exception:
            return self._fallback_ocr(image_path)

    def _call_vl(self, image_path: str | Path) -> str:
        """调用 DeepSeek-VL API。"""
        image_path = Path(image_path)
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        prompt = """
        请详细描述这个教学视频画面：
        1. 是否有图表？描述图表类型和内容
        2. 是否有架构图？描述结构和连接关系
        3. 是否有公式？提取完整的数学公式
        4. 是否有代码？提取代码及其语法
        5. 是否有重要文字？提取关键信息
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        return response.choices[0].message.content or ""

    def _fallback_ocr(self, image_path: str | Path) -> str:
        """降级为 OCR 文字。"""
        ocr_text = self.ocr_engine.extract_text_string(image_path)
        if not ocr_text.strip():
            return "（该画面未识别到文字，且视觉模型当前不可用）"
        return f"画面中的文字内容：\n{ocr_text}"
