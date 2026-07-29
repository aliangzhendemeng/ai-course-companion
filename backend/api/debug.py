"""课程内容与问答诊断 API。"""

import json

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Course, Frame, Summary, Transcript

router = APIRouter()


@router.get("/{course_id}/debug/transcripts")
def get_transcripts_debug(course_id: int):
    """获取课程字幕诊断数据。"""
    with Session(engine) as session:
        course = session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        statement = (
            select(Transcript)
            .where(Transcript.course_id == course_id)
            .order_by(Transcript.start_time)
        )
        transcripts = session.exec(statement).all()
        return [
            {
                "id": t.id,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "text": t.text,
                "confidence": t.confidence,
            }
            for t in transcripts
        ]


@router.get("/{course_id}/debug/frames")
def get_frames_debug(course_id: int):
    """获取课程帧图与 OCR 诊断数据。"""
    with Session(engine) as session:
        course = session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        statement = (
            select(Frame)
            .where(Frame.course_id == course_id)
            .order_by(Frame.timestamp)
        )
        frames = session.exec(statement).all()
        return [
            {
                "id": f.id,
                "timestamp": f.timestamp,
                "image_path": f.image_path,
                "thumbnail_path": f.thumbnail_path,
                "ocr_text": f.ocr_text,
                "vision_desc": f.vision_desc,
            }
            for f in frames
        ]


@router.get("/{course_id}/debug/summary")
def get_summary_debug(course_id: int):
    """获取课程总结诊断数据。"""
    with Session(engine) as session:
        course = session.get(Course, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        summary = session.exec(
            select(Summary).where(Summary.course_id == course_id)
        ).first()
        if not summary:
            raise HTTPException(status_code=404, detail="总结不存在")
        return {
            "outline": summary.outline,
            "abstract": summary.abstract,
            "lecture_notes": summary.lecture_notes,
        }


def _resolve_model_name() -> str:
    """解析当前问答使用的模型标识。"""
    from backend.config import settings

    provider = (settings.chat_model or settings.llm_model or "deepseek").lower()
    specific = ""
    if ":" in provider:
        provider, specific = provider.split(":", 1)
    if specific:
        return f"{provider}:{specific}"
    return provider


@router.get("/{message_id}/debug")
def get_chat_debug(message_id: int):
    """获取单条问答的诊断信息。"""
    with Session(engine) as session:
        message = session.get(ChatMessage, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        if message.role != "assistant":
            raise HTTPException(status_code=400, detail="只能查看助手回答的诊断信息")

        user_msg = session.exec(
            select(ChatMessage)
            .where(
                ChatMessage.course_id == message.course_id,
                ChatMessage.role == "user",
                ChatMessage.created_at < message.created_at,
            )
            .order_by(ChatMessage.created_at.desc())
        ).first()

        debug_info = {}
        if message.debug_info:
            try:
                debug_info = json.loads(message.debug_info)
            except Exception:
                debug_info = {}
        course = session.get(Course, message.course_id)

        try:
            sources = json.loads(message.sources) if message.sources else []
        except Exception:
            sources = []

        return {
            "message_id": message.id,
            "course_id": message.course_id,
            "course_title": course.title if course else None,
            "question": user_msg.content if user_msg else "",
            "answer": message.content,
            "model": debug_info.get("model") or _resolve_model_name(),
            "prompt": debug_info.get("prompt", ""),
            "context": debug_info.get("context", ""),
            "raw_answer": debug_info.get("raw_answer") or message.content,
            "sources": sources,
            "scope": message.scope,
            "created_at": message.created_at,
        }
