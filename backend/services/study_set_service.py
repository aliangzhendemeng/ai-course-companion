"""学习集业务服务：命名课程组合的 CRUD 与展开。"""

from datetime import datetime

from sqlmodel import Session, select

from backend.database import engine
from backend.models import Course, StudySet, StudySetCourse


class StudySetService:
    """学习集 CRUD 与 course_ids 展开（用于限定问答范围）。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def create_set(self, name: str, course_ids: list[int]) -> StudySet:
        """创建学习集并关联课程。"""
        name = name.strip()
        if not name:
            raise ValueError("学习集名称不能为空")
        session = self._get_session()
        study_set = StudySet(name=name)
        session.add(study_set)
        session.flush()
        self._replace_courses(session, study_set.id, course_ids)
        session.commit()
        _ = study_set.id
        if self._owns_session:
            session.close()
        return study_set

    def get_set(self, study_set_id: int) -> StudySet | None:
        """获取学习集。"""
        session = self._get_session()
        study_set = session.get(StudySet, study_set_id)
        if self._owns_session:
            session.close()
        return study_set

    def list_sets(self) -> list[StudySet]:
        """列出所有学习集，按创建时间倒序。"""
        session = self._get_session()
        statement = select(StudySet).order_by(StudySet.created_at.desc())
        sets = session.exec(statement).all()
        if self._owns_session:
            session.close()
        return list(sets)

    def get_course_ids(self, study_set_id: int) -> list[int]:
        """获取学习集关联的全部课程 id（含未完成/已删除的原始记录）。"""
        session = self._get_session()
        statement = select(StudySetCourse.course_id).where(
            StudySetCourse.study_set_id == study_set_id
        )
        ids = list(session.exec(statement).all())
        if self._owns_session:
            session.close()
        return ids

    def get_active_course_ids(self, study_set_id: int) -> list[int]:
        """获取学习集内可用于问答的课程 id（仅保留已完成且存在的课程）。

        集合内课程被删除或正在重新处理时优雅降级，自动跳过。
        """
        raw_ids = self.get_course_ids(study_set_id)
        if not raw_ids:
            return []
        session = self._get_session()
        statement = select(Course.id).where(
            Course.id.in_(raw_ids), Course.status == "completed"
        )
        active = list(session.exec(statement).all())
        if self._owns_session:
            session.close()
        return active

    def update_set(
        self,
        study_set_id: int,
        name: str | None = None,
        course_ids: list[int] | None = None,
    ) -> StudySet:
        """更新学习集名称和/或课程关联（course_ids 为整体替换）。"""
        session = self._get_session()
        study_set = session.get(StudySet, study_set_id)
        if not study_set:
            raise ValueError(f"学习集不存在: {study_set_id}")

        if name is not None:
            name = name.strip()
            if not name:
                raise ValueError("学习集名称不能为空")
            study_set.name = name
        if course_ids is not None:
            self._replace_courses(session, study_set_id, course_ids)

        study_set.updated_at = datetime.utcnow()
        session.add(study_set)
        session.commit()
        session.refresh(study_set)
        if self._owns_session:
            session.close()
        return study_set

    def delete_set(self, study_set_id: int) -> None:
        """删除学习集及其课程关联（不影响课程本身）。"""
        session = self._get_session()
        study_set = session.get(StudySet, study_set_id)
        if study_set:
            session.delete(study_set)
        # 级联删除关联
        links = session.exec(
            select(StudySetCourse).where(StudySetCourse.study_set_id == study_set_id)
        ).all()
        for link in links:
            session.delete(link)
        session.commit()
        if self._owns_session:
            session.close()

    def remove_course_everywhere(self, course_id: int) -> None:
        """课程删除时，清理其在所有学习集中的关联。"""
        session = self._get_session()
        links = session.exec(
            select(StudySetCourse).where(StudySetCourse.course_id == course_id)
        ).all()
        for link in links:
            session.delete(link)
        session.commit()
        if self._owns_session:
            session.close()

    def _replace_courses(
        self, session: Session, study_set_id: int, course_ids: list[int]
    ) -> None:
        """整体替换学习集的课程关联（去重、去 None）。"""
        existing = session.exec(
            select(StudySetCourse).where(StudySetCourse.study_set_id == study_set_id)
        ).all()
        for link in existing:
            session.delete(link)
        session.flush()

        seen: set[int] = set()
        for cid in course_ids:
            if cid is None or cid in seen:
                continue
            seen.add(cid)
            session.add(StudySetCourse(study_set_id=study_set_id, course_id=cid))
