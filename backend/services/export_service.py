"""导出服务：把闪卡/错题导出为 Markdown 或 Anki 可导入的 TSV。

复用 FlashcardService / QuizService 的查询，不重复实现范围解析。
"""

import json
import logging
from sqlmodel import Session, select

from backend.database import engine
from backend.models import Course, StudySet
from backend.services.flashcard_service import FlashcardService
from backend.services.quiz_service import QuizService

logger = logging.getLogger(__name__)

VALID_FLASHCARD_FORMATS = ("md", "anki")
VALID_WRONG_FORMATS = ("md",)


def _fmt_ts(seconds: float | None) -> str:
    """秒 -> M:SS 或 H:MM:SS。"""
    if not seconds or seconds < 0:
        return ""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"


class ExportService:
    """闪卡/错题导出。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def _scope_label(self, course_id: int | None, study_set_id: int | None) -> str:
        """导出范围的可读名称。"""
        session = self._get_session()
        if course_id is not None:
            c = session.get(Course, course_id)
            return c.title if c else f"课程 {course_id}"
        if study_set_id is not None:
            s = session.get(StudySet, study_set_id)
            return s.name if s and hasattr(s, "name") else "学习集"
        return "全部"

    # ----- 闪卡 -----

    def export_flashcards(
        self, course_id: int | None = None, study_set_id: int | None = None, fmt: str = "md"
    ) -> str:
        if fmt not in VALID_FLASHCARD_FORMATS:
            raise ValueError(f"非法格式: {fmt}（应为 md/anki）")
        cards = FlashcardService(session=self.session).list_cards(course_id, study_set_id)
        if fmt == "anki":
            return self._flashcards_anki(cards)
        return self._flashcards_md(cards, self._scope_label(course_id, study_set_id))

    @staticmethod
    def _flashcards_anki(cards) -> str:
        """Anki 可导入的 TSV：正面<TAB>背面。内容换行转 <br>。"""
        lines = []
        for c in cards:
            front = (c.front or "").replace("\n", "<br>").replace("\t", " ")
            back = (c.back or "").replace("\n", "<br>").replace("\t", " ")
            lines.append(f"{front}\t{back}")
        return "\n".join(lines)

    @staticmethod
    def _flashcards_md(cards, label: str) -> str:
        """按熟悉度分组的 Markdown。"""
        buckets = {"known": [], "fuzzy": [], "unknown": []}
        for c in cards:
            buckets.setdefault(c.familiarity, []).append(c)
        title_name = {"known": "✓ 认识", "fuzzy": "~ 模糊", "unknown": "✗ 不认识"}
        out = [f"# 闪卡导出 — {label}", "", f"共 {len(cards)} 张", ""]
        for key in ("unknown", "fuzzy", "known"):
            group = buckets.get(key, [])
            if not group:
                continue
            out.append(f"## {title_name.get(key, key)}（{len(group)}）")
            out.append("")
            for c in group:
                out.append(f"- **{c.front}**")
                out.append(f"  - {c.back}")
            out.append("")
        return "\n".join(out)

    # ----- 错题 -----

    def export_wrong_questions(
        self, course_id: int | None = None, study_set_id: int | None = None, fmt: str = "md"
    ) -> str:
        if fmt not in VALID_WRONG_FORMATS:
            raise ValueError(f"非法格式: {fmt}（错题仅支持 md）")
        items = QuizService(session=self.session).get_wrong_questions(course_id, study_set_id)
        return self._wrong_md(items, self._scope_label(course_id, study_set_id))

    @staticmethod
    def _wrong_md(items, label: str) -> str:
        mastered = [it for it in items if it[1]]
        unmastered = [it for it in items if not it[1]]
        out = [f"# 错题本导出 — {label}", "", f"共 {len(items)} 题（未掌握 {len(unmastered)} · 已掌握 {len(mastered)}）", ""]

        def render(q, wrong_count: int, idx: int) -> list[str]:
            qtype = "判断题" if q.type == "judge" else "选择题"
            lines = [f"### {idx}. {qtype}"]
            lines.append(f"**题目：** {q.question}")
            try:
                opts = json.loads(q.options) if q.options else []
            except (json.JSONDecodeError, TypeError):
                opts = []
            if q.type != "judge" and opts:
                for i, opt in enumerate(opts):
                    letter = chr(ord("A") + i)
                    mark = "✓" if letter == q.answer else "·"
                    lines.append(f"  {mark} {letter}. {opt}")
                lines.append(f"**正确答案：** {q.answer}")
            else:
                lines.append(f"**正确答案：** {q.answer}")
            if q.explanation:
                lines.append(f"**解析：** {q.explanation}")
            meta = []
            ts = _fmt_ts(q.source_timestamp)
            if ts:
                meta.append(f"来源 {ts}")
            meta.append(f"错 {wrong_count} 次")
            lines.append("".join(f"`{m}` " for m in meta).strip())
            lines.append("")
            return lines

        out.append(f"## ✗ 未掌握（{len(unmastered)}）")
        out.append("")
        for i, (q, _m, w, _s) in enumerate(unmastered, 1):
            out.extend(render(q, w, i))
        out.append(f"## ✓ 已掌握（{len(mastered)}）")
        out.append("")
        base = len(unmastered)
        for i, (q, _m, w, _s) in enumerate(mastered, 1):
            out.extend(render(q, w, base + i))
        return "\n".join(out)
