"""Claude Vision 视觉分析实现。"""

import base64
from pathlib import Path

from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings


class ClaudeVisionAnalyzer(BaseVisionAnalyzer):
    """Claude Vision 视觉分析器。"""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
    ) -> None:
        import anthropic

        self.api_key = api_key or settings.claude_api_key or settings.vision_api_key
        self.model_name = model_name or "claude-3-5-sonnet-20241022"
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像。"""
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

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=500,
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
        )
        content = response.content
        if content and len(content) > 0:
            return content[0].text
        return ""
