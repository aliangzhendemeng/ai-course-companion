"""学习周报服务：聚合最近 7 天的学习活动统计。"""

import logging
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from backend.database import engine
from backend.models import ChatMessage, Flashcard, Note, QuestionAttempt
from backend.services.study_stats_service import StudyStatsService, _to_local_date

logger = logging.getLogger(__name__)

WINDOW_DAYS = 7


class WeeklyReportService:
    """最近 7 天学习情况汇总。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def weekly(self) -> dict:
        """返回最近 7 天的学习统计。"""
        session = self._get_session()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=WINDOW_DAYS)

        attempts = list(
            session.exec(
                select(QuestionAttempt).where(QuestionAttempt.created_at >= start)
            ).all()
        )
        correct = sum(1 for a in attempts if a.correct)
        cards = list(
            session.exec(select(Flashcard).where(Flashcard.created_at >= start)).all()
        )
        notes = len(list(session.exec(select(Note).where(Note.created_at >= start)).all()))
        questions = len(
            list(
                session.exec(
                    select(ChatMessage).where(ChatMessage.created_at >= start)
                ).all()
            )
        )

        # 最近 7 天有学习的天数（复用 study_dates 的本地日期转换）
        all_dates = StudyStatsService(session=session).study_dates()
        today = datetime.now().date()
        recent = {today - timedelta(days=i) for i in range(WINDOW_DAYS)}
        study_days = len(all_dates & recent)

        if self._owns_session:
            session.close()

        return {
            "window_days": WINDOW_DAYS,
            "quiz": {
                "attempts": len(attempts),
                "correct": correct,
                "accuracy": round(correct / len(attempts), 2) if attempts else 0.0,
            },
            "flashcards_generated": len(cards),
            "notes": notes,
            "questions": questions,
            "study_days": study_days,
        }
