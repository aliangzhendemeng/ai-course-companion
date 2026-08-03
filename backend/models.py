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


class Conversation(SQLModel, table=True):
    """问答会话：一门课下的多轮对话分组（ChatGPT 式）。

    绑定课程（course_id）；会话内消息通过 ChatMessage.conversation_id 关联。
    scope/course_ids 记录该会话的检索范围（本期课程问答固定 scope=course）。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    title: str = Field(default="新会话")
    scope: str = Field(default="course")  # "course" | "all" | "set"
    course_ids: Optional[str] = None  # JSON 数组：set/all 实际涉及的课程 id
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ChatMessage(SQLModel, table=True):
    """问答消息：用户提问和系统回答。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)  # 锚点课程（归档用）
    conversation_id: Optional[int] = Field(default=None, foreign_key="conversation.id", index=True)  # 所属会话
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
    cleared_at 非空表示该题已被"清空题目"软删除，不再出现在题目 Tab，
    但其作答记录仍保留，错题本可基于历史作答展示。
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
    generated_at: datetime = Field(default_factory=_utcnow, index=True)  # 归属哪一批生成（清空题目时的分界）
    cleared_at: Optional[datetime] = Field(default=None, index=True)  # 软删除：被清空的时间
    created_at: datetime = Field(default_factory=_utcnow)


class QuestionAttempt(SQLModel, table=True):
    """作答记录：每次作答一行，是错题本历史的数据源。

    错题本 = 历史作答记录（独立于题目是否被清空）：
    某题曾答错即留记录，后续答对标"已掌握"但不移除。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int = Field(foreign_key="question.id", index=True)
    answer: str  # 用户作答
    correct: bool = Field(index=True)
    question_generated_at: Optional[datetime] = Field(default=None, index=True)  # 作答时该题所属题库批次
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


class Note(SQLModel, table=True):
    """笔记/书签：学生看视频时在某时间点记录的内容。

    kind = "note" 笔记（带文字内容）| "bookmark" 书签（纯时间点标记，content 可空）。
    timestamp 为视频秒数，点击可跳回对应时间点。按时间排序展示。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    kind: str = Field(default="note", index=True)  # note 笔记 | bookmark 书签
    content: str = Field(default="")  # 笔记文字；书签可空或一句话备注
    timestamp: float = Field(default=0.0)  # 视频时间点（秒）
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Chapter(SQLModel, table=True):
    """视频章节：按时间窗口自动划分，每章带 AI 生成的标题与速览。

    首次请求时生成并缓存（按 course_id），后续直接读取。
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    index: int  # 第几章（从 1 开始）
    title: str
    summary: str
    start_time: float
    end_time: float
    created_at: datetime = Field(default_factory=_utcnow)
