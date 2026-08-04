"""掌握度仪表盘服务：聚合测验正确率、闪卡熟悉度、错题掌握、笔记等统计。

全局视角（不限课程），供课程库页展示学习掌握度总览。
"""

import logging

from sqlmodel import Session, select

from backend.database import engine
from backend.models import Course, Flashcard, Note, QuestionAttempt
from backend.services.quiz_service import QuizService

logger = logging.getLogger(__name__)


class DashboardService:
    """学习掌握度聚合统计。"""

    def __init__(self, session: Session | None = None) -> None:
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session is None:
            return Session(engine)
        return self.session

    def dashboard(self) -> dict:
        session = self._get_session()
        attempts = list(session.exec(select(QuestionAttempt)).all())
        total_attempts = len(attempts)
        correct = sum(1 for a in attempts if a.correct)

        cards = list(session.exec(select(Flashcard)).all())
        familiarity = {"known": 0, "fuzzy": 0, "unknown": 0}
        for c in cards:
            familiarity[c.familiarity] = familiarity.get(c.familiarity, 0) + 1

        # 错题掌握度（复用 QuizService 的连续答对判定）
        wrong = QuizService(session=session).get_wrong_questions()
        unmastered = sum(1 for _q, m, _w, _s in wrong if not m)
        mastered = sum(1 for _q, m, _w, _s in wrong if m)

        notes = len(list(session.exec(select(Note)).all()))
        courses = list(session.exec(select(Course)).all())
        courses_completed = sum(1 for c in courses if c.status == "completed")

        if self._owns_session:
            session.close()

        return {
            "quiz": {
                "total_attempts": total_attempts,
                "correct": correct,
                "accuracy": round(correct / total_attempts, 2) if total_attempts else 0.0,
            },
            "flashcards": {
                "total": len(cards),
                "known": familiarity.get("known", 0),
                "fuzzy": familiarity.get("fuzzy", 0),
                "unknown": familiarity.get("unknown", 0),
            },
            "wrong": {
                "total": len(wrong),
                "unmastered": unmastered,
                "mastered": mastered,
            },
            "notes": notes,
            "courses_completed": courses_completed,
        }
