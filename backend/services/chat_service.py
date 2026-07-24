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

    def ask(self, course_id: int, question: str, scope: str = "course") -> dict:
        """提问并返回答案。"""
        course = self.course_service.get_course(course_id)
        if not course:
            raise ValueError(f"课程不存在: {course_id}")
        if course.status != "completed":
            raise ValueError("课程尚未处理完成，无法问答")

        if scope == "all":
            result = self.rag_engine.query_all(question)
        else:
            result = self.rag_engine.query(course_id, question)

        # 保存用户问题
        with Session(engine) as session:
            user_msg = ChatMessage(
                course_id=course_id,
                role="user",
                content=question,
            )
            assistant_msg = ChatMessage(
                course_id=course_id,
                role="assistant",
                content=result["answer"],
                sources=json.dumps(result["sources"], ensure_ascii=False),
            )
            session.add(user_msg)
            session.add(assistant_msg)
            session.commit()

        return result

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
