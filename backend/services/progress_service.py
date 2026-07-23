"""学习进度服务。"""

from datetime import datetime

from sqlmodel import Session, select

from backend.database import engine
from backend.models import Progress


class ProgressService:
    """学习进度 CRUD。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def update_progress(self, course_id: int, position: float) -> Progress:
        """更新学习进度。"""
        session = self._get_session()
        statement = select(Progress).where(Progress.course_id == course_id)
        progress = session.exec(statement).first()

        if progress:
            progress.last_position = position
            progress.updated_at = datetime.utcnow()
        else:
            progress = Progress(course_id=course_id, last_position=position)

        session.add(progress)
        session.commit()
        session.refresh(progress)
        if self._owns_session:
            session.close()
        return progress

    def get_progress(self, course_id: int) -> Progress | None:
        """获取学习进度。"""
        session = self._get_session()
        statement = select(Progress).where(Progress.course_id == course_id)
        progress = session.exec(statement).first()
        if self._owns_session:
            session.close()
        return progress
