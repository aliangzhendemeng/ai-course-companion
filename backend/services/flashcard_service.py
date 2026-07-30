"""闪卡业务服务：生成、列表、三档熟悉度标记、统计、清空。"""

import logging

from sqlmodel import Session, select

from backend.ai import quiz_generator
from backend.ai.llm.base import BaseLLM
from backend.database import engine
from backend.models import Flashcard
from backend.services.quiz_service import FULL_TEXT_MAX_CHARS, load_course_full_text
from backend.services.study_set_service import StudySetService

logger = logging.getLogger(__name__)

VALID_FAMILIARITY = ("known", "fuzzy", "unknown")


class FlashcardService:
    """闪卡的生成、查询、熟悉度标记与清空。"""

    def __init__(self, session: Session | None = None, llm: BaseLLM | None = None) -> None:
        self.session = session
        self._owns_session = session is None
        self.llm = llm

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def _resolve_scope(
        self, course_id: int | None, study_set_id: int | None
    ) -> tuple[int | None, int | None, list[int]]:
        """与测验一致的范围解析（复用 QuizService 的校验逻辑）。"""
        from backend.services.quiz_service import QuizService

        return QuizService(session=self.session)._resolve_scope(course_id, study_set_id)

    # ----- 生成 -----

    def generate(
        self,
        course_id: int | None = None,
        study_set_id: int | None = None,
        count: int = 15,
    ) -> tuple[int, int]:
        """生成闪卡并追加存库，返回 (本次生成数, 该范围总卡数)。"""
        cid, sid, course_ids = self._resolve_scope(course_id, study_set_id)
        session = self._get_session()

        # 复用测验的全文拼接
        from backend.services.quiz_service import QuizService

        full_text = QuizService(session=session)._build_full_text(session, course_ids)
        if not full_text.strip():
            raise ValueError("该范围没有可用于出题的课程内容（字幕/课件为空）")

        raw_cards = quiz_generator.generate_flashcards(full_text, count=count, llm=self.llm)
        if not raw_cards:
            raise quiz_generator.QuizGenerationError("LLM 未能生成任何有效闪卡")

        default_source = course_ids[0] if course_ids else None
        for c in raw_cards:
            session.add(
                Flashcard(
                    course_id=cid,
                    study_set_id=sid,
                    front=c["front"],
                    back=c["back"],
                    familiarity="unknown",
                    source_course_id=default_source,
                    source_timestamp=c.get("source_timestamp"),
                )
            )
        session.commit()
        total = self._count(cid, sid)
        if self._owns_session:
            session.close()
        return len(raw_cards), total

    # ----- 查询 -----

    def _count(self, course_id: int | None, study_set_id: int | None) -> int:
        session = self._get_session()
        n = len(session.exec(self._scope_select(course_id, study_set_id)).all())
        if self._owns_session:
            session.close()
        return n

    @staticmethod
    def _scope_select(course_id: int | None, study_set_id: int | None):
        statement = select(Flashcard)
        if course_id is not None:
            statement = statement.where(Flashcard.course_id == course_id)
        elif study_set_id is not None:
            statement = statement.where(Flashcard.study_set_id == study_set_id)
        return statement.order_by(Flashcard.id)

    def list_cards(
        self, course_id: int | None = None, study_set_id: int | None = None
    ) -> list[Flashcard]:
        session = self._get_session()
        cards = list(session.exec(self._scope_select(course_id, study_set_id)).all())
        for c in cards:
            _ = (c.id, c.front, c.back, c.familiarity, c.source_course_id, c.source_timestamp)
        if self._owns_session:
            session.close()
        return cards

    # ----- 熟悉度标记 -----

    def set_familiarity(self, flashcard_id: int, familiarity: str) -> Flashcard:
        if familiarity not in VALID_FAMILIARITY:
            raise ValueError(f"非法熟悉度: {familiarity}（应为 known/fuzzy/unknown）")
        session = self._get_session()
        card = session.get(Flashcard, flashcard_id)
        if not card:
            if self._owns_session:
                session.close()
            raise ValueError(f"闪卡不存在: {flashcard_id}")
        card.familiarity = familiarity
        session.add(card)
        session.commit()
        _ = (card.id, card.front, card.back, card.familiarity,
             card.source_course_id, card.source_timestamp)
        if self._owns_session:
            session.close()
        return card

    # ----- 统计 -----

    def stats(self, course_id: int | None = None, study_set_id: int | None = None) -> dict:
        cards = self.list_cards(course_id, study_set_id)
        return {
            "total": len(cards),
            "known": sum(1 for c in cards if c.familiarity == "known"),
            "fuzzy": sum(1 for c in cards if c.familiarity == "fuzzy"),
            "unknown": sum(1 for c in cards if c.familiarity == "unknown"),
        }

    # ----- 清空 -----

    def clear(self, course_id: int | None = None, study_set_id: int | None = None) -> int:
        session = self._get_session()
        cards = session.exec(self._scope_select(course_id, study_set_id)).all()
        n = 0
        for c in cards:
            session.delete(c)
            n += 1
        session.commit()
        if self._owns_session:
            session.close()
        return n
