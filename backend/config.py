"""全局配置管理。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    claude_api_key: str = ""

    # 多模型配置（新增）
    # 为空时自动回退到旧的 llm_model / vision_model 与对应 provider key
    summary_model: str = ""
    chat_model: str = ""
    summary_api_key: str = ""
    chat_api_key: str = ""
    vision_api_key: str = ""

    # 模型配置（旧配置，保持向后兼容）
    vision_model: str = "deepseek"
    llm_model: str = "deepseek"

    # 本地 VLM 预留配置
    local_vlm_model_path: str = ""
    local_vlm_device: str = "cpu"

    # 处理配置
    frame_interval: int = 20
    max_frames_per_course: int = 120
    frame_extraction_mode: str = "scene"  # uniform | scene
    scene_change_threshold: float = 0.65
    min_scene_interval: float = 5.0
    ocr_confidence_threshold: float = 0.6

    # RAG 配置
    rag_top_k: int = 5
    rag_vector_k: int = 50
    rag_bm25_k: int = 50
    rag_rrf_k: int = 60

    # 视觉 API 并发
    vision_max_workers: int = 4

    # CORS / 前端
    frontend_origin: str = "http://localhost:3000"

    # 视频流
    video_stream_chunk_size: int = 1024 * 1024  # 1MB

    # 数据路径
    upload_dir: str = "./data/uploads"
    frame_dir: str = "./data/frames"
    chroma_dir: str = "./data/chroma"
    bm25_dir: str = "./data/bm25"
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
