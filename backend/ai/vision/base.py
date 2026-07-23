"""视觉分析抽象接口。"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseVisionAnalyzer(ABC):
    """视觉分析器抽象基类。"""

    @abstractmethod
    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像，返回文字描述。"""
        pass
