"""时间段总结服务：对视频某段时间区间内的字幕/课件内容做要点总结。"""

import logging

from sqlmodel import Session, select

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.database import engine
from backend.models import Course, Frame, Transcript

logger = logging.getLogger(__name__)

MAX_WINDOW_SECONDS = 30 * 60  # 单次最多总结 30 分钟，避免上下文过大


def _fmt(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"


class SegmentSummaryService:
    """对指定时间段做要点总结。"""

    def __init__(self, llm: BaseLLM | None = None) -> None:
        self.llm = llm or create_chat_llm()

    def summarize(self, course_id: int, start: float, end: float) -> dict:
        if start < 0 or end <= start:
            raise ValueError("时间区间非法（需 0 ≤ start < end）")
        if end - start > MAX_WINDOW_SECONDS:
            raise ValueError(f"时间区间过长，单次最多 {MAX_WINDOW_SECONDS // 60} 分钟")

        with Session(engine) as session:
            course = session.get(Course, course_id)
            if not course:
                raise ValueError(f"课程不存在: {course_id}")
            transcripts = list(
                session.exec(
                    select(Transcript)
                    .where(Transcript.course_id == course_id)
                    .where(Transcript.start_time >= start)
                    .where(Transcript.start_time <= end)
                    .order_by(Transcript.start_time)
                ).all()
            )
            frames = list(
                session.exec(
                    select(Frame)
                    .where(Frame.course_id == course_id)
                    .where(Frame.timestamp >= start)
                    .where(Frame.timestamp <= end)
                    .order_by(Frame.timestamp)
                ).all()
            )

        parts = [f"[{_fmt(t.start_time)}] {t.text}" for t in transcripts if t.text and t.text.strip()]
        for f in frames:
            if f.ocr_text:
                parts.append(f"[课件 {_fmt(f.timestamp)}] {f.ocr_text}")

        if not parts:
            raise ValueError("该时间段没有字幕或课件内容")

        context = "\n".join(parts)
        system_prompt = (
            "你是一位课程助教。请根据下面提供的视频片段内容（字幕与课件文字），"
            "为用户做要点总结。用简洁的条目列出这段内容讲了什么。"
            "如果内容很少，就如实整理而非强行扩充。"
        )
        user_prompt = f"""
        时间段：{_fmt(start)} - {_fmt(end)}

        片段内容：
        {context}

        请用 3~6 个要点总结这段内容的核心。
        """
        summary = self.llm.chat(system_prompt, user_prompt, max_tokens=800)

        return {
            "summary": summary,
            "start": start,
            "end": end,
            "segment_count": len(parts),
        }
