"""总结业务服务。"""

from sqlmodel import Session, select

from backend.database import engine
from backend.models import Summary


class SummaryService:
    """总结 CRUD。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def save_summary(
        self,
        course_id: int,
        outline: str,
        abstract: str,
        lecture_notes: str,
    ) -> Summary:
        """保存或更新课程总结。"""
        session = self._get_session()
        statement = select(Summary).where(Summary.course_id == course_id)
        summary = session.exec(statement).first()

        if summary:
            summary.outline = outline
            summary.abstract = abstract
            summary.lecture_notes = lecture_notes
        else:
            summary = Summary(
                course_id=course_id,
                outline=outline,
                abstract=abstract,
                lecture_notes=lecture_notes,
            )

        session.add(summary)
        session.commit()
        session.refresh(summary)
        if self._owns_session:
            session.close()
        return summary

    def get_summary(self, course_id: int) -> Summary | None:
        """获取课程总结。"""
        session = self._get_session()
        statement = select(Summary).where(Summary.course_id == course_id)
        summary = session.exec(statement).first()
        if self._owns_session:
            session.close()
        return summary
