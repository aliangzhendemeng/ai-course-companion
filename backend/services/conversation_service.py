"""会话服务：课程下的多轮对话分组（CRUD + 取消息）。"""

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Conversation

logger = logging.getLogger(__name__)


class ConversationService:
    """问答会话的增删改查。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def list_by_course(self, course_id: int) -> list[Conversation]:
        """列出某课程的全部会话，按最近更新倒序。"""
        session = self._get_session()
        rows = list(
            session.exec(
                select(Conversation)
                .where(Conversation.course_id == course_id)
                .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            ).all()
        )
        if self._owns_session:
            session.close()
        return rows

    def get(self, conversation_id: int) -> Conversation | None:
        session = self._get_session()
        conv = session.get(Conversation, conversation_id)
        if self._owns_session:
            session.close()
        return conv

    def messages(self, conversation_id: int) -> list[ChatMessage]:
        """某会话的全部消息，按时间正序。"""
        session = self._get_session()
        rows = list(
            session.exec(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(ChatMessage.created_at, ChatMessage.id)
            ).all()
        )
        if self._owns_session:
            session.close()
        return rows

    def create(
        self,
        course_id: int,
        title: str = "新会话",
        scope: str = "course",
        course_ids: str | None = None,
    ) -> Conversation:
        session = self._get_session()
        conv = Conversation(course_id=course_id, title=title, scope=scope, course_ids=course_ids)
        session.add(conv)
        session.commit()
        session.refresh(conv)
        if self._owns_session:
            session.close()
        return conv

    def rename(self, conversation_id: int, title: str) -> Conversation:
        session = self._get_session()
        conv = session.get(Conversation, conversation_id)
        if not conv:
            if self._owns_session:
                session.close()
            raise ValueError(f"会话不存在: {conversation_id}")
        conv.title = title.strip()[:60] or "未命名会话"
        session.add(conv)
        session.commit()
        session.refresh(conv)
        if self._owns_session:
            session.close()
        return conv

    def touch(self, conversation_id: int) -> None:
        """新消息后更新会话的 updated_at（用于排序）。"""
        session = self._get_session()
        conv = session.get(Conversation, conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            session.add(conv)
            session.commit()
        if self._owns_session:
            session.close()

    def delete(self, conversation_id: int) -> int:
        """删除会话及其全部消息，返回删除的消息数。"""
        session = self._get_session()
        conv = session.get(Conversation, conversation_id)
        if not conv:
            if self._owns_session:
                session.close()
            raise ValueError(f"会话不存在: {conversation_id}")
        msgs = list(
            session.exec(
                select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
            ).all()
        )
        for m in msgs:
            session.delete(m)
        session.delete(conv)
        session.commit()
        if self._owns_session:
            session.close()
        return len(msgs)
