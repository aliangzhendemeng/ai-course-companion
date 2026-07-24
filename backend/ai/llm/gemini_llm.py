"""Gemini LLM 实现。"""

from backend.ai.llm.base import BaseLLM
from backend.config import settings


class GeminiLLM(BaseLLM):
    """Gemini LLM 实现。"""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        import google.generativeai as genai

        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or "gemini-1.5-flash"
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_name)

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """调用 Gemini 生成文本。"""
        import google.generativeai as genai

        response = self.client.generate_content(
            f"{system_prompt}\n\n{user_prompt}",
            generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
        )
        return response.text or ""
