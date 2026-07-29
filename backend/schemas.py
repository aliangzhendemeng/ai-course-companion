"""Pydantic 请求/响应模型。"""

from datetime import datetime

from pydantic import BaseModel


class CourseCreateResponse(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime


class CourseListItem(BaseModel):
    id: int
    title: str
    status: str
    status_message: str | None
    progress_percent: int
    duration: float | None
    created_at: datetime


class CourseDetail(BaseModel):
    id: int
    title: str
    video_url: str
    duration: float | None
    status: str
    status_message: str | None
    progress_percent: int
    created_at: datetime
    updated_at: datetime


class SummaryResponse(BaseModel):
    course_id: int
    outline: str | None
    abstract: str | None
    lecture_notes: str | None


class Source(BaseModel):
    """RAG 来源片段。"""

    type: str
    timestamp: float
    text: str
    course_id: int | None = None
    course_title: str | None = None
    frame_id: int | None = None
    transcript_id: int | None = None


class ChatRequest(BaseModel):
    question: str
    scope: str = "course"  # "course" | "all"


class ChatResponse(BaseModel):
    course_id: int
    answer: str
    sources: list[Source] | None
    answer_message_id: int | None = None
