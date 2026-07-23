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
    duration: float | None
    created_at: datetime


class CourseDetail(BaseModel):
    id: int
    title: str
    video_path: str
    duration: float | None
    status: str
    status_message: str | None
    created_at: datetime
    updated_at: datetime


class SummaryResponse(BaseModel):
    course_id: int
    outline: str | None
    abstract: str | None
    lecture_notes: str | None


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    course_id: int
    answer: str
    sources: list[dict] | None
