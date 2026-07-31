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
    scope: str = "course"  # "course" | "all" | "set"
    course_ids: list[int] | None = None  # scope="set" 时指定的课程集合


class ChatResponse(BaseModel):
    course_id: int
    answer: str
    sources: list[Source] | None
    answer_message_id: int | None = None


class StudySetCreate(BaseModel):
    name: str
    course_ids: list[int] = []


class StudySetUpdate(BaseModel):
    name: str | None = None
    course_ids: list[int] | None = None  # 整体替换


class StudySetItem(BaseModel):
    id: int
    name: str
    course_ids: list[int]
    course_titles: list[str]
    created_at: datetime


# ===== 测验（Question）=====

class QuestionItem(BaseModel):
    """单道题（不含答案，作答前展示用）。"""

    id: int
    type: str  # "choice" | "judge"
    question: str
    options: list[str] | None = None
    source_course_id: int | None = None
    source_timestamp: float | None = None


class QuestionDetail(QuestionItem):
    """含答案与解析（判分后 / 列表展示用），并附带最近一次作答进度。"""

    answer: str
    explanation: str | None = None
    last_answer: str | None = None  # 最近一次作答（未作答为 None），供断点续答
    last_correct: bool | None = None  # 最近一次作答是否正确


class QuizGenerateRequest(BaseModel):
    course_id: int | None = None
    study_set_id: int | None = None
    count: int = 12


class QuizGenerateResponse(BaseModel):
    generated: int  # 本次新生成题数
    total: int  # 该范围当前总题数


class QuizAnswerRequest(BaseModel):
    answer: str  # 选择题 "A"/"B"...；判断题 "正确"/"错误"


class QuizAnswerResponse(BaseModel):
    question_id: int
    correct: bool
    answer: str  # 正确答案
    explanation: str | None = None


class WrongQuestionItem(QuestionDetail):
    """错题本条目：历史答错记录，连续答对 N 次才标"已掌握"，记录保留。"""

    mastered: bool  # 是否已掌握（自最近答错起连续答对 master_streak 次）
    wrong_count: int  # 历史答错次数
    streak: int  # 自最近一次答错起的连续答对数（掌握进度）
    master_streak: int  # 达到多少连续答对算掌握


# ===== 闪卡（Flashcard）=====

class FlashcardItem(BaseModel):
    id: int
    front: str
    back: str
    familiarity: str  # known | fuzzy | unknown
    source_course_id: int | None = None
    source_timestamp: float | None = None


class FlashcardGenerateRequest(BaseModel):
    course_id: int | None = None
    study_set_id: int | None = None
    count: int = 15


class FlashcardGenerateResponse(BaseModel):
    generated: int
    total: int


class FlashcardFamiliarityRequest(BaseModel):
    familiarity: str  # known | fuzzy | unknown


class FlashcardStats(BaseModel):
    total: int
    known: int
    fuzzy: int
    unknown: int


# ===== 笔记/书签（Note）=====

class NoteItem(BaseModel):
    id: int
    course_id: int
    kind: str  # note | bookmark
    content: str
    timestamp: float  # 视频时间点（秒）
    created_at: datetime
    updated_at: datetime


class NoteCreateRequest(BaseModel):
    course_id: int
    kind: str = "note"  # note | bookmark
    content: str = ""
    timestamp: float = 0.0


class NoteUpdateRequest(BaseModel):
    content: str
