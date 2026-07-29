"""问答服务。"""

import json

from sqlmodel import Session

from backend.ai.rag_engine import RAGEngine
from backend.database import engine
from backend.models import ChatMessage
from backend.services.course_service import CourseService


class ChatService:
    """课程问答服务。"""

    def __init__(self, rag_engine: RAGEngine | None = None) -> None:
        self.rag_engine = rag_engine or RAGEngine()
        self.course_service = CourseService()

    def ask(
        self,
        course_id: int,
        question: str,
        scope: str = "course",
        course_ids: list[int] | None = None,
    ) -> dict:
        """提问并返回答案。

        scope="course"：单课程；scope="all"：全部课程；
        scope="set"（或传入 course_ids）：限定在指定课程集合内（学习集）。
        """
        course = self.course_service.get_course(course_id)
        if not course:
            raise ValueError(f"课程不存在: {course_id}")
        if course.status != "completed":
            raise ValueError("课程尚未处理完成，无法问答")

        if course_ids:
            result = self.rag_engine.query_multiple(course_ids, question)
        elif scope == "all":
            result = self.rag_engine.query_all(question)
        else:
            result = self.rag_engine.query(course_id, question)

        # 保存用户问题
        with Session(engine) as session:
            user_msg = ChatMessage(
                course_id=course_id,
                role="user",
                content=question,
                scope=scope,
            )
            assistant_msg = ChatMessage(
                course_id=course_id,
                role="assistant",
                content=result["answer"],
                scope=scope,
                sources=json.dumps(result["sources"], ensure_ascii=False),
                debug_info=json.dumps(result.get("debug", {}), ensure_ascii=False),
            )
            session.add(user_msg)
            session.add(assistant_msg)
            session.commit()
            session.refresh(assistant_msg)

        return {**result, "answer_message_id": assistant_msg.id}

    def get_history(self, course_id: int) -> list[ChatMessage]:
        """获取问答历史。"""
        from sqlmodel import Session, select

        with Session(engine) as session:
            statement = (
                select(ChatMessage)
                .where(ChatMessage.course_id == course_id)
                .order_by(ChatMessage.created_at.asc())
            )
            return list(session.exec(statement).all())
