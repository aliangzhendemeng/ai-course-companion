"""问答历史 API。"""

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Course

router = APIRouter()


@router.get("")
def list_history():
    """列出所有问答历史，按时间倒序。"""
    with Session(engine) as session:
        statement = (
            select(ChatMessage, Course.title)
            .join(Course, ChatMessage.course_id == Course.id)
            .order_by(ChatMessage.created_at.desc())
        )
        results = session.exec(statement).all()
        return [
            {
                "id": msg.id,
                "course_id": msg.course_id,
                "course_title": title,
                "role": msg.role,
                "content": msg.content,
                "scope": msg.scope,
                "sources": msg.sources,
                "created_at": msg.created_at,
            }
            for msg, title in results
        ]


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
