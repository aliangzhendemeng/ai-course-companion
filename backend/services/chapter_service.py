"""章节速览服务：按时间窗口自动分章，AI 生成每章标题与速览，缓存到库。"""

import json
import logging

from sqlmodel import Session, select

from backend.ai.factory import create_chat_llm
from backend.ai.llm.base import BaseLLM
from backend.database import engine
from backend.models import Chapter, Course, Transcript

logger = logging.getLogger(__name__)

MIN_CHAPTERS = 3
MAX_CHAPTERS = 12
TARGET_MINUTES = 5  # 约每 5 分钟一章
MAX_TEXT_PER_CHAPTER = 800


def _fmt(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"


def _extract_json_array(text: str) -> list:
    """从 LLM 输出中提取首个 JSON 数组（容错：跳过 markdown 围栏、处理转义/括号在字符串内）。"""
    s = text.strip()
    start = s.find("[")
    if start < 0:
        return []
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(s[start : i + 1])
                    except json.JSONDecodeError:
                        return []
    return []


class ChapterService:
    """章节划分与速览生成。"""

    def __init__(self, llm: BaseLLM | None = None) -> None:
        self.llm = llm or create_chat_llm()

    def list_chapters(self, course_id: int) -> list[Chapter]:
        """返回课程章节；首次调用时自动生成并缓存。"""
        with Session(engine) as session:
            existing = list(
                session.exec(
                    select(Chapter).where(Chapter.course_id == course_id).order_by(Chapter.index)
                ).all()
            )
            if existing:
                return existing
        return self.generate(course_id)

    def generate(self, course_id: int) -> list[Chapter]:
        """按时间窗口分章，AI 生成标题/速览，存库。"""
        with Session(engine) as session:
            course = session.get(Course, course_id)
            if not course:
                raise ValueError(f"课程不存在: {course_id}")
            transcripts = list(
                session.exec(
                    select(Transcript)
                    .where(Transcript.course_id == course_id)
                    .order_by(Transcript.start_time)
                ).all()
            )
        if not transcripts:
            return []

        chapters = self._split(transcripts)
        if not chapters:
            return []

        meta = self._llm_meta(chapters)
        with Session(engine) as session:
            # 重新生成前清旧
            for old in session.exec(select(Chapter).where(Chapter.course_id == course_id)).all():
                session.delete(old)
            rows = []
            for c in chapters:
                m = meta.get(c["index"], {})
                row = Chapter(
                    course_id=course_id,
                    index=c["index"],
                    title=(m.get("title") or f"第 {c['index']} 章").strip(),
                    summary=(m.get("summary") or "").strip(),
                    start_time=c["start"],
                    end_time=c["end"],
                )
                session.add(row)
                rows.append(row)
            session.commit()
            for r in rows:
                session.refresh(r)
        return rows

    @staticmethod
    def _split(transcripts: list[Transcript]) -> list[dict]:
        """按时间窗口分章，返回 [{index,start,end,text}]。"""
        duration = max((t.end_time for t in transcripts), default=0.0)
        if duration <= 0:
            duration = max((t.start_time for t in transcripts), default=0.0)
        if duration <= 0:
            return []
        target = max(MIN_CHAPTERS, min(MAX_CHAPTERS, round(duration / (TARGET_MINUTES * 60))))
        window = duration / target
        chapters = []
        for i in range(target):
            start = i * window
            end = (i + 1) * window if i < target - 1 else duration
            segs = [t for t in transcripts if start - 1 <= t.start_time < end]
            text = " ".join(t.text for t in segs if t.text).strip()[:MAX_TEXT_PER_CHAPTER]
            chapters.append({"index": i + 1, "start": start, "end": end, "text": text})
        return chapters

    def _llm_meta(self, chapters: list[dict]) -> dict:
        """让 LLM 批量为每章生成标题与一句话速览，返回 {index: {title, summary}}。"""
        context = "\n\n".join(
            f"第{c['index']}章（{_fmt(c['start'])}-{_fmt(c['end'])}）：\n{c['text']}"
            for c in chapters
            if c["text"]
        )
        if not context.strip():
            return {}
        system_prompt = "你是一位课程助教。请为下面的视频章节各生成一个简短标题和一句话速览。"
        user_prompt = f"""
        以下是按时间划分的视频章节及其字幕：

        {context}

        请为每个章节生成标题和速览，严格输出 JSON 数组，不要额外文字：
        [{{"index": 1, "title": "章节标题", "summary": "一句话速览"}}, ...]
        index 必须与上面一致。title 不超过 15 字，summary 不超过 40 字。
        """
        try:
            raw = self.llm.chat(system_prompt, user_prompt, max_tokens=1200)
            arr = _extract_json_array(raw)
        except Exception as e:
            logger.warning("章节速览 LLM 调用失败: %s", e)
            return {}
        return {int(item.get("index", 0)): item for item in arr if isinstance(item, dict)}
