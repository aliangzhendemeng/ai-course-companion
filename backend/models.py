"""数据模型定义。"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Course(SQLModel, table=True):
    """课程：用户上传的视频及其处理状态。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    video_path: str = Field(index=True, unique=True)
    duration: Optional[float] = None
    status: str = Field(default="uploaded", index=True)
    status_message: Optional[str] = None
    frame_interval: Optional[float] = None
    max_frames: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    transcripts: list["Transcript"] = Relationship(back_populates="course", cascade_delete=True)
    frames: list["Frame"] = Relationship(back_populates="course", cascade_delete=True)
    summary: Optional["Summary"] = Relationship(back_populates="course", cascade_delete=True)
    chat_messages: list["ChatMessage"] = Relationship(back_populates="course", cascade_delete=True)
    progress: Optional["Progress"] = Relationship(back_populates="course", cascade_delete=True)


class Transcript(SQLModel, table=True):
    """字幕：从音频中提取的分段文本。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    text: str
    start_time: float = Field(index=True)
    end_time: float
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="transcripts")


class Frame(SQLModel, table=True):
    """关键帧：从视频中抽取的图像帧及其多模态信息。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    timestamp: float = Field(index=True)
    image_path: str
    thumbnail_path: Optional[str] = None
    ocr_text: Optional[str] = None
    vision_desc: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="frames")


class Summary(SQLModel, table=True):
    """总结：课程的三级总结内容。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True, unique=True)
    outline: Optional[str] = None
    abstract: Optional[str] = None
    lecture_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="summary")


class ChatMessage(SQLModel, table=True):
    """问答消息：用户提问和系统回答。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    role: str  # "user" 或 "assistant"
    content: str
    sources: Optional[str] = None  # JSON 字符串
    created_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="chat_messages")


class Progress(SQLModel, table=True):
    """学习进度：用户在课程中的最后观看到位置。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True, unique=True)
    last_position: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    course: Course = Relationship(back_populates="progress")
