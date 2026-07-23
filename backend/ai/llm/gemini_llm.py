"""Gemini LLM 实现（预留）。"""

from backend.ai.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """Gemini LLM 实现（预留）。"""

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """调用 Gemini 生成文本。"""
        raise NotImplementedError("Gemini LLM 尚未实现")
