"""测验业务服务：从课程/学习集生成选择题与判断题，存库、追加、清空、判分。"""

import json
import logging

from sqlmodel import Session, select

from backend.ai import quiz_generator
from backend.ai.llm.base import BaseLLM
from backend.ai.rag_engine import RAGEngine, format_timestamp
from backend.database import engine
from backend.models import Course, Frame, Question, Transcript
from backend.services.study_set_service import StudySetService

logger = logging.getLogger(__name__)

# 学习集拼接全文的上限（与 RAGEngine 保持一致，超长截断以控制上下文）
FULL_TEXT_MAX_CHARS = RAGEngine.FULL_TEXT_MAX_CHARS


def _merge_ocr_text(ocr_text: str) -> str:
    """合并 OCR 文本中的短行（与 RAGEngine 逻辑一致）。"""
    lines = [line.strip() for line in ocr_text.split("\n") if line.strip()]
    if not lines:
        return ""
    merged = []
    current = lines[0]
    for line in lines[1:]:
        if len(current) < 20 or line.startswith("·") or line.startswith("-") or line[0].isdigit():
            merged.append(current)
            current = line
        else:
            current += line
    merged.append(current)
    return "\n".join(merged)


def load_course_full_text(session: Session, course_id: int) -> str:
    """加载一门课的完整清洗文本（字幕 + OCR），用于出题。"""
    transcripts = session.exec(
        select(Transcript).where(Transcript.course_id == course_id).order_by(Transcript.start_time)
    ).all()
    frames = session.exec(
        select(Frame).where(Frame.course_id == course_id).order_by(Frame.timestamp)
    ).all()

    parts = []
    for t in transcripts:
        if t.text:
            parts.append(f"[字幕 {format_timestamp(t.start_time)}] {t.text}")
    for f in frames:
        if f.ocr_text:
            merged = _merge_ocr_text(f.ocr_text)
            if merged:
                parts.append(f"[课件 {format_timestamp(f.timestamp)}] {merged}")
    return "\n\n".join(parts)


class QuizService:
    """测验题的生成、查询、判分与清空。"""

    def __init__(self, session: Session | None = None, llm: BaseLLM | None = None) -> None:
        self.session = session
        self._owns_session = session is None
        self.llm = llm  # None 时由 quiz_generator 内部 create_chat_llm()

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    # ----- 范围解析 -----

    def _resolve_scope(
        self, course_id: int | None, study_set_id: int | None
    ) -> tuple[int | None, int | None, list[int]]:
        """校验并解析出题范围，返回 (course_id, study_set_id, 课程 id 列表)。

        单课程：course_id 给定，返回 [course_id]。
        学习集：study_set_id 给定，返回集合内已完成的课程 id 列表。
        """
        if (course_id is None) == (study_set_id is None):
            raise ValueError("必须且只能指定 course_id 或 study_set_id 之一")

        session = self._get_session()
        if course_id is not None:
            course = session.get(Course, course_id)
            if not course:
                raise ValueError(f"课程不存在: {course_id}")
            if course.status != "completed":
                raise ValueError(f"课程尚未处理完成: {course.title}")
            return course_id, None, [course_id]

        # 学习集
        svc = StudySetService(session)
        if not svc.get_set(study_set_id):
            raise ValueError(f"学习集不存在: {study_set_id}")
        active = svc.get_active_course_ids(study_set_id)
        if not active:
            raise ValueError("学习集内没有已完成处理的课程")
        return None, study_set_id, active

    def _build_full_text(self, session: Session, course_ids: list[int]) -> str:
        """拼接一门或多门课的全文，超长截断。"""
        if len(course_ids) == 1:
            return load_course_full_text(session, course_ids[0])

        titles = {c.id: c.title for c in session.exec(select(Course).where(Course.id.in_(course_ids))).all()}
        parts = []
        total = 0
        for cid in course_ids:
            text = load_course_full_text(session, cid)
            if not text:
                continue
            block = f"===== {titles.get(cid, f'课程 {cid}')} =====\n{text}"
            if total + len(block) > FULL_TEXT_MAX_CHARS:
                remaining = FULL_TEXT_MAX_CHARS - total
                if remaining > 0:
                    parts.append(block[:remaining])
                break
            parts.append(block)
            total += len(block)
        return "\n\n".join(parts)

    # ----- 生成 -----

    def generate(
        self,
        course_id: int | None = None,
        study_set_id: int | None = None,
        count: int = 12,
    ) -> tuple[int, int]:
        """生成题目并追加存库，返回 (本次生成数, 该范围总题数)。

        追加式：不覆盖已有题；"清空重生成"请先调 clear()。
        """
        cid, sid, course_ids = self._resolve_scope(course_id, study_set_id)
        session = self._get_session()
        full_text = self._build_full_text(session, course_ids)
        if not full_text.strip():
            raise ValueError("该范围没有可用于出题的课程内容（字幕/课件为空）")

        raw_questions = quiz_generator.generate_questions(full_text, count=count, llm=self.llm)
        if not raw_questions:
            raise quiz_generator.QuizGenerationError("LLM 未能生成任何有效题目")

        # 学习集范围：来源课程暂记为集合内首门课（逐题精确定位留待后续迭代）
        default_source = course_ids[0] if course_ids else None
        for q in raw_questions:
            session.add(
                Question(
                    course_id=cid,
                    study_set_id=sid,
                    type=q["type"],
                    question=q["question"],
                    options=json.dumps(q["options"], ensure_ascii=False) if q["options"] else None,
                    answer=q["answer"],
                    explanation=q["explanation"],
                    source_course_id=default_source,
                    source_timestamp=q.get("source_timestamp"),
                )
            )
        session.commit()
        total = self._count(cid, sid)
        if self._owns_session:
            session.close()
        return len(raw_questions), total

    # ----- 查询 -----

    def _count(self, course_id: int | None, study_set_id: int | None) -> int:
        session = self._get_session()
        statement = self._scope_select(course_id, study_set_id)
        n = len(session.exec(statement).all())
        if self._owns_session:
            session.close()
        return n

    @staticmethod
    def _scope_select(course_id: int | None, study_set_id: int | None):
        statement = select(Question)
        if course_id is not None:
            statement = statement.where(Question.course_id == course_id)
        elif study_set_id is not None:
            statement = statement.where(Question.study_set_id == study_set_id)
        return statement.order_by(Question.id)

    def list_questions(
        self, course_id: int | None = None, study_set_id: int | None = None
    ) -> list[Question]:
        """列出某范围的全部题（含答案与解析，供前端展示/复习）。"""
        session = self._get_session()
        questions = list(session.exec(self._scope_select(course_id, study_set_id)).all())
        # 触发属性加载，避免 owns_session 关闭后访问 detached 属性
        for q in questions:
            _ = (q.id, q.options, q.answer, q.explanation)
        if self._owns_session:
            session.close()
        return questions

    # ----- 判分 -----

    def submit_answer(self, question_id: int, answer: str) -> Question:
        """判分：比对预设答案，返回该题（前端读 correct/answer/explanation）。

        选择/判断纯后端比对，不调 LLM。
        """
        session = self._get_session()
        question = session.get(Question, question_id)
        if not question:
            if self._owns_session:
                session.close()
            raise ValueError(f"题目不存在: {question_id}")
        _ = (question.id, question.type, question.question, question.options,
             question.answer, question.explanation, question.source_course_id,
             question.source_timestamp)
        if self._owns_session:
            session.close()
        return question

    @staticmethod
    def is_correct(question: Question, answer: str) -> bool:
        """判断作答是否正确（大小写/空白容错）。"""
        given = (answer or "").strip()
        expected = (question.answer or "").strip()
        if question.type == "choice":
            return given.upper() == expected.upper()
        # 判断题：兼容 对/错、true/false
        norm = {"对": "正确", "true": "正确", "√": "正确",
                "错": "错误", "false": "错误", "×": "错误"}
        return norm.get(given, given) == norm.get(expected, expected)

    # ----- 清空 -----

    def clear(self, course_id: int | None = None, study_set_id: int | None = None) -> int:
        """清空某范围的全部题，返回删除数。"""
        session = self._get_session()
        questions = session.exec(self._scope_select(course_id, study_set_id)).all()
        n = 0
        for q in questions:
            session.delete(q)
            n += 1
        session.commit()
        if self._owns_session:
            session.close()
        return n
