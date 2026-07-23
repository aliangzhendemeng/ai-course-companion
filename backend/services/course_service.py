"""课程业务服务。"""

import shutil
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, select

from backend.config import settings
from backend.database import engine
from backend.models import Course


class CourseService:
    """课程 CRUD 与状态管理。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def create_course(self, title: str, video_path: str | Path, duration: float | None = None) -> Course:
        """创建课程记录。"""
        session = self._get_session()
        course = Course(
            title=title,
            video_path=str(video_path),
            duration=duration,
            status="uploaded",
        )
        session.add(course)
        session.commit()
        session.refresh(course)
        if self._owns_session:
            session.close()
        return course

    def update_status(
        self,
        course_id: int,
        status: str,
        status_message: str | None = None,
    ) -> Course:
        """更新课程处理状态。"""
        session = self._get_session()
        course = session.get(Course, course_id)
        if not course:
            raise ValueError(f"课程不存在: {course_id}")

        course.status = status
        course.status_message = status_message
        course.updated_at = datetime.utcnow()
        session.add(course)
        session.commit()
        session.refresh(course)
        if self._owns_session:
            session.close()
        return course

    def get_course(self, course_id: int) -> Course | None:
        """获取课程。"""
        session = self._get_session()
        course = session.get(Course, course_id)
        if self._owns_session:
            session.close()
        return course

    def list_courses(self) -> list[Course]:
        """列出所有课程，按创建时间倒序。"""
        session = self._get_session()
        statement = select(Course).order_by(Course.created_at.desc())
        courses = session.exec(statement).all()
        if self._owns_session:
            session.close()
        return list(courses)

    def update_course(self, course: Course) -> Course:
        """更新课程记录。"""
        session = self._get_session()
        session.add(course)
        session.commit()
        session.refresh(course)
        if self._owns_session:
            session.close()
        return course

    def delete_course(self, course_id: int) -> None:
        """删除课程及相关文件。"""
        session = self._get_session()
        course = session.get(Course, course_id)
        if not course:
            if self._owns_session:
                session.close()
            return

        # 删除本地文件
        upload_dir = settings.resolve_path(settings.upload_dir) / str(course_id)
        frame_dir = settings.resolve_path(settings.frame_dir) / str(course_id)
        chroma_dir = settings.resolve_path(settings.chroma_dir)
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        if frame_dir.exists():
            shutil.rmtree(frame_dir)

        # 删除向量索引
        try:
            from backend.ai.rag_engine import RAGEngine
            RAGEngine().delete_index(course_id)
        except Exception:
            pass

        session.delete(course)
        session.commit()
        if self._owns_session:
            session.close()
