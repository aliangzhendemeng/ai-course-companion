"""问答相关 API。"""

from fastapi import APIRouter, HTTPException

from backend.schemas import ChatRequest, ChatResponse
from backend.services.chat_service import ChatService

router = APIRouter()


@router.post("/{course_id}", response_model=ChatResponse)
def ask_question(course_id: int, request: ChatRequest):
    """向课程提问。"""
    service = ChatService()
    try:
        result = service.ask(
            course_id,
            request.question,
            scope=request.scope,
            course_ids=request.course_ids,
        )
        return ChatResponse(
            course_id=course_id,
            answer=result["answer"],
            sources=result["sources"],
            answer_message_id=result.get("answer_message_id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{course_id}/history")
def get_chat_history(course_id: int):
    """获取问答历史。"""
    service = ChatService()
    messages = service.get_history(course_id)
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "sources": msg.sources,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]
