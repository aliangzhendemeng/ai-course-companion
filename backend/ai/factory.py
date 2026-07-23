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


def create_vision_analyzer(model: str | None = None) -> BaseVisionAnalyzer:
    """根据配置创建视觉分析器。"""
    model = (model or settings.vision_model).lower()
    if model == "deepseek":
        return DeepSeekVisionAnalyzer()
    if model == "gemini":
        return GeminiVisionAnalyzer()
    if model == "local_vlm":
        return LocalVLMVisionAnalyzer()
    raise ValueError(f"不支持的视觉模型: {model}")


def create_llm(model: str | None = None) -> BaseLLM:
    """根据配置创建 LLM。"""
    model = (model or settings.llm_model).lower()
    if model == "deepseek":
        return DeepSeekLLM()
    if model == "gemini":
        return GeminiLLM()
    if model == "claude":
        return ClaudeLLM()
    raise ValueError(f"不支持的 LLM: {model}")
