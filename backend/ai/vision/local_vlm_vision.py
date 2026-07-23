"""本地 VLM 视觉分析实现（预留接口）。"""

from pathlib import Path

from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings


class LocalVLMVisionAnalyzer(BaseVisionAnalyzer):
    """本地视觉语言模型分析器（预留实现）。

    二期可通过 Ollama 或 vLLM 接入 Qwen2-VL、InternVL2、LLaVA 等模型。
    """

    def __init__(self, model_path: str | None = None, device: str | None = None) -> None:
        self.model_path = model_path or settings.local_vlm_model_path
        self.device = device or settings.local_vlm_device

    def understand_frame(self, image_path: str | Path) -> str:
        """理解单帧图像。"""
        if not self.model_path:
            raise ValueError("未配置本地 VLM 模型路径 LOCAL_VLM_MODEL_PATH")
        raise NotImplementedError("本地 VLM 推理尚未实现，预留接口")
