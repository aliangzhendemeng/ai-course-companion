"""LLM 抽象接口。"""

from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """大语言模型抽象基类。"""

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """调用 LLM 生成文本。"""
        pass
