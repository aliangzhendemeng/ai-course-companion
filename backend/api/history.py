"""问答历史 API。"""

import json
from datetime import timezone

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Conversation, Course

router = APIRouter()


def _to_utc_iso(dt) -> str:
    """把时间戳序列化为带时区的 UTC ISO 字符串，前端才能正确解析为 UTC。

    历史数据库存的是 naive UTC（无时区）， naive 时按 UTC 补上 +00:00。
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


@router.get("")
def list_history():
    """列出所有问答历史，按时间倒序（带会话分组信息）。"""
    with Session(engine) as session:
        statement = (
            select(ChatMessage, Course.title, Conversation.title)
            .join(Course, ChatMessage.course_id == Course.id)
            .outerjoin(Conversation, ChatMessage.conversation_id == Conversation.id)
            .order_by(ChatMessage.created_at.desc())
        )
        results = session.exec(statement).all()

        # 预取所有课程标题，便于把 course_ids 展开成课程名
        titles = {c.id: c.title for c in session.exec(select(Course)).all()}

        items = []
        for msg, anchor_title, conv_title in results:
            involved_ids: list[int] = []
            if msg.course_ids:
                try:
                    involved_ids = [int(x) for x in json.loads(msg.course_ids)]
                except (ValueError, TypeError):
                    involved_ids = []
            items.append(
                {
                    "id": msg.id,
                    "course_id": msg.course_id,
                    "course_title": anchor_title,
                    "course_ids": involved_ids,
                    "course_titles": [titles.get(cid, f"课程 {cid}") for cid in involved_ids],
                    "role": msg.role,
                    "content": msg.content,
                    "scope": msg.scope,
                    "sources": msg.sources,
                    "created_at": _to_utc_iso(msg.created_at),
                    "conversation_id": msg.conversation_id,
                    "conversation_title": conv_title,
                    "web_results": msg.web_results,
                }
            )
        return items


@router.delete("/{message_id}")
def delete_history(message_id: int):
    """删除单条历史记录。"""
    with Session(engine) as session:
        message = session.get(ChatMessage, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="历史记录不存在")
        session.delete(message)
        session.commit()
    return {"message": "已删除"}
