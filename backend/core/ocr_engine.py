"""OCR 引擎：基于 PaddleOCR 的文字识别。"""

from pathlib import Path

from paddleocr import PaddleOCR

from backend.config import settings


class OCREngine:
    """本地 OCR 引擎。"""

    def __init__(self, confidence_threshold: float | None = None) -> None:
        self.confidence_threshold = confidence_threshold or settings.ocr_confidence_threshold
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            use_gpu=False,
            show_log=False,
        )

    def extract_text(self, image_path: str | Path) -> list[dict]:
        """从图像中提取文字。

        返回包含文字、置信度、位置的列表。
        """
        image_path = Path(image_path)
        result = self.ocr.ocr(str(image_path), cls=True)

        if not result or not result[0]:
            return []

        texts = []
        for line in result[0]:
            bbox = line[0]
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]

            if confidence > self.confidence_threshold:
                texts.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox,
                })

        return texts

    def extract_text_string(self, image_path: str | Path) -> str:
        """提取文字并返回拼接字符串。"""
        texts = self.extract_text(image_path)
        return "\n".join([t["text"] for t in texts])
