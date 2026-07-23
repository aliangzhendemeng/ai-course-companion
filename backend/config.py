"""全局配置管理。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    claude_api_key: str = ""

    # 模型配置
    vision_model: str = "deepseek"
    llm_model: str = "deepseek"

    # 本地 VLM 预留配置
    local_vlm_model_path: str = ""
    local_vlm_device: str = "cpu"

    # 处理配置
    frame_interval: int = 20
    max_frames_per_course: int = 120
    ocr_confidence_threshold: float = 0.6
    rag_top_k: int = 5

    # 数据路径
    upload_dir: str = "./data/uploads"
    frame_dir: str = "./data/frames"
    chroma_dir: str = "./data/chroma"
    database_url: str = "sqlite:///./data/app.db"

    # 日志
    log_level: str = "INFO"

    @property
    def project_root(self) -> Path:
        """项目根目录。"""
        return Path(__file__).parent.parent

    def resolve_path(self, path: str) -> Path:
        """解析相对路径为绝对路径。"""
        p = Path(path)
        if p.is_absolute():
            return p
        return self.project_root / p


settings = Settings()
