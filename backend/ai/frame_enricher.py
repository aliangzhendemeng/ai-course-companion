"""帧增强器：OCR + 复杂度判定 + 并发视觉理解。"""

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from backend.ai.frame_complexity import FrameComplexityAnalyzer
from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings
from backend.core.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class FrameEnricher:
    """对关键帧执行 OCR 和可选的视觉理解。"""

    def __init__(
        self,
        ocr_engine: OCREngine | None = None,
        vision_analyzer: BaseVisionAnalyzer | None = None,
        complexity_analyzer: FrameComplexityAnalyzer | None = None,
        max_workers: int | None = None,
    ) -> None:
        self.ocr_engine = ocr_engine or OCREngine()
        self.vision_analyzer = vision_analyzer
        self.complexity_analyzer = complexity_analyzer or FrameComplexityAnalyzer()
        self.max_workers = max_workers or settings.vision_max_workers

    def _get_vision_analyzer(self) -> BaseVisionAnalyzer:
        """延迟初始化视觉分析器。"""
        if self.vision_analyzer is None:
            from backend.ai.factory import create_vision_analyzer

            logger.info("初始化视觉分析器...")
            self.vision_analyzer = create_vision_analyzer()
            logger.info("视觉分析器初始化完成")
        return self.vision_analyzer

    def _ocr_frame(self, frame_info: dict) -> str:
        """对单帧做 OCR。"""
        frame_path = frame_info["path"]
        try:
            return self.ocr_engine.extract_text_string(frame_path)
        except Exception as e:
            logger.exception("帧 OCR 失败: %s", frame_path)
            return ""

    def _call_vision_safe(self, frame_path: str | Path) -> tuple[str, str | None]:
        """安全调用视觉模型，返回 (desc, error_message)。"""
        try:
            desc = self._get_vision_analyzer().understand_frame(frame_path)
            return desc, None
        except Exception as e:
            logger.warning("视觉模型调用失败: %s: %s", frame_path, e)
            return "", str(e)

    def enrich(
        self,
        course_id: int,
        frames: list[dict],
    ) -> list[dict]:
        """对帧列表执行 OCR 和智能视觉理解。

        返回 [{"id": ..., "timestamp": ..., "ocr_text": ..., "vision_desc": ...}, ...]，
        顺序与输入一致。
        """
        if not frames:
            return []

        # 第一步：顺序 OCR（OCR 本身较重，不在 ThreadPool 中并行）
        ocr_texts = [self._ocr_frame(frame_info) for frame_info in frames]

        # 第二步：判定哪些帧需要视觉理解
        vision_tasks = []
        for i, (frame_info, ocr_text) in enumerate(zip(frames, ocr_texts)):
            if self.complexity_analyzer.is_complex(ocr_text):
                vision_tasks.append((i, frame_info["path"]))

        # 第三步：对复杂帧并行调用视觉模型
        vision_descs: dict[int, tuple[str, str | None]] = {}
        if vision_tasks:
            paths = [path for _, path in vision_tasks]
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(executor.map(self._call_vision_safe, paths))
            for (i, _), (desc, error) in zip(vision_tasks, results):
                vision_descs[i] = (desc, error)

        # 第四步：组装结果
        enriched = []
        vision_task_set = {idx for idx, _ in vision_tasks}
        for i, frame_info in enumerate(frames):
            ocr_text = ocr_texts[i]
            vision_entry = vision_descs.get(i, ("", None))
            vision_desc, vision_error = vision_entry if isinstance(vision_entry, tuple) else (vision_entry, None)

            # 如果视觉模型失败，补充错误说明与 OCR 结果
            if i in vision_task_set and vision_error:
                vision_desc = f"（视觉模型调用失败：{vision_error}，仅 OCR 结果：\n{ocr_text}）"
            elif i in vision_task_set and not vision_desc.strip():
                vision_desc = f"（视觉模型不可用，仅 OCR 结果：\n{ocr_text}）"

            enriched.append({
                "id": frame_info.get("id"),
                "timestamp": frame_info["timestamp"],
                "ocr_text": ocr_text,
                "vision_desc": vision_desc,
            })

        return enriched
