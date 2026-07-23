import pytest

from backend.config import settings


def test_settings_defaults():
    assert settings.vision_model == "deepseek"
    assert settings.llm_model == "deepseek"
    assert settings.max_frames_per_course == 120


def test_create_vision_analyzer():
    from backend.ai.factory import create_vision_analyzer
    from backend.ai.vision.deepseek_vision import DeepSeekVisionAnalyzer

    analyzer = create_vision_analyzer("deepseek")
    assert isinstance(analyzer, DeepSeekVisionAnalyzer)


def test_create_llm():
    from backend.ai.factory import create_llm
    from backend.ai.llm.deepseek_llm import DeepSeekLLM

    llm = create_llm("deepseek")
    assert isinstance(llm, DeepSeekLLM)
