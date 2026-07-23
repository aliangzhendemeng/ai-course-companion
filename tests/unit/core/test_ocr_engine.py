"""OCR 引擎测试。"""

import pytest

from backend.core.ocr_engine import OCREngine


def test_ocr_engine_init():
    engine = OCREngine(confidence_threshold=0.7)
    assert engine.confidence_threshold == 0.7
