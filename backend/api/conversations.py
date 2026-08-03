"""会话 API：课程下的多轮对话分组（列表/消息流/改名/删除）。"""

import json

from fastapi import APIRouter, HTTPException

from backend.schemas import ConversationItem, ConversationRenameRequest
from backend.services.conversation_service import ConversationService

router = APIRouter()


def _to_item(c) -> ConversationItem:
    try:
        cids = json.loads(c.course_ids) if c.course_ids else []
    except (json.JSONDecodeError, TypeError):
        cids = []
    return ConversationItem(
        id=c.id,
        course_id=c.course_id,
        title=c.title,
        scope=c.scope,
        course_ids=cids,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("/courses/{course_id}/conversations", response_model=list[ConversationItem])
def list_conversations(course_id: int):
    """列出某课程的全部会话（按最近更新倒序）。"""
    return [_to_item(c) for c in ConversationService().list_by_course(course_id)]


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int):
    """某会话的消息流（按时间正序）。"""
    svc = ConversationService()
    if not svc.get(conversation_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = svc.messages(conversation_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "scope": m.scope,
            "sources": m.sources,
            "created_at": m.created_at,
        }
        for m in msgs
    ]


@router.patch("/conversations/{conversation_id}", response_model=ConversationItem)
def rename_conversation(conversation_id: int, payload: ConversationRenameRequest):
    """会话改名。"""
    try:
        conv = ConversationService().rename(conversation_id, payload.title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_item(conv)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    """删除会话及其全部消息。"""
    try:
        n = ConversationService().delete(conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": f"已删除会话及 {n} 条消息", "deleted_messages": n}
