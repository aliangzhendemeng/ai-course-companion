"""Claude LLM 实现。"""

from backend.ai.llm.base import BaseLLM
from backend.config import settings


class ClaudeLLM(BaseLLM):
    """Claude LLM 实现。"""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        import anthropic

        self.api_key = api_key or settings.claude_api_key
        self.model_name = model_name or "claude-3-5-sonnet-20241022"
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """调用 Claude 生成文本。"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content
        if content and len(content) > 0:
            return content[0].text
        return ""
