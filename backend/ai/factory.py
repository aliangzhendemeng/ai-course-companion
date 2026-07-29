"""AI 模块工厂函数。"""

from backend.ai.llm.base import BaseLLM
from backend.ai.llm.claude_llm import ClaudeLLM
from backend.ai.llm.deepseek_llm import DeepSeekLLM
from backend.ai.llm.gemini_llm import GeminiLLM
from backend.ai.vision.base import BaseVisionAnalyzer
from backend.ai.vision.deepseek_vision import DeepSeekVisionAnalyzer
from backend.ai.vision.gemini_vision import GeminiVisionAnalyzer
from backend.ai.vision.local_vlm_vision import LocalVLMVisionAnalyzer
from backend.config import settings


_LLM_PROVIDERS = {
    "deepseek": DeepSeekLLM,
    "gemini": GeminiLLM,
    "claude": ClaudeLLM,
}

_VISION_PROVIDERS = {
    "deepseek": DeepSeekVisionAnalyzer,
    "gemini": GeminiVisionAnalyzer,
    "local_vlm": LocalVLMVisionAnalyzer,
}


def _resolve_model(role_model: str, fallback_model: str) -> str:
    """解析模型配置：角色配置优先，为空时回退。"""
    return (role_model or fallback_model or "deepseek").lower()


def _resolve_api_key(role_key: str, provider_name: str) -> str:
    """解析 API Key：角色 Key 优先，为空时按 provider 回退。"""
    if role_key:
        return role_key
    provider_name = provider_name.lower()
    if provider_name == "deepseek":
        return settings.deepseek_api_key or settings.chat_api_key or settings.summary_api_key
    if provider_name == "gemini":
        return settings.gemini_api_key or settings.chat_api_key or settings.summary_api_key
    if provider_name == "claude":
        return settings.claude_api_key or settings.chat_api_key or settings.summary_api_key
    return ""


def create_vision_analyzer(model: str | None = None) -> BaseVisionAnalyzer:
    """根据配置创建视觉分析器。

    优先使用传入的 model，其次使用 VISION_MODEL（新配置），最后使用旧 VISION_MODEL。
    API Key 优先使用 VISION_API_KEY，其次按 provider 回退。
    支持 model 格式：provider 或 provider:model_name
    """
    model_input = (model or settings.vision_model or "deepseek").lower()
    parts = model_input.split(":", 1)
    model_name = parts[0]
    specific_model = parts[1] if len(parts) > 1 else None
    api_key = _resolve_api_key(settings.vision_api_key, model_name)

    provider = _VISION_PROVIDERS.get(model_name)
    if provider is None:
        raise ValueError(f"不支持的视觉模型: {model_name}")
    return provider(api_key=api_key, model_name=specific_model)


def create_llm(model: str | None = None) -> BaseLLM:
    """根据配置创建 LLM（通用，保持向后兼容）。

    支持 model 格式：provider 或 provider:model_name
    """
    model_input = (model or settings.llm_model or "deepseek").lower()
    parts = model_input.split(":", 1)
    model_name = parts[0]
    specific_model = parts[1] if len(parts) > 1 else None
    api_key = _resolve_api_key("", model_name)

    provider = _LLM_PROVIDERS.get(model_name)
    if provider is None:
        raise ValueError(f"不支持的 LLM: {model_name}")
    return provider(api_key=api_key, model_name=specific_model)


def _create_role_llm(role_model: str, fallback_model: str, role_api_key: str) -> BaseLLM:
    """创建角色专用 LLM（总结/聊天）。"""
    model_input = _resolve_model(role_model, fallback_model)
    parts = model_input.split(":", 1)
    model_name = parts[0]
    specific_model = parts[1] if len(parts) > 1 else None
    api_key = _resolve_api_key(role_api_key, model_name)

    provider = _LLM_PROVIDERS.get(model_name)
    if provider is None:
        raise ValueError(f"不支持的模型: {model_name}")
    return provider(api_key=api_key, model_name=specific_model)


def create_summary_llm() -> BaseLLM:
    """创建用于生成总结的 LLM。"""
    return _create_role_llm(settings.summary_model, settings.llm_model, settings.summary_api_key)


def create_chat_llm() -> BaseLLM:
    """创建用于问答聊天的 LLM。"""
    return _create_role_llm(settings.chat_model, settings.llm_model, settings.chat_api_key)
