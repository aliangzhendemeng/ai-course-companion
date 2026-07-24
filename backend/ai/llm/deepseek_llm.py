"""DeepSeek Chat LLM 实现。"""

from openai import OpenAI

from backend.ai.llm.base import BaseLLM
from backend.config import settings


class DeepSeekLLM(BaseLLM):
    """DeepSeek Chat LLM 实现。"""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.deepseek_api_key
        self.model = model_name or "deepseek-chat"
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """调用 DeepSeek Chat 生成文本。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content or ""
