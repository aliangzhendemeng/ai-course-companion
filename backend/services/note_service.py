"""笔记/书签业务服务：按课程增删改查，按视频时间点排序。"""

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from backend.database import engine
from backend.models import Course, Note

logger = logging.getLogger(__name__)

VALID_KINDS = ("note", "bookmark")


class NoteService:
    """笔记/书签的增删改查。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    # ----- 查询 -----

    def list_notes(self, course_id: int) -> list[Note]:
        """列出某课程的全部笔记/书签，按视频时间点升序。"""
        session = self._get_session()
        statement = (
            select(Note)
            .where(Note.course_id == course_id)
            .order_by(Note.timestamp, Note.id)
        )
        notes = list(session.exec(statement).all())
        for n in notes:
            _ = (n.id, n.course_id, n.kind, n.content, n.timestamp, n.created_at, n.updated_at)
        if self._owns_session:
            session.close()
        return notes

    # ----- 创建 -----

    def create(
        self,
        course_id: int,
        kind: str = "note",
        content: str = "",
        timestamp: float = 0.0,
    ) -> Note:
        if kind not in VALID_KINDS:
            raise ValueError(f"非法类型: {kind}（应为 note/bookmark）")
        content = (content or "").strip()
        if kind == "note" and not content:
            raise ValueError("笔记内容不能为空")
        if timestamp < 0:
            raise ValueError("时间点不能为负")

        session = self._get_session()
        if not session.get(Course, course_id):
            if self._owns_session:
                session.close()
            raise ValueError(f"课程不存在: {course_id}")

        note = Note(course_id=course_id, kind=kind, content=content, timestamp=timestamp)
        session.add(note)
        session.commit()
        session.refresh(note)
        _ = (note.id, note.course_id, note.kind, note.content, note.timestamp,
             note.created_at, note.updated_at)
        if self._owns_session:
            session.close()
        return note

    # ----- 更新 -----

    def update(self, note_id: int, content: str) -> Note:
        content = (content or "").strip()
        if not content:
            raise ValueError("内容不能为空")
        session = self._get_session()
        note = session.get(Note, note_id)
        if not note:
            if self._owns_session:
                session.close()
            raise ValueError(f"笔记不存在: {note_id}")
        note.content = content
        note.updated_at = datetime.now(timezone.utc)
        session.add(note)
        session.commit()
        session.refresh(note)
        _ = (note.id, note.course_id, note.kind, note.content, note.timestamp,
             note.created_at, note.updated_at)
        if self._owns_session:
            session.close()
        return note

    # ----- 删除 -----

    def delete(self, note_id: int) -> None:
        session = self._get_session()
        note = session.get(Note, note_id)
        if not note:
            if self._owns_session:
                session.close()
            raise ValueError(f"笔记不存在: {note_id}")
        session.delete(note)
        session.commit()
        if self._owns_session:
            session.close()
