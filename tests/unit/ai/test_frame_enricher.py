"""帧增强器测试。"""

from pathlib import Path

import pytest

from backend.ai.frame_enricher import FrameEnricher


class FakeOCREngine:
    """伪 OCR 引擎：根据文件名返回不同 OCR 文本。"""

    def __init__(self, text_by_path: dict | None = None) -> None:
        self.text_by_path = text_by_path or {}

    def extract_text_string(self, image_path: str | Path) -> str:
        path = str(image_path)
        return self.text_by_path.get(path, "默认文字")


class FakeVisionAnalyzer:
    """伪视觉分析器：记录调用次数，按路径返回描述。"""

    def __init__(self, desc_by_path: dict | None = None) -> None:
        self.desc_by_path = desc_by_path or {}
        self.calls = []

    def understand_frame(self, image_path: str | Path) -> str:
        path = str(image_path)
        self.calls.append(path)
        if path in self.desc_by_path:
            return self.desc_by_path[path]
        return "fake vision desc"


def test_simple_frame_does_not_call_vision(tmp_path):
    """简单帧不应调用视觉 API。"""
    frame1 = tmp_path / "frame1.jpg"
    frame1.write_bytes(b"frame1")

    ocr = FakeOCREngine({str(frame1): "这是一段普通的课程讲解文字，内容比较长。"})
    vision = FakeVisionAnalyzer()

    enricher = FrameEnricher(ocr_engine=ocr, vision_analyzer=vision, max_workers=2)
    result = enricher.enrich(
        course_id=1,
        frames=[{"timestamp": 0.0, "path": str(frame1)}],
    )

    assert len(result) == 1
    assert result[0]["ocr_text"] == "这是一段普通的课程讲解文字，内容比较长。"
    assert result[0]["vision_desc"] == ""
    assert len(vision.calls) == 0


def test_complex_frame_calls_vision(tmp_path):
    """复杂帧应调用视觉 API。"""
    frame1 = tmp_path / "frame1.jpg"
    frame1.write_bytes(b"frame1")

    ocr = FakeOCREngine({str(frame1): "def hello():"})
    vision = FakeVisionAnalyzer({str(frame1): "代码画面"})

    enricher = FrameEnricher(ocr_engine=ocr, vision_analyzer=vision, max_workers=2)
    result = enricher.enrich(
        course_id=1,
        frames=[{"timestamp": 5.0, "path": str(frame1)}],
    )

    assert len(result) == 1
    assert result[0]["ocr_text"] == "def hello():"
    assert result[0]["vision_desc"] == "代码画面"
    assert len(vision.calls) == 1


def test_vision_failure_fallback_to_ocr(tmp_path):
    """视觉 API 失败时降级为 OCR。"""
    frame1 = tmp_path / "frame1.jpg"
    frame1.write_bytes(b"frame1")

    ocr = FakeOCREngine({str(frame1): "公式: E=mc^2"})
    vision = FakeVisionAnalyzer()

    def failing_vision(image_path):
        raise RuntimeError("API 失败")

    vision.understand_frame = failing_vision

    enricher = FrameEnricher(ocr_engine=ocr, vision_analyzer=vision, max_workers=2)
    result = enricher.enrich(
        course_id=1,
        frames=[{"timestamp": 10.0, "path": str(frame1)}],
    )

    assert len(result) == 1
    assert result[0]["ocr_text"] == "公式: E=mc^2"
    assert "API 失败" in result[0]["vision_desc"]


def test_parallel_calls_respect_max_workers(tmp_path):
    """并发数不应超过 max_workers。"""
    frames = []
    ocr_texts = {}
    for i in range(6):
        path = tmp_path / f"frame_{i}.jpg"
        path.write_bytes(f"frame{i}".encode())
        frames.append({"timestamp": float(i), "path": str(path)})
        ocr_texts[str(path)] = f"def code_{i}():"

    ocr = FakeOCREngine(ocr_texts)
    vision = FakeVisionAnalyzer()

    enricher = FrameEnricher(ocr_engine=ocr, vision_analyzer=vision, max_workers=4)
    result = enricher.enrich(course_id=1, frames=frames)

    assert len(result) == 6
    assert len(vision.calls) == 6
