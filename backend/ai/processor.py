"""视频处理编排器。"""

import logging
from pathlib import Path

from backend.ai.factory import create_vision_analyzer
from backend.ai.frame_enricher import FrameEnricher
from backend.ai.rag_engine import RAGEngine
from backend.ai.summarizer import Summarizer
from backend.ai.vision.base import BaseVisionAnalyzer
from backend.config import settings
from backend.core.asr_engine import ASREngine
from backend.core.audio_extractor import AudioExtractor
from backend.core.frame_extractor import FrameExtractor
from backend.core.ocr_engine import OCREngine
from backend.models import Course, Frame
from backend.services.course_service import CourseService
from backend.services.summary_service import SummaryService


def _save_course_duration(course_id: int, duration: float) -> None:
    """持久化课程时长。"""
    from backend.database import engine
    from sqlmodel import Session

    with Session(engine) as session:
        course = session.get(Course, course_id)
        if course:
            course.duration = duration
            session.add(course)
            session.commit()


logger = logging.getLogger(__name__)


class VideoProcessor:
    """编排完整视频处理流程。"""

    def __init__(
        self,
        audio_extractor: AudioExtractor | None = None,
        asr_engine: ASREngine | None = None,
        frame_extractor: FrameExtractor | None = None,
        ocr_engine: OCREngine | None = None,
        vision_analyzer: BaseVisionAnalyzer | None = None,
        summarizer: Summarizer | None = None,
    ) -> None:
        # 延迟初始化重型组件，避免在后台任务线程外或请求线程中初始化
        self._audio_extractor = audio_extractor
        self._asr_engine = asr_engine
        self._frame_extractor = frame_extractor
        self._ocr_engine = ocr_engine
        self._vision_analyzer = vision_analyzer
        self._summarizer = summarizer
        self.rag_engine = None
        self.course_service = CourseService()
        self.summary_service = SummaryService()

    @property
    def audio_extractor(self) -> AudioExtractor:
        if self._audio_extractor is None:
            self._audio_extractor = AudioExtractor()
        return self._audio_extractor

    @property
    def asr_engine(self) -> ASREngine:
        if self._asr_engine is None:
            self._asr_engine = ASREngine()
        return self._asr_engine

    @property
    def frame_extractor(self) -> FrameExtractor:
        if self._frame_extractor is None:
            self._frame_extractor = FrameExtractor(
                max_frames=settings.max_frames_per_course,
                frame_interval=settings.frame_interval,
                mode=settings.frame_extraction_mode,
                scene_change_threshold=settings.scene_change_threshold,
                min_scene_interval=settings.min_scene_interval,
            )
        return self._frame_extractor

    @property
    def ocr_engine(self) -> OCREngine:
        if self._ocr_engine is None:
            logger.info("初始化 OCR 引擎...")
            self._ocr_engine = OCREngine()
            logger.info("OCR 引擎初始化完成")
        return self._ocr_engine

    @property
    def vision_analyzer(self) -> BaseVisionAnalyzer:
        if self._vision_analyzer is None:
            logger.info("初始化视觉分析器...")
            self._vision_analyzer = create_vision_analyzer()
            logger.info("视觉分析器初始化完成")
        return self._vision_analyzer

    @property
    def summarizer(self) -> Summarizer:
        if self._summarizer is None:
            self._summarizer = Summarizer()
        return self._summarizer

    def _get_rag_engine(self) -> RAGEngine:
        if self.rag_engine is None:
            logger.info("初始化 RAG 引擎...")
            self.rag_engine = RAGEngine()
            logger.info("RAG 引擎初始化完成")
        return self.rag_engine

    def process(self, course_id: int) -> None:
        """处理单个课程。"""
        course = self.course_service.get_course(course_id)
        if not course:
            raise ValueError(f"课程不存在: {course_id}")

        upload_dir = settings.resolve_path(settings.upload_dir) / str(course_id)
        frame_dir = settings.resolve_path(settings.frame_dir) / str(course_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        frame_dir.mkdir(parents=True, exist_ok=True)

        # 重新处理时先清掉旧的中间产物，避免新旧字幕/帧/RAG 索引堆叠
        self._clear_old_course_data(course_id, frame_dir)

        video_path = Path(course.video_path)
        audio_path = upload_dir / "audio.wav"

        try:
            # 1. 提取音频
            self._update_status(course, "extracting_audio")
            duration = self.audio_extractor.get_duration(video_path)
            course.status_message = f"视频时长: {duration:.1f}s"
            course.duration = duration
            _save_course_duration(course_id, duration)
            self.audio_extractor.extract(video_path, audio_path)

            # 检测音频是否近乎静音（无可用语音）
            mean_volume = self.audio_extractor.get_mean_volume(audio_path)
            low_audio = mean_volume < -40.0
            if low_audio:
                logger.warning("课程 %s 音频近乎静音（平均 %.1f dB），转写可能无有效内容", course_id, mean_volume)

            # 2. 语音识别
            self._update_status(
                course,
                "transcribing",
                f"音频平均音量 {mean_volume:.1f} dB" + ("（近乎静音，可能无法转写）" if low_audio else ""),
            )
            transcripts = self.asr_engine.transcribe(audio_path)
            # 静音音频下 Whisper 会产生幻觉乱码，丢弃以免污染搜索与总结
            if low_audio:
                logger.warning("课程 %s 音频静音，丢弃 %d 条（疑似幻觉）字幕", course_id, len(transcripts))
                transcripts = []
            self._save_transcripts(course_id, transcripts)

            # 3. 抽取关键帧
            self._update_status(course, "extracting_frames")
            frames = self.frame_extractor.extract(video_path, frame_dir)

            # 4. OCR + 视觉理解
            self._update_status(course, "ocr_and_vision")
            enriched_frames = self._enrich_frames(course_id, frames)

            # 5. 生成总结
            self._update_status(course, "generating_summary")
            transcript_dicts = [
                {"text": t["text"], "start_time": t["start_time"], "end_time": t["end_time"]}
                for t in transcripts
            ]
            summary_result = self.summarizer.summarize(
                transcripts=transcript_dicts,
                frames=enriched_frames,
            )
            self.summary_service.save_summary(
                course_id=course_id,
                outline=summary_result["outline"],
                abstract=summary_result["abstract"],
                lecture_notes=summary_result["lecture_notes"],
            )

            # 6. 构建 RAG 索引
            self._update_status(course, "indexing_rag")
            frame_models = self._get_frames(course_id)
            self._get_rag_engine().index_course(course_id, transcripts, frame_models)

            # 7. 完成
            if low_audio:
                done_msg = (
                    f"处理完成，但音频近乎静音（平均 {mean_volume:.1f} dB），"
                    "未转写出有效语音；课件图像识别（OCR/视觉）仍可用于问答。"
                )
            else:
                done_msg = "处理完成"
            self._update_status(course, "completed", done_msg)

        except Exception as e:
            logger.exception("课程处理失败: %s", course_id)
            self._update_status(course, "failed", str(e))
            raise

    def _clear_old_course_data(self, course_id: int, frame_dir: Path) -> None:
        """重新处理前清理旧的字幕、帧、总结和 RAG 索引，避免新旧数据堆叠。"""
        import shutil

        from backend.database import engine
        from backend.models import Frame, Summary, Transcript
        from sqlmodel import Session, delete

        with Session(engine) as session:
            session.exec(delete(Transcript).where(Transcript.course_id == course_id))
            session.exec(delete(Frame).where(Frame.course_id == course_id))
            session.exec(delete(Summary).where(Summary.course_id == course_id))
            session.commit()

        # 清理旧的帧图文件
        if frame_dir.exists():
            shutil.rmtree(frame_dir)
            frame_dir.mkdir(parents=True, exist_ok=True)

        # 清理旧的向量/BM25 索引（失败不阻断）
        try:
            self._get_rag_engine().delete_index(course_id)
        except Exception as e:
            logger.warning("清理旧 RAG 索引失败 course=%s: %s", course_id, e)

    def _update_status(self, course: Course, status: str, message: str | None = None) -> None:
        course.status = status
        course.status_message = message
        course.progress_percent = self._status_to_progress(status)
        self.course_service.update_course(course)

    def _status_to_progress(self, status: str) -> int:
        mapping = {
            "uploaded": 0,
            "extracting_audio": 5,
            "transcribing": 25,
            "extracting_frames": 47,
            "ocr_and_vision": 67,
            "generating_summary": 85,
            "indexing_rag": 95,
            "completed": 100,
            "failed": 100,
        }
        return mapping.get(status, 0)

    def _save_transcripts(self, course_id: int, transcripts: list[dict]) -> None:
        from backend.database import engine
        from backend.models import Transcript
        from sqlmodel import Session

        with Session(engine) as session:
            for item in transcripts:
                transcript = Transcript(
                    course_id=course_id,
                    text=item["text"],
                    start_time=item["start_time"],
                    end_time=item["end_time"],
                )
                session.add(transcript)
            session.commit()

    def _enrich_frames(self, course_id: int, frames: list[dict]) -> list[dict]:
        """使用 FrameEnricher 对帧进行 OCR 和智能视觉理解，并持久化。"""
        from backend.database import engine
        from backend.models import Frame
        from sqlmodel import Session

        enricher = FrameEnricher(
            ocr_engine=self.ocr_engine,
            vision_analyzer=self._vision_analyzer,
            max_workers=settings.vision_max_workers,
        )
        enriched = enricher.enrich(course_id=course_id, frames=frames)

        # 建立 timestamp -> frame_info 的映射，用于回填 image_path
        frame_info_by_timestamp = {f["timestamp"]: f for f in frames}

        with Session(engine) as session:
            orm_frames = []
            for item in enriched:
                frame_info = frame_info_by_timestamp.get(item["timestamp"], {})
                frame = Frame(
                    course_id=course_id,
                    timestamp=item["timestamp"],
                    image_path=frame_info.get("path", ""),
                    ocr_text=item["ocr_text"],
                    vision_desc=item["vision_desc"],
                )
                session.add(frame)
                orm_frames.append(frame)
            session.commit()
            for frame in orm_frames:
                session.refresh(frame)
        return enriched

    def _get_frames(self, course_id: int) -> list[Frame]:
        from backend.database import engine
        from backend.models import Frame
        from sqlmodel import Session, select

        with Session(engine) as session:
            statement = select(Frame).where(Frame.course_id == course_id)
            return list(session.exec(statement).all())
