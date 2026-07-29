"""全局配置管理。"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.services.settings_service import SettingsService


class _BaseSettings(BaseSettings):
    """静态配置：从 .env 加载，运行时不变。"""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Keys
    deepseek_api_key: str = ""
    gemini_api_key: str = ""
    claude_api_key: str = ""

    # 模型配置（旧配置，保持向后兼容）
    vision_model: str = "deepseek"
    llm_model: str = "deepseek"

    # 本地 VLM 预留配置
    local_vlm_model_path: str = ""
    local_vlm_device: str = "cpu"

    # ASR 语音识别配置
    # 模型大小：tiny / base / small / medium / large-v3。
    # base 中文识别较差（专业术语易听错），中文课程建议 small 或 medium。
    asr_model_size: str = "small"
    asr_device: str = "cpu"
    asr_compute_type: str = "int8"

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


_base_settings = _BaseSettings()


class Settings:
    """统一配置入口：静态配置 + 动态配置（支持运行时覆盖）。"""

    def __init__(self) -> None:
        self._static = _base_settings
        self._dynamic = SettingsService().load()

    def refresh(self) -> None:
        """重新从 .env 加载动态配置。"""
        self._dynamic = SettingsService().load()

    # 透传静态属性
    @property
    def project_root(self) -> Path:
        return self._static.project_root

    def resolve_path(self, path: str) -> Path:
        return self._static.resolve_path(path)

    @property
    def frame_interval(self) -> int:
        return self._static.frame_interval

    @property
    def asr_model_size(self) -> str:
        return self._static.asr_model_size

    @property
    def asr_device(self) -> str:
        return self._static.asr_device

    @property
    def asr_compute_type(self) -> str:
        return self._static.asr_compute_type

    @property
    def max_frames_per_course(self) -> int:
        return self._static.max_frames_per_course

    @property
    def frame_extraction_mode(self) -> str:
        return self._static.frame_extraction_mode

    @property
    def scene_change_threshold(self) -> float:
        return self._static.scene_change_threshold

    @property
    def min_scene_interval(self) -> float:
        return self._static.min_scene_interval

    @property
    def ocr_confidence_threshold(self) -> float:
        return self._static.ocr_confidence_threshold

    @property
    def vision_max_workers(self) -> int:
        return self._static.vision_max_workers

    @property
    def rag_top_k(self) -> int:
        return self._static.rag_top_k

    @property
    def rag_vector_k(self) -> int:
        return self._static.rag_vector_k

    @property
    def rag_bm25_k(self) -> int:
        return self._static.rag_bm25_k

    @property
    def rag_rrf_k(self) -> int:
        return self._static.rag_rrf_k

    @property
    def frontend_origin(self) -> str:
        return self._static.frontend_origin

    @property
    def video_stream_chunk_size(self) -> int:
        return self._static.video_stream_chunk_size

    @property
    def upload_dir(self) -> str:
        return self._static.upload_dir

    @property
    def frame_dir(self) -> str:
        return self._static.frame_dir

    @property
    def chroma_dir(self) -> str:
        return self._static.chroma_dir

    @property
    def bm25_dir(self) -> str:
        return self._static.bm25_dir

    @property
    def database_url(self) -> str:
        return self._static.database_url

    @property
    def log_level(self) -> str:
        return self._static.log_level

    @property
    def local_vlm_model_path(self) -> str:
        return self._static.local_vlm_model_path

    @property
    def local_vlm_device(self) -> str:
        return self._static.local_vlm_device

    # 动态属性（可被运行时覆盖）
    @property
    def chat_model(self) -> str:
        return self._dynamic.get("chat_model") or self._static.llm_model

    @property
    def summary_model(self) -> str:
        return self._dynamic.get("summary_model") or self._static.llm_model

    @property
    def vision_model(self) -> str:
        return self._dynamic.get("vision_model") or self._static.vision_model

    @property
    def chat_api_key(self) -> str:
        return self._dynamic.get("chat_api_key") or self._static.deepseek_api_key

    @property
    def summary_api_key(self) -> str:
        return self._dynamic.get("summary_api_key") or self._static.deepseek_api_key

    @property
    def vision_api_key(self) -> str:
        return self._dynamic.get("vision_api_key") or self._static.deepseek_api_key

    @property
    def enable_vision(self) -> bool:
        return self._dynamic.get("enable_vision", False)

    @property
    def is_configured(self) -> bool:
        return self._dynamic.get("is_configured", False)

    # 向后兼容旧属性名
    @property
    def llm_model(self) -> str:
        return self.chat_model

    @property
    def deepseek_api_key(self) -> str:
        return self._static.deepseek_api_key

    @property
    def gemini_api_key(self) -> str:
        return self._static.gemini_api_key

    @property
    def claude_api_key(self) -> str:
        return self._static.claude_api_key


settings = Settings()
