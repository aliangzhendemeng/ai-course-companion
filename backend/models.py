"""数据模型定义。"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    """带时区的当前 UTC 时间（序列化带 +00:00，前端可正确解析为 UTC）。"""
    return datetime.now(timezone.utc)


class Course(SQLModel, table=True):
    """课程：用户上传的视频及其处理状态。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    video_path: str = Field(index=True, unique=True)
    file_hash: Optional[str] = Field(default=None, index=True)
    duration: Optional[float] = None
    status: str = Field(default="uploaded", index=True)
    status_message: Optional[str] = None
    progress_percent: int = Field(default=0)
    frame_interval: Optional[float] = None
    max_frames: Optional[int] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

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
    created_at: datetime = Field(default_factory=_utcnow)

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
    created_at: datetime = Field(default_factory=_utcnow)

    course: Course = Relationship(back_populates="frames")


class Summary(SQLModel, table=True):
    """总结：课程的三级总结内容。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True, unique=True)
    outline: Optional[str] = None
    abstract: Optional[str] = None
    lecture_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    course: Course = Relationship(back_populates="summary")


class ChatMessage(SQLModel, table=True):
    """问答消息：用户提问和系统回答。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)  # 锚点课程（归档用）
    role: str  # "user" 或 "assistant"
    content: str
    scope: str = Field(default="course")  # "course" | "all" | "set"
    course_ids: Optional[str] = None  # JSON 数组：set/all 实际涉及的课程 id
    sources: Optional[str] = None  # JSON 字符串
    debug_info: Optional[str] = None  # JSON 字符串：prompt、context、model、raw_answer
    created_at: datetime = Field(default_factory=_utcnow)

    course: Course = Relationship(back_populates="chat_messages")


class Progress(SQLModel, table=True):
    """学习进度：用户在课程中的最后观看到位置。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True, unique=True)
    last_position: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=_utcnow)

    course: Course = Relationship(back_populates="progress")


class StudySetCourse(SQLModel, table=True):
    """学习集-课程关联：多对多。课程删除时关联随之失效。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    study_set_id: int = Field(foreign_key="studyset.id", index=True)
    course_id: int = Field(foreign_key="course.id", index=True)


class StudySet(SQLModel, table=True):
    """学习集：命名的课程组合，用于限定问答范围（如"数学必修"）。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Question(SQLModel, table=True):
    """测验题：从课程内容生成的选择题/判断题。

    范围：单课程（course_id）或学习集（study_set_id）二选一。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: Optional[int] = Field(default=None, foreign_key="course.id", index=True)
    study_set_id: Optional[int] = Field(default=None, foreign_key="studyset.id", index=True)
    type: str = Field(default="choice")  # "choice" 选择 | "judge" 判断
    question: str
    options: Optional[str] = None  # JSON 数组（选择题选项）
    answer: str  # 选择题存选项序号("A"/"B"...)，判断题存 "正确"/"错误"
    explanation: Optional[str] = None
    source_course_id: Optional[int] = Field(default=None, index=True)  # 来源课程（学习集时标注具体哪门课）
    source_timestamp: Optional[float] = None  # 来源时间点（秒），可跳回视频
    created_at: datetime = Field(default_factory=_utcnow)


class QuestionAttempt(SQLModel, table=True):
    """作答记录：每次作答一行，用于错题本（最近一次答错即为错题）。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    answer: str  # 用户作答
    correct: bool = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)


class Flashcard(SQLModel, table=True):
    """闪卡：从课程内容生成的正/反面记忆卡。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: Optional[int] = Field(default=None, foreign_key="course.id", index=True)
    study_set_id: Optional[int] = Field(default=None, foreign_key="studyset.id", index=True)
    front: str  # 正面：概念/问题
    back: str  # 背面：解释/答案
    familiarity: str = Field(default="unknown", index=True)  # known 认识 | fuzzy 模糊 | unknown 不认识
    source_course_id: Optional[int] = Field(default=None, index=True)
    source_timestamp: Optional[float] = None
    created_at: datetime = Field(default_factory=_utcnow)
