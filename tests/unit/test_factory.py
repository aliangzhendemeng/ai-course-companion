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


def test_create_summary_llm_uses_summary_config(monkeypatch):
    """create_summary_llm 应使用 SUMMARY_MODEL 配置。"""
    from backend.ai.factory import create_summary_llm
    from backend.ai.llm.deepseek_llm import DeepSeekLLM

    monkeypatch.setattr(settings, "summary_model", "deepseek")
    monkeypatch.setattr(settings, "summary_api_key", "summary-key")

    llm = create_summary_llm()
    assert isinstance(llm, DeepSeekLLM)
    assert llm.api_key == "summary-key"
    assert llm.model == "deepseek-chat"


def test_create_chat_llm_uses_chat_config(monkeypatch):
    """create_chat_llm 应使用 CHAT_MODEL 配置。"""
    from backend.ai.factory import create_chat_llm
    from backend.ai.llm.deepseek_llm import DeepSeekLLM

    monkeypatch.setattr(settings, "chat_model", "deepseek")
    monkeypatch.setattr(settings, "chat_api_key", "chat-key")

    llm = create_chat_llm()
    assert isinstance(llm, DeepSeekLLM)
    assert llm.api_key == "chat-key"


def test_create_vision_analyzer_uses_vision_config(monkeypatch):
    """create_vision_analyzer 应使用 VISION_MODEL 与 VISION_API_KEY 配置。"""
    from backend.ai.factory import create_vision_analyzer
    from backend.ai.vision.deepseek_vision import DeepSeekVisionAnalyzer

    monkeypatch.setattr(settings, "vision_model", "deepseek")
    monkeypatch.setattr(settings, "vision_api_key", "vision-key")

    analyzer = create_vision_analyzer()
    assert isinstance(analyzer, DeepSeekVisionAnalyzer)
    assert analyzer.api_key == "vision-key"


def test_create_summary_llm_fallback_to_legacy_llm_model(monkeypatch):
    """当 SUMMARY_MODEL 为空时，应回退到 LLM_MODEL。"""
    from backend.ai.factory import create_summary_llm
    from backend.ai.llm.deepseek_llm import DeepSeekLLM

    monkeypatch.setattr(settings, "summary_model", "")
    monkeypatch.setattr(settings, "llm_model", "deepseek")
    monkeypatch.setattr(settings, "summary_api_key", "")
    monkeypatch.setattr(settings, "deepseek_api_key", "legacy-key")

    llm = create_summary_llm()
    assert isinstance(llm, DeepSeekLLM)
    assert llm.api_key == "legacy-key"


def test_create_chat_llm_fallback_to_legacy_llm_model(monkeypatch):
    """当 CHAT_MODEL 为空时，应回退到 LLM_MODEL。"""
    from backend.ai.factory import create_chat_llm
    from backend.ai.llm.deepseek_llm import DeepSeekLLM

    monkeypatch.setattr(settings, "chat_model", "")
    monkeypatch.setattr(settings, "llm_model", "deepseek")
    monkeypatch.setattr(settings, "chat_api_key", "")
    monkeypatch.setattr(settings, "deepseek_api_key", "legacy-key")

    llm = create_chat_llm()
    assert isinstance(llm, DeepSeekLLM)
    assert llm.api_key == "legacy-key"


def test_create_vision_analyzer_fallback_to_legacy_vision_model(monkeypatch):
    """当 VISION_MODEL 为空时，应回退到 VISION_MODEL（旧配置）。"""
    from backend.ai.factory import create_vision_analyzer
    from backend.ai.vision.deepseek_vision import DeepSeekVisionAnalyzer

    monkeypatch.setattr(settings, "vision_model", "deepseek")
    monkeypatch.setattr(settings, "vision_api_key", "")
    monkeypatch.setattr(settings, "deepseek_api_key", "legacy-key")

    analyzer = create_vision_analyzer()
    assert isinstance(analyzer, DeepSeekVisionAnalyzer)
    assert analyzer.api_key == "legacy-key"
